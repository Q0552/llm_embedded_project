# 🤖 LLM + 嵌入式融合项目

> **目标：** 以找工作为导向，边做项目边学习大模型与嵌入式开发的融合技术

## 📋 12周学习计划

| 周次 | 主题 | 嵌入式端 | 智能体端 |
|------|------|---------|---------|
| 第1周 | 🔌 **设备采集** | ESP32/STM32 传感器数据采集 | Python 数据接收与初步处理 |
| 第2周 | ⏱ **任务调度** | FreeRTOS 多任务调度 | 智能体任务队列管理 |
| 第3周 | 📡 **通信上传** | WiFi/MQTT 数据上传 | 云端API数据接收 |
| 第4周 | 🖥 **边缘端接收** | 边缘计算节点数据处理 | 边缘推理服务 |
| 第5周 | 🔍 **规则异常检测** | 本地异常信号检测 | 统计规则异常分析 |
| 第6周 | 🧠 **智能体诊断** | 数据采集与反馈 | LLM驱动的故障诊断 |
| 第7周 | 🔧 **智能体工具调用** | 固件OTA更新接口 | Function Calling 工具链 |
| 第8周 | 🔄 **控制闭环** | 执行器控制逻辑 | 智能体决策→设备控制 |
| 第9周 | 📊 **自动报告** | 设备状态记录 | LLM生成分析报告 |
| 第10周 | ⚡ **系统稳定性** | WDT/错误恢复 | 系统监控与自愈 |
| 第11周 | 📝 **项目文档和演示** | 硬件Demo搭建 | 项目文档与演示视频 |
| 第12周 | 🎯 **简历和面试** | 项目经验梳理 | 面试题库与模拟 |

## 🛠 技术栈

- **芯片平台：** ESP32 (ESP-IDF) / STM32 (STM32CubeIDE)
- **嵌入式框架：** PlatformIO
- **智能体框架：** LangChain / OpenAI API / Transformers
- **语言：** Python 3.10+ / C / C++
- **仿真：** Wokwi
- **版本控制：** Git + GitHub

## 📁 项目结构

```
E:\llm_embedded_project\
├── firmware\              # 嵌入式固件代码
│   ├── esp32_device\      # ESP32 项目 (PlatformIO)
│   ├── stm32_device\      # STM32 项目 (STM32CubeIDE)
│   └── components\        # 共用组件
├── agent\                 # 智能体 Python 项目
│   ├── src\               # 源代码 (按周划分)
│   │   ├── week1_data_collection\
│   │   ├── week2_task_scheduler\
│   │   ├── week3_cloud_upload\
│   │   ├── week4_edge_receive\
│   │   ├── week5_anomaly_detection\
│   │   ├── week6_agent_diagnosis\
│   │   ├── week7_tool_calling\
│   │   ├── week8_control_loop\
│   │   ├── week9_auto_report\
│   │   └── week10_stability\
│   ├── tests\             # 单元测试
│   └── config\            # 配置文件
├── docs\                  # 项目文档
├── tools\                 # 辅助工具脚本
├── .wokwi\                # Wokwi 仿真配置
├── .gitignore
├── requirements.txt       # Python 依赖
└── README.md              # 本文件
```

## 🚀 快速开始

```bash
# 1. 激活 Python 环境
conda activate llm_embedded

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy agent\config\.env.example agent\config\.env
# 编辑 .env 填入 API Key 等信息

# 4. 运行测试
cd agent && python -m pytest tests/
```

## 📌 环境安装状态

- [x] VS Code (代码编辑器)
- [x] Git 2.53.0 (版本控制)
- [x] Anaconda + Python 3.10 (llm_embedded 环境)
- [x] VS Code 扩展：Python, PlatformIO, ESP-IDF, Wokwi, C/C++
- [ ] ESP-IDF 工具链 (待安装)
- [ ] GitHub 仓库 (待配置)
