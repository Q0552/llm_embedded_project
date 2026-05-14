# 🔌 第1周：设备数据采集

## 🎯 学习目标

1. 理解嵌入式传感器的工作原理和数据采集流程
2. 掌握 ESP32 读取数字传感器 (DHT11) 和模拟传感器的方法
3. 学会使用 JSON 格式在串口上传输结构化数据
4. 用 Python 编写串口数据解析器，完成数据的接收和存储
5. 通过 Wokwi 仿真验证完整的"采集→传输→解析→存储"链路

## 📚 理论知识

### 1. 传感器类型

| 类型 | 示例 | 接口 | 说明 |
|------|------|------|------|
| **数字传感器** | DHT11/DHT22 | 单总线 (OneWire) | 直接输出数字信号，需要特定时序协议 |
| **模拟传感器** | 光敏电阻、电位器 | ADC (模拟数字转换) | 输出连续电压，ESP32 ADC 精度 12-bit (0-4095) |
| **I2C 传感器** | BMP280、MPU6050 | I2C (SDA/SCL) | 通过地址访问，支持多设备 |
| **SPI 传感器** | SD卡、显示屏 | SPI (MOSI/MISO/SCLK/CS) | 高速通信，全双工 |

### 2. ESP32 引脚注意

- **ADC2 引脚** (GPIO 25-27, 32-39)：WiFi 开启时会影响 ADC2，建议使用 ADC1 (GPIO 32-39)
- 代码中使用 GPIO34 (ADC1_CH6) 是安全的
- DHT11 使用 GPIO4，任意数字引脚均可

### 3. JSON 数据格式

嵌入式端由于内存有限，使用 `ArduinoJson` 库构建轻量 JSON：

```json
{
  "device_id": "esp32_001",
  "timestamp": 5000,
  "sensors": {
    "temperature": { "value": 25.6, "unit": "c" },
    "humidity": { "value": 60.2, "unit": "%" },
    "light": { "value": 2048, "unit": "raw" }
  }
}
```

## 🔧 动手实践

### 任务1：理解已有代码

**ESP32 固件** ([`firmware/esp32_device/src/main.cpp`](E:/llm_embedded_project/firmware/esp32_device/src/main.cpp))：

- `setup()` — 初始化串口、LED、DHT 传感器
- `loop()` — 每5秒读取一次传感器 → 组装 JSON → 串口发送 → LED 闪烁指示

**Python 接收器** ([`agent/src/week1_data_collection/data_receiver.py`](E:/llm_embedded_project/agent/src/week1_data_collection/data_receiver.py))：

- `SensorDataReceiver.receive_data()` — 解析 JSON，存入缓冲区
- `SensorDataReceiver.flush_to_disk()` — 将缓冲区的数据写入文件

### 任务2：Wokwi 仿真运行 ESP32

VS Code 打开项目根目录 `E:\llm_embedded_project`，然后：

1. 按 `F1` → 输入 `Wokwi: Start Simulator` → 选择 `firmware/esp32_device`
2. 仿真启动后，你会看到 ESP32 + DHT22 + 光敏电阻的电路图
3. 点击 DHT22 传感器，可以手动调节温湿度值
4. 串口输出面板会显示 JSON 数据流

> 💡 **如果没有 Wokwi 授权**，可以先用 Python 端模拟串口数据测试

### 任务3：编写串口读取器

创建文件 [`agent/src/week1_data_collection/serial_reader.py`](E:/llm_embedded_project/agent/src/week1_data_collection/serial_reader.py)，实现从串口读取 ESP32 数据：

```python
"""
串口读取器 — 从 ESP32 串口读取传感器数据
"""

import serial
import json
import logging
import time
from data_receiver import SensorDataReceiver

logger = logging.getLogger(__name__)


class SerialReader:
    """ESP32 串口数据读取器"""

    def __init__(self, port: str = "COM3", baud: int = 115200, receiver: SensorDataReceiver = None):
        self.port = port
        self.baud = baud
        self.receiver = receiver or SensorDataReceiver()
        self.serial = None

    def connect(self) -> bool:
        """连接串口"""
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            logger.info(f"已连接串口 {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"串口连接失败: {e}")
            return False

    def read_loop(self, duration: int = 30):
        """持续读取数据"""
        if not self.serial:
            if not self.connect():
                return

        start = time.time()
        line_buffer = ""

        try:
            while time.time() - start < duration:
                if self.serial.in_waiting:
                    char = self.serial.read(1).decode('utf-8', errors='ignore')
                    if char == '\n':
                        if line_buffer.strip():
                            self.receiver.receive_data(line_buffer.strip())
                        line_buffer = ""
                    else:
                        line_buffer += char
                else:
                    time.sleep(0.01)
        finally:
            self.serial.close()
            self.receiver.flush_to_disk()
            logger.info("串口读取结束")
```

### 任务4：完整链路测试

在无法连接真实硬件时，可以用 Python 模拟串口数据来进行完整测试：

```python
# 模拟 ESP32 串口输出
from data_receiver import SensorDataReceiver
import time
import json
import random

def simulate_esp32_data():
    """模拟 ESP32 发送传感器数据"""
    receiver = SensorDataReceiver()
    
    mock_sensors = [
        {"temperature": 25.0, "humidity": 55.0, "light": 2000},
        {"temperature": 25.3, "humidity": 54.8, "light": 1800},
        {"temperature": 24.8, "humidity": 56.1, "light": 2100},
    ]
    
    for i, sensors in enumerate(mock_sensors):
        # 模拟 JSON 数据包（与 ESP32 格式一致）
        packet = json.dumps({
            "device_id": "esp32_001",
            "timestamp": i * 5000,
            "sensors": {
                "temperature": {"value": sensors["temperature"] + random.uniform(-0.5, 0.5), "unit": "c"},
                "humidity": {"value": sensors["humidity"] + random.uniform(-1, 1), "unit": "%"},
                "light": {"value": sensors["light"] + random.randint(-50, 50), "unit": "raw"},
            }
        })
        
        result = receiver.receive_data(packet)
        print(f"[{'✓' if result['status']=='ok' else '✗'}] {result}")
        time.sleep(0.5)
    
    count = receiver.flush_to_disk()
    print(f"\n✅ 已保存 {count} 条传感器数据到文件")

if __name__ == "__main__":
    simulate_esp32_data()
```

### 任务5：扩展练习（选做）

1. **添加新传感器** — 在 ESP32 固件中添加超声波测距传感器 (HC-SR04)
2. **数据校验** — 在 Python 端添加数据范围校验（温度超过 0-50°C 报警）
3. **实时可视化** — 用 matplotlib 实时绘制传感器曲线
4. **多设备支持** — 修改代码支持多个 ESP32 同时发送数据

## 📊 预期输出成果

运行完整链路后，你应该得到：

1. `data/sensor_data_20260514_*.json` — 包含多条传感器数据的 JSON 文件
2. 控制台输出类似：
```
INFO:__main__:收到数据: {'device_id': 'esp32_001', 'sensors': {'temperature': {...}}, ...}
INFO:__main__:已写入 3 条数据到 data/sensor_data_20260514_130841.json
```

## 🔗 与后续周的关联

| 后续周次 | 依赖第1周的内容 |
|---------|----------------|
| 第2周 任务调度 | 基于传感器数据触发不同的采集任务 |
| 第3周 通信上传 | 将采集的数据通过 MQTT 上传到服务器 |
| 第5周 异常检测 | 对采集的历史数据进行异常分析 |

## ✅ 第1周完成清单

- [ ] 理解 DHT11 温湿度传感器的工作原理
- [ ] 理解 ESP32 ADC 模拟信号采集
- [ ] 成功在 Wokwi 中运行 ESP32 固件仿真
- [ ] 理解 JSON 序列化/反序列化
- [ ] 运行 Python 数据接收器并看到数据文件生成
- [ ] 理解缓冲区写入文件的批量存储模式
- [ ] (选做) 添加至少一种新传感器
