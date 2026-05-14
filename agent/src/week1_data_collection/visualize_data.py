"""
数据可视化 — 将采集的传感器数据绘制成图表

读取 data/ 目录下的传感器数据文件，绘制温湿度变化曲线
"""

import json
import logging
from pathlib import Path
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use("TkAgg")
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_latest_data(data_dir: str = "./data") -> list:
    """加载最新的传感器数据文件"""
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return []

    json_files = sorted(data_path.glob("sensor_data_*.json"))
    if not json_files:
        logger.error("未找到传感器数据文件")
        return []

    latest = json_files[-1]
    logger.info(f"加载数据文件: {latest}")

    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def visualize(data: list):
    """绘制传感器数据图表"""
    if not data:
        logger.warning("没有数据可可视化")
        return

    if not HAS_MATPLOTLIB:
        logger.warning("需要安装 matplotlib: pip install matplotlib")
        return

    # 提取数据
    timestamps = []
    temperatures = []
    humidities = []
    lights = []

    for i, record in enumerate(data):
        timestamps.append(i)
        sensors = record.get("sensors", {})

        if "temperature" in sensors:
            temperatures.append(sensors["temperature"]["value"])
        if "humidity" in sensors:
            humidities.append(sensors["humidity"]["value"])
        if "light" in sensors:
            lights.append(sensors["light"]["value"])

    # 创建图表
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("ESP32 传感器数据", fontsize=14)

    # 温度
    if temperatures:
        axes[0].plot(timestamps, temperatures, "r-o", markersize=4)
        axes[0].set_ylabel("温度 (°C)")
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=25, color="gray", linestyle="--", alpha=0.5)

    # 湿度
    if humidities:
        axes[1].plot(timestamps, humidities, "b-o", markersize=4)
        axes[1].set_ylabel("湿度 (%)")
        axes[1].grid(True, alpha=0.3)

    # 光照
    if lights:
        axes[2].plot(timestamps, lights, "y-o", markersize=4)
        axes[2].set_ylabel("光照 (raw)")
        axes[2].set_xlabel("采样点")
        axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def main():
    data = load_latest_data()
    if data:
        print(f"共加载 {len(data)} 条记录")
        visualize(data)


if __name__ == "__main__":
    main()
