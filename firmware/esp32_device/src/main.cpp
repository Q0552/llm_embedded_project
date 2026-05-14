/**
 * 第1周：设备数据采集 - ESP32 固件
 * 
 * 功能：采集传感器数据并通过串口发送
 * 传感器：DHT11 (温度湿度) + 模拟传感器
 */

#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>

// 引脚定义
#define DHTPIN 4
#define DHTTYPE DHT11
#define ANALOG_PIN 34
#define LED_BUILTIN 2

DHT dht(DHTPIN, DHTTYPE);

// 数据发送间隔 (ms)
const unsigned long SEND_INTERVAL = 5000;
unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  
  dht.begin();
  Serial.println("ESP32 Sensor Node Started");
  Serial.println("{\"event\":\"system\",\"status\":\"ready\"}");
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = now;
    
    // 读取传感器
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    int analogValue = analogRead(ANALOG_PIN);
    
    // 构建 JSON 数据包
    StaticJsonDocument<256> doc;
    doc["device_id"] = "esp32_001";
    doc["timestamp"] = now;
    
    JsonObject sensors = doc.createNestedObject("sensors");
    
    if (!isnan(humidity) && !isnan(temperature)) {
      sensors["temperature"]["value"] = temperature;
      sensors["temperature"]["unit"] = "c";
      sensors["humidity"]["value"] = humidity;
      sensors["humidity"]["unit"] = "%";
    }
    
    sensors["light"]["value"] = analogValue;
    sensors["light"]["unit"] = "raw";
    
    // 串口发送 JSON
    serializeJson(doc, Serial);
    Serial.println();
    
    // LED 闪烁指示
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);
  }
}
