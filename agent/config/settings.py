"""
项目配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM 配置
    llm_api_key: str = "your_api_key_here"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # MQTT 配置
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "llm_embedded"

    # 路径配置
    data_dir: str = "./data"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
