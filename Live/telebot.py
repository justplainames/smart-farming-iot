from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from pandas import *
import requests

TOKEN = "5172874200:AAHQvea7ycHSR5xTWSMOUQZI7io2632BVjk"

data = read_csv("Data(Live).csv")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hi! :) Welcome to the Smart Argiculture Bot created by SIT-UoG Computing Science Students. Please write /help to see the commands available.")

def help(update: Update, context: CallbackContext):
    update.message.reply_text("""Available Commands :\n
    /viewdata - To view dashboard of the data on Thingsboard\n
    /humidity - To get current humidity data\n
    /temperature - To get current temperature data\n
    /waterlevel - To get current water level data""")

def data_url(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Your link here https://demo.thingsboard.io/dashboard/f70ba180-b25d-11ec-a14a-ddee2b216d1b?publicId=403452a0-b34c-11ec-a0c1-cff7830564bf")

def humidity(update: Update, context: CallbackContext):
    data = read_csv("Data(Live).csv")
    humidity = data['humidity'].tolist()
    humidity = humidity[-1]
    update.message.reply_text(humidity)

def temperature(update: Update, context: CallbackContext):
    data = read_csv("Data(Live).csv")
    temp = data['temp'].tolist()
    temp = temp[-1]
    update.message.reply_text(temp)

def waterLevel(update: Update, context: CallbackContext):
    data = read_csv("Data(Live).csv")
    water = data['water'].tolist()
    water = water[-1]
    update.message.reply_text(water)


updater = Updater(TOKEN, use_context=True)
data = read_csv("Data(Live).csv")
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('viewdata', data_url))
updater.dispatcher.add_handler(CommandHandler('humidity', humidity))
updater.dispatcher.add_handler(CommandHandler('temperature', temperature))
updater.dispatcher.add_handler(CommandHandler('waterlevel', waterLevel))
updater.start_polling()
