#include <M5StickC.h>
#include <BLEDevice.h> // Bluetooth Low Energy 
#include <BLEServer.h> // Bluetooth Low Energy
#include <BLEUtils.h> // Bluetooth Low Energy
#include <esp_sleep.h>

#define T_PERIOD 10 // Number of seconds to send advertizing packets
#define S_PERIOD 20 // Number of seconds to Deep Sleep

void setAdvData(BLEAdvertising *pAdvertising) { // Formatting Advertising Packets
    BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();

    oAdvertisementData.setFlags(0x06); // BR_EDR_NOT_SUPPORTED | General Discoverable Mode
    // oAdvertisementData.setFlags(0x05); // BR_EDR_NOT_SUPPORTED | Limited Discoverable Mode

    std::string strServiceData = "";
    strServiceData += (char)0x0c; // Length(12Byte)
    strServiceData += (char)0xff; // AD Type 0xFF: Manufacturer specific data
    strServiceData += (char)0xff; // Test manufacture ID low byte
    strServiceData += (char)0xff; // Test manufacture ID high byte
    strServiceData += (char)seq; // sequence number

    oAdvertisementData.addData(strServiceData);
    pAdvertising->setAdvertisementData(oAdvertisementData);
}


void setup() {
    M5.begin();
    M5.Axp.ScreenBreath(10); // Reduce the brightness of the screen
    M5.Lcd.setRotation(1); // Change the direction of the LCD
    M5.Lcd.setTextSize(2); // Set font size to 2
    M5.Lcd.setTextColor(WHITE, BLACK); // White for text, black for background
