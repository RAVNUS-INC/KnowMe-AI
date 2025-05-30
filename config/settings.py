from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MinIO 설정
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_access_key: str = "minio_admin"
    minio_secret_key: str = "helloworld1234"
    minio_secure: bool = False

    # MySQL 설정
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_root_password: str = "your_root_password"
    mysql_database: str = "knowme_db"
    mysql_user: str = "knowme_user"
    mysql_password: str = "hello"

    # RabbitMQ 설정
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_management_port: int = 15672
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "hello"

    # ChromaDB 설정
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # OpenAI 설정
    openai_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 설정 인스턴스 생성
settings = Settings()
