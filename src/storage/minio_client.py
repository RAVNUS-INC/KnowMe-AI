from minio import Minio
from minio.error import S3Error
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

client = Minio(
    f"{settings.minio_host}:{settings.minio_port}",
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def get_minio_client() -> Minio:
    """
    Returns the Minio client instance.
    """
    return client


def ensure_bucket_exists(bucket_name: str) -> bool:
    """
    버킷이 존재하는지 확인하고 없으면 생성
    """
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"버킷 '{bucket_name}'이 생성되었습니다.")
        return True
    except S3Error as e:
        logger.error(f"버킷 확인/생성 실패: {str(e)}")
        return False


# 기본 버킷들 생성
DEFAULT_BUCKETS = ["documents", "embeddings", "temp"]


def initialize_buckets():
    """기본 버킷들을 초기화"""
    for bucket in DEFAULT_BUCKETS:
        ensure_bucket_exists(bucket)
