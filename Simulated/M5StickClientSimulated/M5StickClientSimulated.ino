/*
  Soil Moisture Sensor
  modified on 21 Feb 2019
  by Saeed Hosseini @ Electropeak
  https://electropeak.com/learn/
*/
//#include "M5Stack.h"
#include "M5StickCPlus.h"

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914c"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a9"
BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
//      M5.Lcd.println("connect");
      Serial.printf("connect\n");
      deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer) {
//      M5.Lcd.println("disconnect");
      Serial.printf("disconnect\n");
      deviceConnected = false;
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onRead(BLECharacteristic *pCharacteristic) {
//      M5.Lcd.println("read");
      Serial.printf("read\n");
      pCharacteristic->setValue("Hello World!");
    }

    void onWrite(BLECharacteristic *pCharacteristic) {
      Serial.printf("write\n");
//      M5.Lcd.println("write");
      std::string value = pCharacteristic->getValue();
//      M5.Lcd.println(value.c_str());
      
    }
};

//define SensorPin A0 //This is for Arduino board
float  sensorValue  = 0;
float list[]={1,2,3,4,5,4,3,2,1,0};
void setup() {
  Serial.printf("setup\n");
  M5.begin();
  //M5.Lcd.setBrightness(0);
  M5.Lcd.setTextColor(TFT_GREEN, TFT_BLACK);
  M5.Lcd.setTextSize(3);
  M5.Lcd.setRotation(1);
//  pinMode(36, INPUT);
//  gpio_pulldown_dis(GPIO_NUM_25);
//  gpio_pullup_dis(GPIO_NUM_25);
  Serial.begin(9600);
  //  m5.Speaker.mute();

  BLEDevice::init("m5-stack-simulated");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_NOTIFY |
                      BLECharacteristic::PROPERTY_INDICATE
                    );
  pCharacteristic->setCallbacks(new MyCallbacks());
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();
  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->start();
}
void loop() {
  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->start();
//  for (int i = 0; i <= 100; i++)
//  {
//    sensorValue = sensorValue + analogRead(36);
//    delay(1);
//  }
  //sensorValue = sensorValue / 100.0;
  //  M5.Lcd.printf("Water Level: %d\n", sensorValue);
  Serial.println(sensorValue);
  delay(30);
  if (deviceConnected) {
    //    Serial.printf("*** Sent Value: %d ***\n", sensorValue);
    pCharacteristic->setValue(list[0]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[1]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[2]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[3]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[4]);
    pCharacteristic->notify();
    delay(5000);
    pCharacteristic->setValue(list[5]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[6]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[7]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[8]);
    pCharacteristic->notify();
    delay(5000);
     pCharacteristic->setValue(list[9]);
    pCharacteristic->notify();
    delay(5000);
  }
//  else {
//    esp_light_sleep_start();
//  }
  M5.update();


}
