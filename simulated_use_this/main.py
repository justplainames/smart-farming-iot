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
harvest_client = mqtt.Client("tuas_c1")  # give client name

def harvest(index):
    size = [0, 1000, 2000, 3000, 4000, 5000, 8000, 9000, 10100]

    if size[index] > 10000:
        return True
    return False



def ble_pi(out_q):
    # Enable debug output
    # logging.basicConfig(level=logging.DEBUG)

    DEVICE_NAME = "m5-stack-simulated"
    SERVICE_UUID = uuid.UUID("4fafc201-1fb5-459e-8fcc-c5c9c331914c")
    CHAR_UUID = uuid.UUID("beb5483e-36e1-4688-b7f5-ea07361b26a9")

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
                        # print(val1)
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
    ACCESS_TOKEN = 'RCzo8hS8pJyCqtpguRhm'

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
    start = time.time()
    size = False
    counter = 0

    data = "Data.csv"
    Flag = False

    try:
        with open(data, 'r') as csvfile:
            datareader = csv.reader(csvfile)
            while True:
                for row in datareader:
                    if counter == 9:
                        counter = 0
                    # print(counter)
                    humidity = float(row[1])
                    temperature = float(row[0])
                    waterLevel = in_q.get()
                    elapsedtime = time.time() - start
                    print("ELAPSED TIME: ",elapsedtime)
                    if(elapsedtime > 5):
                        print("Checking Cabbage Size...")
                        start = time.time()
                        size = harvest(counter)
                        print("size:"+str(size))
                        counter += 1

                    if (waterLevel == 0.0):
                        sense.clear((0, 0, 255))
                    else:
                        sense.clear((0, 0, 0))

                    print(u"Temperature: {:g}, Humidity: {:g}%, waterLevel: {:g}, Size:{}".format(temperature, humidity, waterLevel, size))
                    if size == True and Flag == False:
                        harvest_client.publish(
                            "tuas/container_1/temperature_control", "harvest")
                        Flag = True
                    if size == False:
                        Flag = False
                    sensor_data['waterLevel'] = waterLevel
                    sensor_data['temperature'] = temperature
                    sensor_data['humidity'] = humidity

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
