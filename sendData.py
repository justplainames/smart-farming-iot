import os
import time
import sys
import paho.mqtt.client as mqtt
import json
import csv
from sense_hat import SenseHat

import asyncio
import logging
import uuid
import struct

import threading

from bleak import BleakScanner, BleakClient



def ble_pi():
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
                        val = struct.unpack('f',data)
                        print(f"Received: {val}")
                        f = open('waterLevelData(Live).csv', 'w')
                        writer = csv.writer(f)
                        writer.writerow(val)


                    print("Subscribing to characteristic changes...")
                    while(client.is_connected):
                        await client.start_notify(CHAR_UUID, callback)
                        await asyncio.sleep(10)
                    #  if (not client.is_connected):
                    #       break

                #print("Waiting 60 seconds to receive data from the device...")
                #await asyncio.sleep(60)


    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())




def thingsboardpushdata():
    sense = SenseHat()

    text = (255,0,0)
    back = (0,0,0)


    def on_message(client, userdata, msg):
        print('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
        y = msg.payload
        x = json.loads(y)
        print(str(msg.payload))
        sense.lowLight = True
        sense.show_message(str(x['params']), text_colour=text, back_colour=back,  scroll_speed=0.05)


    THINGSBOARD_HOST = 'demo.thingsboard.io'
    ACCESS_TOKEN = 'P2-4DemoToken'

    INTERVAL = 5

    sense = SenseHat()
    sensor_data = {'temperature': 0, 'humidity': 0, 'waterLevel': 0.0}

    next_reading = time.time()

    client = mqtt.Client()

    # Set access token
    client.username_pw_set(ACCESS_TOKEN)

    # Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
    client.connect(THINGSBOARD_HOST, 1883, 60)


    client.loop_start()

    try:
        while True:
            humidity = sense.get_humidity()
            temperature = sense.get_temperature()
            with open('waterLevelData(Live).csv','r') as f:
                    waterLevel = float(f.readlines()[-1]) 
            humidity = round(humidity, 2)
            temperature = round(temperature, 2)
            waterLevel = round(waterLevel, 2)   
            print(u"Temperature: {:g}, Humidity: {:g}%, waterLevel: {:g}".format(temperature, humidity, waterLevel))
            sensor_data['waterLevel'] = waterLevel
            sensor_data['temperature'] = temperature
            sensor_data['humidity'] = humidity

            # Sending humidity and temperature data to ThingsBoard
            client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
            client.subscribe('v1/devices/me/rpc/request/+')
            client.on_message = on_message

            next_reading += INTERVAL
            sleep_time = next_reading-time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":

    # creating threads
    t1 = threading.Thread(target=ble_pi, name='t1')
    t2 = threading.Thread(target=thingsboardpushdata, name='t2')  
  
    # starting threads
    t1.start()
    t2.start()
  
    # wait until all threads finish
    t1.join()
    t2.join()