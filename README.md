# 2006-IoT-Project
IoT Project - Smart Agriculture

There are 3 main sections of the project
2 folders in the main directory, Live and Simulated:
1) Live - system that runs on actual data using sensors (Sense HAT temperature and humidity sensor, moisture sensor for water level, camera to take images of plant)
2) Simulated - system that run on fake/pre-recorded data
3) publisher.py - retrieve latest data from Thingsboard, using algorithm to determine new container temperature based on budget and local weather. Publish changes through MQTT

Within the Live/Simulated folder, you will find a set of files
1) M5StickClient - Folder containing M5StickCplus code to send moisture data to RPI the using BLE
2) main.py - the main code to run on the RPI, it performs the following tasks
a) it retrieves tempurature and humidity sensor data from the Sense Hat
b) consolidates all the moisture data 
c) performs object recognition on the plant to measure its size to determine when the plant is ready for harvest.
AI model details:
wget https://dl.google.com/coral/canned_models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite
mv mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite Sample_TFLite_model/edgetpu.tflite
4) subcriber.py - subscribe message from publisher to adjust tempurature
5) telebot.py (only for Live) - user can subscribe to a bot to request data via telegram
