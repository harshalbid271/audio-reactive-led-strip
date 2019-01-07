#include <Arduino.h>
#include <ArduinoOTA.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#define FASTLED_ESP8266_DMA // better control for ESP8266 will output or RX pin requires fork https://github.com/coryking/FastLED
#include "FastLED.h"

/************ Network Information (CHANGE THESE FOR YOUR SETUP) ************************/
const char* ssid = "_A1306";
const char* password = "openopen";

const char* sensor_name = "TEST_SENSOR_HOSTNAME";
const char* ota_password = "OTA_PASSWORD";

const bool static_ip = true;
IPAddress ip(192, 168, 1, 112);
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);

const int udp_port1 = 7777;
const int udp_port2 = 7778;

/*********************************** FastLED Defintions ********************************/
#define NUM_LEDS      180
#define DATA_PIN1      6
#define DATA_PIN2      5
//#define CLOCK_PIN   2
#define CHIPSET       WS2812B
#define COLOR_ORDER   GRB

/*********************************** Globals *******************************************/
WiFiUDP port1;
WiFiUDP port2;

CRGB leds1[NUM_LEDS];
CRGB leds2[NUM_LEDS];

/********************************** Start Setup ****************************************/
void setup() {
  Serial.begin(115200);

  // Setup FastLED
  #ifdef CLOCK_PIN
    FastLED.addLeds<CHIPSET, DATA_PIN1, CLOCK_PIN, COLOR_ORDER>(leds1, NUM_LEDS);
    FastLED.addLeds<CHIPSET, DATA_PIN2, CLOCK_PIN, COLOR_ORDER>(leds2, NUM_LEDS);
  #else
    FastLED.addLeds<CHIPSET, DATA_PIN1, COLOR_ORDER>(leds1, NUM_LEDS);
    FastLED.addLeds<CHIPSET, DATA_PIN2, COLOR_ORDER>(leds2, NUM_LEDS);
  #endif

  // Setup the wifi connection
  setup_wifi();

  // Setup OTA firmware updates
  //setup_ota();

  // Initialize the UDP port
  port1.begin(udp_port1);
  port2.begin(udp_port2);
}

void setup_wifi() {
  delay(10);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.print(ssid);

  if (static_ip) {
    WiFi.config(ip, gateway, subnet);
  }
  
  WiFi.hostname(sensor_name);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setup_ota() {
  ArduinoOTA.setHostname(sensor_name);
  ArduinoOTA.setPassword(ota_password);

  ArduinoOTA.onStart([]() {
    Serial.println("Starting");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
  });
  ArduinoOTA.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    delay(1);
    Serial.print("WIFI Disconnected. Attempting reconnection.");
    setup_wifi();
    return;
  }
  
  //ArduinoOTA.handle();

  // TODO: Hookup either a more elaborate protocol, or a secondary
  // communication channel (i.e. mqtt) for functional control. This
  // will also give the ability to have some non-reative effects to
  // be driven completely locally making them less glitchy.

  // Handle UDP data
  int packetSize = port1.parsePacket();
  if (packetSize == sizeof(leds1)) {
    port1.read((char*)leds1, sizeof(leds1));
  } else if (packetSize) {
    Serial.printf("Invalid packet size: %u (expected %u)\n", packetSize, sizeof(leds1));
    port1.flush();
    return;
  }

  packetSize = port2.parsePacket();
  if (packetSize == sizeof(leds2)) {
    port2.read((char*)leds2, sizeof(leds2));
  } else if (packetSize) {
    Serial.printf("Invalid packet size: %u (expected %u)\n", packetSize, sizeof(leds2));
    port2.flush();
    return;
  }

  FastLED.show();

}
