import paho.mqtt.client as mqtt
import time
from sense_hat import SenseHat

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from pandas import *
import requests

sense = SenseHat()
text = (255, 0, 0)
back = (0, 0, 0)



def on_message(client, userdata, message):
    print("received message:", str(message.payload.decode("utf-8")))
    msg = str(message.payload.decode("utf-8"))
    # <-Add code to change LED here ->
    # y = msg.payload
    # x = json.loads(y)
    # print(str(msg.payload))
    # sense.lowLight = True
    sense.show_message(msg, text_colour=text,
                       back_colour=back,  scroll_speed=0.05)


def on_message2(client, userdata, message):
    print("received message:", str(message.payload.decode("utf-8")))
    msg = str(message.payload.decode("utf-8"))
    # <-Add code to change LED here ->
    # y = msg.payload
    # x = json.loads(y)
    # print(str(msg.payload))
    # sense.lowLight = True
    357224626
    if msg == "harvest":
        base_url = 'https://api.telegram.org/bot5172874200:AAHQvea7ycHSR5xTWSMOUQZI7io2632BVjk/sendMessage?chat_id=357224626&text=TIME TO HARVEST:)'
        requests.get(base_url)


mqttBroker = "mqtt.eclipseprojects.io"
# give client name
client = mqtt.Client("pasir_ris/container_1/temperature_control")
harvest_client = mqtt.Client('pasir_ris/container_1/harvest')
client.connect(mqttBroker)
harvest_client.connect(mqttBroker)


while True:
    client.loop_start()
    harvest_client.loop_start()
    client.subscribe("pasir_ris/container_1/temperature_control")
    harvest_client.subscribe('pasir_ris/container_1/harvest')
    client.on_message = on_message
    harvest_client.on_message = on_message2
    time.sleep(30)
    client.loop_stop()
    harvest_client.loop_stop()
