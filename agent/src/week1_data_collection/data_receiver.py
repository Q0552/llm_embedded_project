"""
第1周：设备数据采集 - 数据接收模块

功能：接收来自 ESP32/STM32 的传感器数据，进行初步解析和存储
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensorDataReceiver:
    """传感器数据接收器"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.buffer: list = []

    def receive_data(self, raw_data: str) -> Dict[str, Any]:
        """
        接收并解析传感器数据
        支持 JSON 格式: {"sensor": "temperature", "value": 25.6, "unit": "c"}
        """
        try:
            data = json.loads(raw_data)
            data["timestamp"] = datetime.now().isoformat()
            self.buffer.append(data)
            logger.info(f"收到数据: {data}")
            return {"status": "ok", "data": data}
        except json.JSONDecodeError as e:
            logger.error(f"数据解析失败: {e}")
            return {"status": "error", "message": str(e)}

    def flush_to_disk(self) -> int:
        """将缓冲区数据写入磁盘"""
        if not self.buffer:
            return 0

        filename = f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.buffer, f, ensure_ascii=False, indent=2)

        count = len(self.buffer)
        self.buffer.clear()
        logger.info(f"已写入 {count} 条数据到 {filepath}")
        return count


def main():
    """演示运行"""
    receiver = SensorDataReceiver()

    # 模拟接收数据
    test_data = [
        '{"sensor": "temperature", "value": 25.6, "unit": "c"}',
        '{"sensor": "humidity", "value": 60.2, "unit": "%"}',
        '{"sensor": "pressure", "value": 1013.25, "unit": "hPa"}',
    ]

    for data in test_data:
        result = receiver.receive_data(data)
        time.sleep(0.1)

    receiver.flush_to_disk()
    logger.info("数据采集演示完成")


if __name__ == "__main__":
    main()
