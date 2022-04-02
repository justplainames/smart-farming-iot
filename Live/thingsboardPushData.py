import os
import time
import sys
import paho.mqtt.client as mqtt
import json
import csv
from sense_hat import SenseHat

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
ACCESS_TOKEN = '8DjYuRVnY2KZJU1c9whc'

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