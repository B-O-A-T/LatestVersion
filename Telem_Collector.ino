/*****************************************************************************************************************************************************
* Project: B.O.A.T.
* File: Telem_Collector.ino
* Authors: Lorenzo Kearns
* Purpose: This program runs cyclic executive scheduling to perform real time operation of sensor reading for the Autonomous Sailboat
*****************************************************************************************************************************************************/
//
//
/******************************************************************************/
//Includes:
#include <SPI.h>
/******************************************************************************/
//
//
/******************************************************************************/
//Global Definitions:
#define TASK1_PERIOD 1000 // in milliseconds
#define TASK2_PERIOD 1000 // in milliseconds
#define TASK3_PERIOD 100 // in milliseconds
/******************************************************************************/
//
//
/****************************************************************************/
//Global Variables:
//
bool debug = false; // set to true if you want to see debug outputs on serial console 
//Task countdown variables
unsigned long task1_countdown;
unsigned long task2_countdown;
unsigned long task3_countdown;

// Cereal Stuff
const int HANDSHAKE = 0;
const int WINDSPEED = 1;
const int APPARENTWINDANGLE = 2;
const int MOVERUDDER = 3;
const int SAILWINCH = 4;

// Anemometer
const int sensorPin = A0;
int sensorValue = 0;
float sensorVoltage = 0;
float windSpeed = 0;
float voltageConversionConstant = 0.0032258064;
float voltageMin = 0.417;
float windSpeedMin = 0;
float voltageMax = 2.0;
float windSpeedMax = 32;
float windSpeedAvg = 0.0;

// Wind vane
const int windVanePin = A1;
double windVaneOutput = 0.0;
int windDirection = 0;
double voltage = 0.0;
const int resistance = 165;
float current = 0.0;


/******************************************************************************/
//
//
//
/*******************************************************************************
* Function to call initialization and setup connection between the two radios  *
*******************************************************************************/
void setup() {
    // set up the LCD's number of columns and rows:
  Serial.begin(115200);
    // Initialize Sensors
  /********************************************************************************/
  
  /********************************************************************************/
  task1();
  task1_countdown = millis();
  task2();
  task2_countdown = millis();
  task3();
  task3_countdown = millis();
//  task4();
//  task4_countdown = millis();
//  task5();
//  task5_countdown = millis();
//  task6();
//  task6_countdown = millis();
}
// end of setup
/*****************************************************************************/
//
//
//
/*******************************************************************************
* heartbeat function of the system to run while the system is alive            *
*******************************************************************************/
void loop() {  
  if((unsigned long)(millis() - task1_countdown) >= TASK1_PERIOD) { // Read GPS sensor
      task1();
      task1_countdown = millis();
      if(windSpeed == 0){
        windSpeedAvg = 0;
      }
      windSpeedAvg = (windSpeedAvg + windSpeed)/2;
  }
  else if((unsigned long)(millis() - task2_countdown) >= TASK2_PERIOD) { // Reads Accelerometer
      task2();
      task2_countdown = millis();
  }  
  else if((unsigned long)(millis() - task3_countdown) >= TASK3_PERIOD) { // Reads Accelerometer
      task3();
      task3_countdown = millis();
  }  
}
// end of heartbeat
/*****************************************************************************/
//
//
//
/*******************************************************************************
* priority 1 function:                                    *
*******************************************************************************/
void task1() {
  windVaneOutput = analogRead(windVanePin);
  voltage = ((windVaneOutput)*voltageConversionConstant);
  current = voltage/resistance;
  windDirection = (int((22500 * current) - 90));
  if(debug){
//    Serial.print("Current: ");
//    Serial.print(current,4);
    Serial.print("Wind Direction: ");
    Serial.println(windDirection);
  }
}
// end of task1
/*****************************************************************************/
//
//
//
/*******************************************************************************
* priority 2 function:                 *
*******************************************************************************/
void task2() {
  sensorValue = analogRead(sensorPin);
  sensorVoltage = sensorValue * voltageConversionConstant;

  if (sensorVoltage <= voltageMin) { 
    windSpeed = 0; 
  } else { 
//    windSpeed = 1.94384 * (sensorVoltage - voltageMin)*windSpeedMax/(voltageMax - voltageMin); 
    windSpeed = (sensorVoltage - voltageMin)*windSpeedMax/(voltageMax - voltageMin); 
  }
  if(debug){
//    Serial.print("Voltage: ");
//    Serial.print(sensorVoltage);
//    Serial.print("\t");
    Serial.print("Wind speed: ");
    Serial.println(windSpeed);
//    delay(sensorDelay); 
  }
}
// end of task2
/*****************************************************************************/
//
//
//
///*******************************************************************************
//* priority 3 function:                              *
//*******************************************************************************/
void task3() {
  if (Serial.available() > 0) {
    // Read in request
    int inByte = Serial.read();
  
    // Take appropriate action
    switch(inByte) {
      case HANDSHAKE: // Handshake with OBC device to ensure communcation is working properly
        if (Serial.availableForWrite()) {
          Serial.println("689");
        }
        break;
      case WINDSPEED:
        if (Serial.availableForWrite()) {
          Serial.println(windSpeedAvg);
        }
        break;
      case APPARENTWINDANGLE:
        if (Serial.availableForWrite()) {
          Serial.println(windDirection);
        }
        break;
      case MOVERUDDER:
          if (Serial.availableForWrite()) {
            Serial.println(windDirection);
          }
          break;
      case SAILWINCH:
          if (Serial.availableForWrite()) {
            winch_sail();
            Serial.println(windDirection);
          }
          break;
    }
  }
}
//// end of task3
///*****************************************************************************/

void winch_sail() {
  Serial.println("689")
  if (Serial.available() > 0) {
    int sailAngle = Serial.read();
  }
}
