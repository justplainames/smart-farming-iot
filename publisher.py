import requests
import json
from requests.structures import CaseInsensitiveDict
import paho.mqtt.client as paho  # mqtt library
import os
import json
import time
from datetime import datetime, timedelta

# Set budget
BUDGET = 300
API_KEY = "3c3bfe5fe77a667b64fd41b816d29c11"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
LOCATIONS = ["pasir ris", "tuas"]
DEVICE_PASIR = '47a94bb0-b25e-11ec-a14a-ddee2b216d1b'
DEVICE_TUAS = 'c90dc490-b260-11ec-a14a-ddee2b216d1b'

# startTs=1648531324856&endTs=1648531407418
endTime = time.time() * 1000
dtime = datetime.now() - timedelta(seconds=300)
startTime = time.mktime(dtime.timetuple()) * 1000

# REST API attributes to get thingsboard from first location temperature device readings

headers = CaseInsensitiveDict()
headers["X-Authorization"] = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJqdXN0cGxhaW5hbWVzQGhvdG1haWwuY29tIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJ1c2VySWQiOiJkZDdkYjkxMC1hOTk4LTExZWMtYTBjMS1jZmY3ODMwNTY0YmYiLCJmaXJzdE5hbWUiOiJjc2MiLCJsYXN0TmFtZSI6IjIwMDgiLCJlbmFibGVkIjp0cnVlLCJwcml2YWN5UG9saWN5QWNjZXB0ZWQiOnRydWUsImlzUHVibGljIjpmYWxzZSwidGVuYW50SWQiOiJkY2M0MmQxMC1hOTk4LTExZWMtYTBjMS1jZmY3ODMwNTY0YmYiLCJjdXN0b21lcklkIjoiMTM4MTQwMDAtMWRkMi0xMWIyLTgwODAtODA4MDgwODA4MDgwIiwiaXNzIjoidGhpbmdzYm9hcmQuaW8iLCJpYXQiOjE2NDg1Mjc2NjgsImV4cCI6MTY1MDMyNzY2OH0.-j1SL40oWmMJrDXwb_3ZqeGbhCEnl4tPbVqp9YNnXTe_UOghwlsjDt-q6DNCasFA0GS75E4dsX1uj7l_Cmstug"
headers["Content-Type"] = "application/json"

pasir_ris_telemetry = requests.get('http://demo.thingsboard.io/api/plugins/telemetry/DEVICE/'+DEVICE_PASIR +
                                   '/values/timeseries?keys=temperature,&startTs=' + str(int(startTime))+'&endTs='+str(int(endTime))+'&interval=10000&limit=5&agg=AVG', headers=headers)
tuas_telemetry = requests.get('http://demo.thingsboard.io/api/plugins/telemetry/DEVICE/'+DEVICE_TUAS + '/values/timeseries?keys=temperature,&startTs=' +
                              str(int(startTime))+'&endTs='+str(int(endTime))+'&interval=10000&limit=5&agg=AVG', headers=headers)

pasir_ris_telemetry_dict = json.loads(pasir_ris_telemetry.text)
tuas_telemetry_dict = json.loads(tuas_telemetry.text)

pasir_ris_json = pasir_ris_telemetry.json()
tuas_json = tuas_telemetry.json()
print(pasir_ris_json)

sumTemp1 = 0.0
sumTemp2 = 0.0

for x in pasir_ris_json['temperature']:
    # Average out all the temperature reading being captured
    sumTemp1 += float(pasir_ris_json['temperature'][0]['value'])
    # print(x)

for x in tuas_json['temperature']:
    # Average out all the temperature reading being captured
    sumTemp2 += float(tuas_json['temperature'][0]['value'])
    # print(x)

averagePasirRisTemp = sumTemp1 / len(pasir_ris_json['temperature'])
print("----First Container----")
print("sum of temperature is: ", str(sumTemp1) + " degree celcius",
      "\nAverage temperature is: ", str(averagePasirRisTemp) + " degree celcius")

averageTuasTemp = sumTemp2 / len(tuas_json['temperature'])
print("----Second Container----")
print("sum of temperature is: ", str(sumTemp2) + " degree celcius",
      "\nAverage temperature is: ", str(averageTuasTemp) + " degree celcius")

# API Request to retrieve temperature reading from openweather website
# First container location


# This is to complete the BASE_URL, you can also do this manually to checkout other weather data available
firstLocation_url = BASE_URL + "appid=" + API_KEY + "&q=" + LOCATIONS[0]
secondLocation_url = BASE_URL + "appid=" + API_KEY + "&q=" + LOCATIONS[1]
firstLocationResponse = requests.get(firstLocation_url)
secondLocationResponse = requests.get(secondLocation_url)
firstLocation_json = firstLocationResponse.json()
secondLocation_json = secondLocationResponse.json()


if firstLocation_json["cod"] != "404":
    getFirstTemp = firstLocation_json["main"]
    getSecondTemp = secondLocation_json["main"]

    # Convert from kelvin to degree celcius
    firstLocation_currentTemp = getFirstTemp["temp"] - 273.15
    secondLocation_currentTemp = getSecondTemp["temp"] - 273.15
    lowerTemp = 40.0
    lowerTempLocation = ""
    if secondLocation_currentTemp < firstLocation_currentTemp:
        lowerTemp = secondLocation_currentTemp
        higherTemp = firstLocation_currentTemp
        lowerTempLocation = LOCATIONS[1]
        higherTempLocation = '_'.join(LOCATIONS[0].split(" "))
    else:
        lowerTemp = firstLocation_currentTemp
        higherTemp = secondLocation_currentTemp
        lowerTempLocation = '_'.join(LOCATIONS[0].split(" "))
        higherTempLocation = LOCATIONS[1]

    print("----OpenWeather----")
    # First container location
    print("Temperature on "+LOCATIONS[0]+" is " +
          str(firstLocation_currentTemp) + " degree celcius")
    print("Temperature on "+LOCATIONS[1]+" is " +
          str(secondLocation_currentTemp) + " degree celcius")
    print("The location with higher temperature is: " + lowerTempLocation +
          " with a temperature of "+str(lowerTemp)+" degree celcius.")

else:
    print(" City Not Found ")


def on_publish(client, userdata, result):  # create function for callback
    print("----Send to thingsboard----")
    pass


def adjustor(value):
    # Calculates difference in containers and increases the container sequentially till same or necessary
    value = value
    newTemp = [16, 16]
    container_difference = averagePasirRisTemp - averageTuasTemp
    if averagePasirRisTemp < averageTuasTemp:
        newTemp[0] += container_difference
    else:
        newTemp[1] += container_difference
    print(value, container_difference)

    # Caluculates different environment temperature and adjusts inner container temperature based on environmental changes
    environemnt_difference = higherTemp - lowerTemp
    adjust_higher = (value-environemnt_difference)/2
    print(adjust_higher)
    adjust_lower = adjust_higher + environemnt_difference
    if firstLocation_currentTemp < secondLocation_currentTemp:
        newTemp[0] += adjust_lower
        newTemp[1] += adjust_higher
    else:
        newTemp[1] += adjust_lower
        newTemp[0] += adjust_higher

    for i in range(len(newTemp)):
        if newTemp[i] > 24.0:
            newTemp[i] = 24.0

    return newTemp


def newTempPublisher(newTemp):
    temperature_client.publish(
        f"pasir_ris/container_1/temperature_control", "{:.2f}".format(newTemp[0]))
    temperature_client.publish(
        f"tuas/container_1/temperature_control", "{:.2f}".format(newTemp[1]))
    print(
        f"Adjusts pasir_ris to {newTemp[0]}\nAdjusts Tuas to {newTemp[1]}")


# Connect MQTT broker for temperature control(mqtt.eclipseprojects.io)
mqttBroker = "mqtt.eclipseprojects.io"
temperature_client = paho.Client("Temperature_inside")  # give client name
temperature_client.connect(mqttBroker)

while True:

    # Set budget
    BUDGET = 300
    API_KEY = "3c3bfe5fe77a667b64fd41b816d29c11"
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
    LOCATIONS = ["pasir ris", "tuas"]
    DEVICE_PASIR = '47a94bb0-b25e-11ec-a14a-ddee2b216d1b'
    DEVICE_TUAS = 'c90dc490-b260-11ec-a14a-ddee2b216d1b'

    # startTs=1648531324856&endTs=1648531407418
    endTime = time.time() * 1000
    dtime = datetime.now() - timedelta(seconds=300)
    startTime = time.mktime(dtime.timetuple()) * 1000

    # REST API attributes to get thingsboard from first location temperature device readings

    headers = CaseInsensitiveDict()
    headers["X-Authorization"] = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJqdXN0cGxhaW5hbWVzQGhvdG1haWwuY29tIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJ1c2VySWQiOiJkZDdkYjkxMC1hOTk4LTExZWMtYTBjMS1jZmY3ODMwNTY0YmYiLCJmaXJzdE5hbWUiOiJjc2MiLCJsYXN0TmFtZSI6IjIwMDgiLCJlbmFibGVkIjp0cnVlLCJwcml2YWN5UG9saWN5QWNjZXB0ZWQiOnRydWUsImlzUHVibGljIjpmYWxzZSwidGVuYW50SWQiOiJkY2M0MmQxMC1hOTk4LTExZWMtYTBjMS1jZmY3ODMwNTY0YmYiLCJjdXN0b21lcklkIjoiMTM4MTQwMDAtMWRkMi0xMWIyLTgwODAtODA4MDgwODA4MDgwIiwiaXNzIjoidGhpbmdzYm9hcmQuaW8iLCJpYXQiOjE2NDg1Mjc2NjgsImV4cCI6MTY1MDMyNzY2OH0.-j1SL40oWmMJrDXwb_3ZqeGbhCEnl4tPbVqp9YNnXTe_UOghwlsjDt-q6DNCasFA0GS75E4dsX1uj7l_Cmstug"
    headers["Content-Type"] = "application/json"

    pasir_ris_telemetry = requests.get('http://demo.thingsboard.io/api/plugins/telemetry/DEVICE/'+DEVICE_PASIR +
                                       '/values/timeseries?keys=temperature,&startTs=' + str(int(startTime))+'&endTs='+str(int(endTime))+'&interval=10000&limit=5&agg=AVG', headers=headers)
    tuas_telemetry = requests.get('http://demo.thingsboard.io/api/plugins/telemetry/DEVICE/'+DEVICE_TUAS + '/values/timeseries?keys=temperature,&startTs=' +
                                  str(int(startTime))+'&endTs='+str(int(endTime))+'&interval=10000&limit=5&agg=AVG', headers=headers)

    pasir_ris_telemetry_dict = json.loads(pasir_ris_telemetry.text)
    tuas_telemetry_dict = json.loads(tuas_telemetry.text)

    pasir_ris_json = pasir_ris_telemetry.json()
    tuas_json = tuas_telemetry.json()

    sumTemp1 = 0.0
    sumTemp2 = 0.0

    for x in pasir_ris_json['temperature']:
        # Average out all the temperature reading being captured
        sumTemp1 += float(pasir_ris_json['temperature'][0]['value'])

    for x in tuas_json['temperature']:
        # Average out all the temperature reading being captured
        sumTemp2 += float(tuas_json['temperature'][0]['value'])

    averagePasirRisTemp = sumTemp1 / len(pasir_ris_json['temperature'])
    print("----First Container----")
    print("sum of temperature is: ", str(sumTemp1) + " degree celcius",
          "\nAverage temperature is: ", str(averagePasirRisTemp) + " degree celcius")

    averageTuasTemp = sumTemp2 / len(tuas_json['temperature'])
    print("----Second Container----")
    print("sum of temperature is: ", str(sumTemp2) + " degree celcius",
          "\nAverage temperature is: ", str(averageTuasTemp) + " degree celcius")

    # API Request to retrieve temperature reading from openweather website
    # First container location
    if BUDGET < 300:
        newTempPublisher(adjustor(8))
    elif BUDGET >= 300 and BUDGET < 325:
        newTempPublisher(adjustor(7))
    elif BUDGET >= 300 and BUDGET < 350:
        newTempPublisher(adjustor(6))
    elif BUDGET >= 300 and BUDGET < 375:
        newTempPublisher(adjustor(5))
    elif BUDGET >= 300 and BUDGET < 400:
        newTempPublisher(adjustor(4))
    else:
        print('No condition met to increase temperature')

    time.sleep(5)
