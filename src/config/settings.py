from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # OpenAI API 설정
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"

    # ChromaDB 설정
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # MySQL 설정
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_root_password: str = os.getenv("MYSQL_ROOT_PASSWORD")
    mysql_database: str = "knowme_Db"
    mysql_user: str = os.getenv("MYSQL_USER")
    mysql_password: str = os.getenv("MYSQL_PASSWORD")

    # RabbitMQ 설정
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_management_port: int = 15672
    rabbitmq_user: str = os.getenv("RABBITMQ_USER")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD")

    # MinIO 설정
    minio_host: str = "localhost"
    minio_api_port: int = 9000
    minio_console_port: int = 9001
    minio_root_user: str = os.getenv("MINIO_ROOT_USER")
    minio_root_password: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 설정 인스턴스 생성
settings = Settings()
