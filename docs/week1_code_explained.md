# 第1周代码逐行讲解

## 一、整体架构图

```
┌──────────────────────────────────────────────────────────────┐
│                    数据采集链路 (Data Pipeline)                 │
├──────────────┬───────────────────┬───────────────────────────┤
│  ① 传感器层   │   ② 通信层        │     ③ 应用层              │
│              │                   │                           │
│  DHT11  ──┐  │                   │                           │
│  (温度湿度) │  │  串口(Serial)     │  Python 数据接收器         │
│            ├──│── JSON 文本流 ────│── parse → buffer → file   │
│  光敏电阻 ─┘  │                   │                           │
│  (光照强度)    │  baud=115200      │  data/sensor_data_*.json │
└──────────────┴───────────────────┴───────────────────────────┘
           ↑                        ↑
      ESP32 固件               Python 脚本
      (C++)                    (agent/src/week1/)
```

---

## 二、ESP32 固件详解 (C++)

文件：[`firmware/esp32_device/src/main.cpp`](E:/llm_embedded_project/firmware/esp32_device/src/main.cpp)

### 第1-10行：头文件引入

```cpp
#include <Arduino.h>      // Arduino 核心库 - 提供 pinMode, digitalWrite, Serial 等
#include <DHT.h>          // DHT 传感器库 - 读取温湿度
#include <ArduinoJson.h>  // JSON 库 - 构建结构化数据包（轻量级，适合嵌入式）
```

### 第12-18行：全局定义

```cpp
#define DHTPIN 4          // DHT11 数据引脚接 GPIO4
#define DHTTYPE DHT11     // 传感器型号（还有 DHT22 精度更高）
#define ANALOG_PIN 34     // 光敏电阻接 GPIO34 (ADC1通道，WiFi下也稳定)
#define LED_BUILTIN 2     // ESP32 板载 LED 在 GPIO2

DHT dht(DHTPIN, DHTTYPE); // 创建 DHT 对象，传入引脚和型号
```

**为什么用 GPIO34 做模拟输入？**
- ESP32 有两组 ADC：ADC1 (GPIO32-39) 和 ADC2 (GPIO0,2,4,12-15,25-27)
- **ADC2 在 WiFi 开启时会受影响**，所以传感器接 ADC1 (GPIO34)

### 第20-22行：时间控制变量

```cpp
const unsigned long SEND_INTERVAL = 5000;  // 发送间隔 5000ms = 5秒
unsigned long lastSendTime = 0;            // 上次发送时间
```

**这是嵌入式非阻塞编程的核心技巧：** 用 `millis()` 计时而非 `delay()`，这样 loop() 可以同时做其他事（如按键检测）。

### 第24-32行：setup() — 初始化

```cpp
void setup() {
  Serial.begin(115200);     // 开启串口，波特率115200（与 platformio.ini 一致）
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);  // 初始熄灭
  
  dht.begin();
  Serial.println("ESP32 Sensor Node Started");
  Serial.println("{\"event\":\"system\",\"status\":\"ready\"}");
  // 发送一个 JSON 格式的启动状态（方便 Python 端解析）
}
```

**波特率 115200 是什么意思？**
- 串口每秒传输 115200 比特
- 这个值必须和 Python 端的 `serial.Serial(port, 115200)` 一致，否则乱码

### 第34-71行：loop() — 主循环

```cpp
void loop() {
  unsigned long now = millis();  // 获取当前时间（ms）
  
  if (now - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = now;  // 更新计时
    
    // ── 读取传感器 ──
    float humidity = dht.readHumidity();       // 读取湿度 (%)
    float temperature = dht.readTemperature();  // 读取温度 (°C)
    int analogValue = analogRead(ANALOG_PIN);   // 读取模拟值 (0-4095)
    
    // ── 构建 JSON ──
    StaticJsonDocument<256> doc;     // 分配 256 字节的静态 JSON 文档
    doc["device_id"] = "esp32_001";  // 设备标识（多设备时区分）
    doc["timestamp"] = now;          // 时间戳
    
    JsonObject sensors = doc.createNestedObject("sensors"); // 嵌套对象
    
    if (!isnan(humidity) && !isnan(temperature)) {  // isnan 检查读数是否有效
      sensors["temperature"]["value"] = temperature;
      sensors["temperature"]["unit"] = "c";
      sensors["humidity"]["value"] = humidity;
      sensors["humidity"]["unit"] = "%";
    }
    
    sensors["light"]["value"] = analogValue;
    sensors["light"]["unit"] = "raw";
    
    // ── 串口发送 ──
    serializeJson(doc, Serial);  // 将 JSON 写入串口
    Serial.println();            // 换行符（Python 靠它分隔每条数据）
    
    // ── 指示 ──
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);
  }
}
```

**串口发送的数据格式（真实输出）：**
```json
{"device_id":"esp32_001","timestamp":5000,"sensors":{"temperature":{"value":25.6,"unit":"c"},"humidity":{"value":60.2,"unit":"%"},"light":{"value":2048,"unit":"raw"}}}
```

### DHT11 vs DHT22

| 特性 | DHT11 | DHT22 |
|------|-------|-------|
| 温度范围 | 0~50°C (±2°C) | -40~80°C (±0.5°C) |
| 湿度范围 | 20~90% (±5%) | 0~100% (±2%) |
| 采样周期 | 1秒 | 2秒 |
| 价格 | 便宜 | 稍贵 |

代码中 `#define DHTTYPE DHT11` 改为 `DHT22` 即可切换。

---

## 三、Python 数据接收器详解

文件：[`data_receiver.py`](E:/llm_embedded_project/agent/src/week1_data_collection/data_receiver.py)

### 类：SensorDataReceiver

```
                数据流:
                  
  原始 JSON 字符串           Python 字典              磁盘文件
  ┌──────────┐    json.loads()   ┌──────────┐  批量写入  ┌──────────┐
  │ "{...}"   │ ───────────────→ │ {...}     │ ───────→ │ [...]    │
  │ "{...}"   │                  │ {...}     │          │ {...},   │
  │ "{...}"   │                  │ {...}     │          │ {...}    │
  └──────────┘                  └──────────┘          └──────────┘
                                 缓冲区 buffer           JSON 数组
                                 内存中暂存              持久化存储
```

### 逐行解析

```python
class SensorDataReceiver:
    """传感器数据接收器"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)        # Path 对象，跨平台路径处理
        self.data_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录
        self.buffer: list = []                # 数据缓冲区
```

**为什么用缓冲区？**
- 每收到一条数据就写磁盘 → 频繁 I/O，效率低
- 先攒一批（如 10 条或 30 秒）→ 一次性写入 → 性能提升 100 倍
- 这是 IoT 设备端的通用设计模式

```python
    def receive_data(self, raw_data: str) -> Dict[str, Any]:
        try:
            data = json.loads(raw_data)        # JSON 字符串 → Python 字典
            data["timestamp"] = datetime.now().isoformat()  # 添加接收时间
            self.buffer.append(data)           # 存入缓冲区
            return {"status": "ok", "data": data}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": str(e)}
```

**json.loads() 的作用：**
```python
# 串口传来的字符串:
'{"temperature": {"value": 25.6, "unit": "c"}}'

# json.loads() 之后:
{"temperature": {"value": 25.6, "unit": "c"}}
# ↑ 变成了真正的 Python 字典，可以直接 dict["temperature"]["value"] 访问
```

```python
    def flush_to_disk(self) -> int:
        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # 例: sensor_data_20260514_134050.json
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.buffer, f, ensure_ascii=False, indent=2)
            # indent=2 → 格式化输出，方便人类阅读
            # ensure_ascii=False → 支持中文等非 ASCII 字符
        
        count = len(self.buffer)
        self.buffer.clear()    # 清空缓冲区
        return count
```

---

## 四、ESP32 模拟器详解

文件：[`simulate_esp32.py`](E:/llm_embedded_project/agent/src/week1_data_collection/simulate_esp32.py)

### 为什么需要模拟器？

```
真实场景:                        你现在:
┌──────────┐     串口线      ┌──────────┐    ┌──────────┐
│  ESP32   │ ──────────────→ │  电脑    │    │  电脑    │
│ (硬件)   │   115200 baud   │ Python   │    │ Python   │
│ DHT11    │                 │ 接收器   │    │ 模拟器   │ ← 假装自己是 ESP32
└──────────┘                 └──────────┘    └──────────┘
```

模拟器生成的 JSON 格式和真实 ESP32 **完全一致**，所以 Python 接收器不需要任何修改。

### 模拟器核心逻辑

```python
class ESP32Simulator:
    def __init__(self, device_id="esp32_001", interval=2.0):
        self.temperature = 25.0   # 初始温度
        self.humidity = 55.0      # 初始湿度
        self.light = 2000         # 初始光照（0-4095）

    def read_sensors(self):
        # 每次读数加一点随机波动，模拟真实传感器的噪声
        self.temperature += random.uniform(-0.3, 0.3)
        self.humidity += random.uniform(-1.0, 1.0)
        self.light += random.randint(-100, 100)
        
        # 限制合理范围（对应真实物理世界的上下限）
        self.temperature = max(15, min(35, self.temperature))    # 15~35°C
        self.humidity = max(30, min(80, self.humidity))          # 30~80%
        self.light = max(0, min(4095, self.light))               # 0~4095
```

**随机波动模拟了什么？**
- 温度 ±0.3°C → 真实 DHT11 的读数噪声
- 湿度 ±1% → 空气流动导致的自然变化
- 光照 ±100 → 环境光线微小变化

### 运行流程

```
main() 函数执行流程：

① 创建接收器         receiver = SensorDataReceiver()
② 创建模拟器         simulator = ESP32Simulator(interval=1.0)
③ 运行模拟           simulator.run(count=5, receiver=receiver)
                        │
                        ├─ 第1秒: 生成数据 → receive_data() → buffer
                        ├─ 第2秒: 生成数据 → receive_data() → buffer
                        ├─ 第3秒: 生成数据 → receive_data() → buffer
                        ├─ 第4秒: 生成数据 → receive_data() → buffer
                        └─ 第5秒: 生成数据 → receive_data() → buffer
④ 保存数据           receiver.flush_to_disk() → data/*.json
```

---

## 五、第1周工具/插件用法

### 1. PlatformIO (嵌入式开发)

**位置：** VS Code 左侧栏 → PlatformIO 图标 (小蚂蚁)

**主要操作：**

| 操作 | 方法 | 说明 |
|------|------|------|
| **编译** | PlatformIO → `Build` 或 `Ctrl+Alt+B` | 编译 ESP32 固件 |
| **上传** | PlatformIO → `Upload` 或 `Ctrl+Alt+U` | 烧录到 ESP32 硬件 |
| **串口监视** | PlatformIO → `Serial Monitor` | 查看 ESP32 串口输出 |
| **新建项目** | PlatformIO → `Open` → `New Project` | 创建新的嵌入式项目 |

**platformio.ini 配置解读：**
```ini
[env:esp32dev]               # 环境名称
platform = espressif32       # 平台（ESP32 芯片系列）
board = esp32dev             # 开发板型号（ESP32 DevKit V1）
framework = arduino          # 使用 Arduino 框架（更方便）
monitor_speed = 115200       # 串口监视器波特率
lib_deps =                   # 依赖库（自动从网上下载）
    bblanchon/ArduinoJson@^7.0.0
    knolleary/PubSubClient@^2.8
    adafruit/DHT sensor library@^1.4.0
```

### 2. Wokwi (电路仿真)

**位置：** VS Code 命令面板 (`F1` → `Wokwi: Start Simulator`)

**作用：** 不需要真硬件，就在电脑上模拟运行 ESP32

**使用步骤：**
1. 在 VS Code 中打开项目根目录 `E:\llm_embedded_project`
2. 按 `F1` → 输入 `Wokwi: Start Simulator`
3. 选择 `firmware/esp32_device`
4. 浏览器会弹出仿真界面：
   - 左侧：ESP32 开发板电路图
   - 右侧：串口输出面板
   - 点击 DHT22 传感器 → 弹窗可调节温湿度值
   - 点击光敏电阻 → 可调节光照强度

**仿真配置文件：**
- [`.wokwi/diagram.json`](E:/llm_embedded_project/.wokwi/diagram.json) — 电路连接图
- [`.wokwi/wokwi.toml`](E:/llm_embedded_project/.wokwi/wokwi.toml) — 仿真设置

### 3. VS Code Python 扩展

**位置：** VS Code 左侧栏 → 扩展图标 (已安装)

**帮助功能：**
- **代码补全：** 输入 `json.` 会自动提示 `loads()`、`dumps()` 等方法
- **错误检查：** 语法错误会在代码下画红色波浪线，鼠标悬停看详情
- **类型提示：** `def receive_data(self, raw_data: str) -> Dict[str, Any]:` 这种写法，调用时会提示参数类型
- **调试功能：** 点击行号左边添加断点 → `F5` 启动调试 → 可以单步执行

### 4. 串口读取器 (serial_reader.py)

文件：[`serial_reader.py`](E:/llm_embedded_project/agent/src/week1_data_collection/serial_reader.py)

**什么时候用？** 当你有了真实的 ESP32 硬件，通过 USB 连接到电脑时。

**使用方法：**
```bash
# 查看 ESP32 连接到了哪个 COM 口（Windows 设备管理器查看）
# 假设是 COM3
cd E:\llm_embedded_project
F:\Anaconda3\envs\llm_embedded\python.exe -X utf8 agent/src/week1_data_collection/serial_reader.py COM3 30
#                                                               ↑端口  ↑读取30秒
```

**工作原理：**
```python
while True:
    if serial.in_waiting > 0:          # 串口有数据等待读取
        char = serial.read(1)          # 每次读1个字符
        if char == '\n':               # 遇到换行符，一条完整JSON结束
            parse_and_store(line)      # 解析这条数据
            line = ""                  # 开始下一条
        else:
            line += char               # 拼接字符
```

**为什么逐字符读取而不是 `readline()`？**
- ESP32 发送 JSON 是一行，但串口传输可能被拆分成多个包
- 逐字符读取 + 检测 `\n` 换行符，是最可靠的方式

### 5. 数据可视化 (visualize_data.py)

文件：[`visualize_data.py`](E:/llm_embedded_project/agent/src/week1_data_collection/visualize_data.py)

**作用：** 将保存的 JSON 数据画成折线图

```bash
cd E:\llm_embedded_project
F:\Anaconda3\envs\llm_embedded\python.exe -X utf8 agent/src/week1_data_collection/visualize_data.py
```

会弹出 matplotlib 窗口，显示三条曲线：
- 红色：温度变化
- 蓝色：湿度变化
- 黄色：光照变化

---

## 六、核心概念总结

### 你学到了什么？

| 概念 | 解释 | 代码体现 |
|------|------|---------|
| **序列化** | 把内存数据转成可传输的文本 | C++: `serializeJson()` / Python: `json.dumps()` |
| **反序列化** | 把文本解析回内存数据 | Python: `json.loads()` |
| **缓冲区** | 暂存数据，攒一批再处理 | Python: `self.buffer: list = []` |
| **非阻塞编程** | 用 `millis()` 计时而非 `delay()` | C++: `if (now - lastSendTime >= interval)` |
| **波特率** | 串口通信速度，两端必须一致 | C++: `Serial.begin(115200)` / Python: `serial.Serial(port, 115200)` |
| **ADC** | 模拟信号转数字值 (0-4095) | C++: `analogRead(34)` |
| **JSON 嵌套** | 用层级结构组织复杂数据 | C++: `doc.createNestedObject("sensors")` |

### 完整数据流回顾

```
真实世界:
物理量 (温度25°C)
  → DHT11 传感器 (电阻变化)
    → ESP32 读取 (数字信号)
      → JSON 格式化 (字符串)
        → 串口发送 (电信号)
          → 电脑接收 (Python)
            → 解析存储 (JSON文件)
              → 后续分析 (LLM智能体)
```

**这就是物联网数据采集的标准架构！** 大公司如阿里云 IoT、AWS IoT 也是这个模式，只是把串口换成了 WiFi/MQTT（第3周的内容）。