import os
import time
import sys
import paho.mqtt.client as mqtt
import json
import csv
from csv import writer
from sense_hat import SenseHat
from queue import Queue

import asyncio
import logging
import uuid
import struct

import threading


from bleak import BleakScanner, BleakClient

mqttBroker = "mqtt.eclipseprojects.io"
harvest_client = mqtt.Client("pasir_ris_c1")  # give client name


def ble_pi(out_q):
    # Enable debug output
    # logging.basicConfig(level=logging.DEBUG)

    DEVICE_NAME = "m5-stack"
    SERVICE_UUID = uuid.UUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
    CHAR_UUID = uuid.UUID("beb5483e-36e1-4688-b7f5-ea07361b26a8")

    async def run():
        while(True):
            print("Searching devices...")
            devices = await BleakScanner.discover()

            device = list(filter(lambda d: d.name == DEVICE_NAME, devices))
            if len(device) == 0:
                print("NO DEVICE FOUND")
                #raise RuntimeError(f"Failed to find a device name '{DEVICE_NAME}'")
            else:
                address = device[0].address
                print(f"Connecting to the device... (address: {address})")
                async with BleakClient(address, loop=loop) as client:
                    print("Message from the device...")
                    value = await client.read_gatt_char(CHAR_UUID)
                    print(value.decode())

                    print("Sending message to the device...")
                    message = bytearray(b"hi!")
                    await client.write_gatt_char(CHAR_UUID, message, True)

                    def callback(sender, data):
                        val = struct.unpack('f', data)
                        print(f"Received: {val}")
                        val1 = float('.'.join(str(elem) for elem in val))
                        print(val1)
                        out_q.put(val1)
                        print(val1)
                        # f = open('waterLevelData(Live).csv', 'w')
                        # writer = csv.writer(f)
                        # writer.writerow(val)

                    print("Subscribing to characteristic changes...")
                    while(client.is_connected):
                        await client.start_notify(CHAR_UUID, callback)
                        await asyncio.sleep(10)
                    #  if (not client.is_connected):
                    #       break

                #print("Waiting 60 seconds to receive data from the device...")
                # await asyncio.sleep(60)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())


def thingsboardpushdata(in_q):
    flag = False
    sense = SenseHat()

    text = (255, 0, 0)
    back = (0, 0, 0)

    # def on_message(client, userdata, msg):
    #     print('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
    #     y = msg.payload
    #     x = json.loads(y)
    #     print(str(msg.payload))
    #     sense.lowLight = True
    #     sense.show_message(str(x['params']), text_colour=text, back_colour=back,  scroll_speed=0.05)

    THINGSBOARD_HOST = 'demo.thingsboard.io'
    ACCESS_TOKEN = '8DjYuRVnY2KZJU1c9whc'

    INTERVAL = 1

    sense = SenseHat()
    sensor_data = {'temperature': 0, 'humidity': 0, 'waterLevel': 0.0}

    next_reading = time.time()

    client = mqtt.Client()

    # Set access token
    client.username_pw_set(ACCESS_TOKEN)

    # Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
    client.connect(THINGSBOARD_HOST, 1883, 60)
    harvest_client.connect(mqttBroker)

    harvest_client.loop_start()
    client.loop_start()

    try:
        while True:
            humidity = sense.get_humidity()
            temperature = sense.get_temperature()
            # with open('waterLevelData(Live).csv','r') as f:
            #         waterLevel = float(f.readlines()[-1])
            humidity = round(humidity, 2)
            temperature = round(temperature, 2)
            waterLevel = in_q.get()
            print("thread2:", waterLevel)
            size = True
#             if size == True and flag == True:
#                 harvest_client.publish(
#                     'pasir_ris/container_1/harvest', "harvest")
#                 flag = False
#             elif size==True and flag==False:
#                 flag = True
            #print('test')
            if size == True and flag == False:
                #print('test2')
                harvest_client.publish(
                    'pasir_ris/container_1/harvest', "harvest") 
                flag = True
            #print('test3')
            if size == False:
                flag = False  
                

            if (waterLevel == 0.0):
                sense.clear((0, 0, 255))
            else:
                sense.clear((0, 0, 0))

            print(u"Temperature: {:g}, Humidity: {:g}%, waterLevel: {:g}, Size:{}".format(
                temperature, humidity, waterLevel, size))
            sensor_data['waterLevel'] = waterLevel
            sensor_data['temperature'] = temperature
            sensor_data['humidity'] = humidity

            with open("Data(Live).csv", "a", newline='') as file_object:
                # data = [temperature, humidity,waterLevel, sizeStatus]
                data = [temperature, humidity, waterLevel, size]
                writer_object = writer(file_object)
                writer_object.writerow(data)

            # Sending humidity and temperature data to ThingsBoard
            client.publish('v1/devices/me/telemetry',
                           json.dumps(sensor_data), 1)
            client.subscribe('v1/devices/me/rpc/request/+')
            # client.on_message = on_message

            #next_reading += INTERVAL
            #sleep_time = next_reading-time.time()
            # if sleep_time > 0:
            # time.sleep(5)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()
    harvest_client.loop_stop()
    harvest_client.disconnect()


if __name__ == "__main__":

    # creating threads
    q = Queue()
    t1 = threading.Thread(target=ble_pi, args=(q,))
    t2 = threading.Thread(target=thingsboardpushdata, args=(q,))

    # starting threads
    t1.start()
    t2.start()

    # wait until all threads finish
    t1.join()
    t2.join()
