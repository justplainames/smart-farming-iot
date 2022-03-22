/* 
  Soil Moisture Sensor  
  modified on 21 Feb 2019 
  by Saeed Hosseini @ Electropeak 
  https://electropeak.com/learn/ 
*/
//#include "M5Stack.h"
#include "M5StickCPlus.h"
//define SensorPin A0 //This is for Arduino board
float sensorValue = 0; 
void setup() { 
   M5.begin();
   M5.Lcd.setTextColor(TFT_GREEN,TFT_BLACK);
   M5.Lcd.setTextSize(3);
   M5.Lcd.setRotation(1);
   pinMode(36, INPUT);
   gpio_pulldown_dis(GPIO_NUM_25);
   gpio_pullup_dis(GPIO_NUM_25);
   Serial.begin(9600); 
} 
void loop() { 
  for (int i = 0; i <= 100; i++) 
  { 
    sensorValue = sensorValue + analogRead(36); 
    delay(1); 
  } 
  sensorValue = sensorValue/100.0;
  M5.Lcd.printf("Water Level: %d\n",sensorValue); 
  Serial.println(sensorValue); 
  delay(30); 

}
