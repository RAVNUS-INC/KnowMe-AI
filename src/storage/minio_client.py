from minio import Minio
from minio.error import S3Error
import logging
import io
from typing import Optional

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


def get_object(bucket_name: str, object_name: str) -> Optional[io.BytesIO]:
    """
    MinIO에서 객체를 가져와서 BytesIO로 반환
    """
    try:
        response = client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return io.BytesIO(data)
    except S3Error as e:
        logger.error(f"객체 다운로드 실패 ({bucket_name}/{object_name}): {str(e)}")
        return None


def list_objects(bucket_name: str, prefix: str = "") -> list:
    """
    버킷의 객체 목록을 반환
    """
    try:
        objects = client.list_objects(bucket_name, prefix=prefix)
        return [obj.object_name for obj in objects]
    except S3Error as e:
        logger.error(f"객체 목록 조회 실패 ({bucket_name}): {str(e)}")
        return []


def object_exists(bucket_name: str, object_name: str) -> bool:
    """
    객체가 존재하는지 확인
    """
    try:
        client.stat_object(bucket_name, object_name)
        return True
    except S3Error:
        return False


# 기본 버킷들 생성
DEFAULT_BUCKETS = ["documents", "embeddings", "temp"]


def initialize_buckets():
    """기본 버킷들을 초기화"""
    for bucket in DEFAULT_BUCKETS:
        ensure_bucket_exists(bucket)
