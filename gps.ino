#include <TinyGPS++.h>
#include <HardwareSerial.h>

// The LC76 uses 9600 baud by default
static const uint32_t GPSBaud = 115200;

// Define the Serial pins for the LC76
// Using ESP32's HardwareSerial 2
#define RXD2 16
#define TXD2 17

TinyGPSPlus gps;
HardwareSerial ss(2); // Use UART2

void setup() {
  Serial.begin(115200);
  ss.begin(GPSBaud, SERIAL_8N1, RXD2, TXD2);

  Serial.println("LC76 GPS Module Initializing...");
}

void loop() {
  // Feed the GPS data to the TinyGPS++ object
  while (ss.available() > 0) {
    if (gps.encode(ss.read())) {
      displayInfo();
    }
  }

  // If no data is received for 5 seconds, check wiring
  if (millis() > 5000 && gps.charsProcessed() < 10) {
    Serial.println("Error: No GPS data detected. Check wiring!");
    delay(2000);
  }
}

void displayInfo() {
  Serial.print(F("Location: ")); 
  if (gps.location.isValid()) {
    Serial.print(gps.location.lat(), 6);
    Serial.print(F(","));
    Serial.print(gps.location.lng(), 6);
  } else {
    Serial.print(F("INVALID (Waiting for Lock)"));
  }

  Serial.print(F("  Date/Time: "));
  if (gps.date.isValid()) {
    Serial.print(gps.date.month());
    Serial.print(F("/"));
    Serial.print(gps.date.day());
    Serial.print(F("/"));
    Serial.print(gps.date.year());
  }

  Serial.print(F(" "));
  if (gps.time.isValid()) {
    if (gps.time.hour() < 10) Serial.print(F("0"));
    Serial.print(gps.time.hour());
    Serial.print(F(":"));
    if (gps.time.minute() < 10) Serial.print(F("0"));
    Serial.print(gps.time.minute());
  }

  Serial.println();
}
