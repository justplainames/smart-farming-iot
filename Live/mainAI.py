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

import argparse
import cv2
import numpy as np
#from threading import Thread
import importlib.util

import threading


from bleak import BleakScanner, BleakClient

mqttBroker = "mqtt.eclipseprojects.io"
harvest_client = mqtt.Client("pasir_ris_c1")  # give client name
HARVEST_THRESHOLD = 10000

class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

	# Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	# Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
	# Return the most recent frame
        return self.frame

    def stop(self):
	# Indicate that the camera and thread should be stopped
        self.stopped = True


def harvest():
    harvest = False
    # Define and parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--modeldir', help='Folder the .tflite file is located in')
    parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                        default='detect.tflite')
    parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                        default='labelmap.txt')
    parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                        default=0.5)
    parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                        default='640x480')
    parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                        action='store_true')

    args = parser.parse_args()

    #MODEL_NAME = args.modeldir
    MODEL_NAME = 'Sample_TFLite_model'
    GRAPH_NAME = args.graph
    LABELMAP_NAME = args.labels
    min_conf_threshold = float(args.threshold)
    resW, resH = args.resolution.split('x')
    imW, imH = int(resW), int(resH)
    use_TPU = args.edgetpu

    # Import TensorFlow libraries
    # If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
    # If using Coral Edge TPU, import the load_delegate library
    pkg = importlib.util.find_spec('tflite_runtime')
    if pkg:
        from tflite_runtime.interpreter import Interpreter
        if use_TPU:
            from tflite_runtime.interpreter import load_delegate
    else:
        from tensorflow.lite.python.interpreter import Interpreter
        if use_TPU:
            from tensorflow.lite.python.interpreter import load_delegate

    # If using Edge TPU, assign filename for Edge TPU model
    if use_TPU:
        # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
        if (GRAPH_NAME == 'detect.tflite'):
            GRAPH_NAME = 'edgetpu.tflite'       

    # Get path to current working directory
    CWD_PATH = os.getcwd()

    # Path to .tflite file, which contains the model that is used for object detection
    PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

    # Path to label map file
    PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

    # Load the label map
    with open(PATH_TO_LABELS, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Have to do a weird fix for label map if using the COCO "starter model" from
    # https://www.tensorflow.org/lite/models/object_detection/overview
    # First label is '???', which has to be removed.
    if labels[0] == '???':
        del(labels[0])

    # Load the Tensorflow Lite model.
    # If using Edge TPU, use special load_delegate argument
    if use_TPU:
        interpreter = Interpreter(model_path=PATH_TO_CKPT,
                                  experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        print(PATH_TO_CKPT)
    else:
        interpreter = Interpreter(model_path=PATH_TO_CKPT)

    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    floating_model = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Initialize frame rate calculation
    frame_rate_calc = 1
    freq = cv2.getTickFrequency()

    detected = False

    # Initialize video stream
    #camera = cv2.VideoCapture(0)
    videostream = VideoStream(resolution=(imW,imH),framerate=30)
    time.sleep(1)
    start = time.time()

#try:
    #for frame1 in camera.capture_continuous(rawCapture, format="bgr",use_video_port=True):
    #while(True):
    detectionCounter=0
    # Start timer (for calculating frame rate)
    t1 = cv2.getTickCount()

    # Grab frame from video stream
    for i in range(10):
        frame1 = videostream.read()

    # Acquire frame and resize to expected shape [1xHxWx3]
    frame = frame1.copy()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (width, height))
    input_data = np.expand_dims(frame_resized, axis=0)

    # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
    if floating_model:
        input_data = (np.float32(input_data) - input_mean) / input_std

    # Perform the actual detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'],input_data)
    interpreter.invoke()

    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
    classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
    scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects
    #num = interpreter.get_tensor(output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)

    # Loop over all detections and draw detection box if confidence is above minimum threshold
    biggest = 0
    for i in range(len(scores)):
        # Get bounding box coordinates and draw box
        # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
        ymin = int(max(1,(boxes[i][0] * imH)))
        xmin = int(max(1,(boxes[i][1] * imW)))
        ymax = int(min(imH,(boxes[i][2] * imH)))
        xmax = int(min(imW,(boxes[i][3] * imW)))
            
        if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):
            # Draw label
            object_name = labels[int(classes[i])] # Look up object name from "labels" array using class index
            if (object_name =='apple'):
                detectionCounter=detectionCounter+1
                print(detectionCounter)
                area = (ymax-ymin)*(xmax-xmin)
                if (area > biggest):
                    biggest = area
                    largestymin = ymin
                    largestxmin = xmin
                    largestymax = ymax
                    largestxmax = xmax
                    label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'
                    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                    label_ymin = max(largestymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
                    
                    cv2.rectangle(frame, (largestxmin, label_ymin-labelSize[1]-10), (largestxmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
                    cv2.putText(frame, label, (largestxmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text
                    cv2.rectangle(frame, (largestxmin,ymin), (largestxmax,largestymax), (10, 255, 0), 2)
                        
    if detectionCounter == 0:
        print("No detection")
        #if (detected == True):
        #    detected = False
        print(detected)
            #ser.write(bytes('b', 'utf-8'))
    else:
        #if (detected == False):
        #    detected = True
            print(detected)
            #ser.write(bytes('a', 'utf-8'))
            if (biggest > HARVEST_THRESHOLD):
                print("Detected Size: ",biggest)
                print("HARVEST TIME!")
                harvest = True
            else:
                print("Detected Size: ",biggest)
                print("Not Ready...")
                harvest = False
        
    # Draw framerate in corner of frame
    #cv2.putText(frame,'FPS: {0:.2f}'.format(frame_rate_calc),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)

    # All the results have been drawn on the frame, so it's time to display it.
    #cv2.imshow('Object detector', frame)

    # Calculate framerate
    #t2 = cv2.getTickCount()
    #time1 = (t2-t1)/freq
    #frame_rate_calc= 1/time1
    #time.sleep(1)

    # Press 'q' to quit
    #if cv2.waitKey(1) == ord('q'):
    #    break

# Clean up
    #cv2.destroyAllWindows()
    cv2.imwrite("test.jpg",frame)
    videostream.stop()
    print(harvest)
    return harvest


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
                        #print(val1)
                        out_q.put(val1)
                        #print(val1)
                        # f = open('waterLevelData(Live).csv', 'w')
                        # writer = csv.writer(f)
                        # writer.writerow(val)

                    print("Subscribing to characteristic changes...")
                    while(client.is_connected):
                        await client.start_notify(CHAR_UUID, callback)
                        await asyncio.sleep(15)
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
    start = time.time()
    size = False

    try:
        while True:
            humidity = sense.get_humidity()
            temperature = sense.get_temperature()
            # with open('waterLevelData(Live).csv','r') as f:
            #         waterLevel = float(f.readlines()[-1])
            humidity = round(humidity, 2)
            temperature = round(temperature, 2)
            waterLevel = in_q.get()
            #print("thread2:", waterLevel)
            elapsedtime = time.time() - start
            #print("ELAPSED TIME: ",elapsedtime)
            if(elapsedtime > 10):
                print("Checking Cabbage Size...")
                start = time.time()
                size = harvest()
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
    #t3 = threading.Thread(target=harvest)

    # starting threads
    t1.start()
    t2.start()
    #t3.start()

    # wait until all threads finish
    t1.join()
    t2.join()
    #t3.join()
