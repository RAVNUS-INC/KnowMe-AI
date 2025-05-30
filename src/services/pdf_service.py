from typing import Optional, List, Dict, Any
import logging
from fastapi import HTTPException
from concurrent.futures import ThreadPoolExecutor
import asyncio

from src.utils.pdf_extractor import PDFTextExtractor
from src.storage.minio_client import list_objects, object_exists
from config.settings import settings

logger = logging.getLogger(__name__)


class PDFProcessingService:
    """PDF 처리를 위한 서비스 클래스"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_pdf_from_minio(
        self, object_name: str, bucket_name: str = None
    ) -> Dict[str, Any]:
        """
        MinIO의 PDF 파일을 처리하여 텍스트 추출
        """
        bucket_name = bucket_name or settings.minio_default_bucket

        try:
            # 객체 존재 확인
            if not object_exists(bucket_name, object_name):
                raise HTTPException(
                    status_code=404,
                    detail=f"PDF 파일을 찾을 수 없습니다: {object_name}",
                )

            # 비동기적으로 텍스트 추출 (CPU 집약적 작업이므로 별도 스레드에서 실행)
            loop = asyncio.get_event_loop()
            extracted_text = await loop.run_in_executor(
                self.executor,
                PDFTextExtractor.extract_from_minio,
                bucket_name,
                object_name,
            )

            if extracted_text is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"PDF 텍스트 추출에 실패했습니다: {object_name}",
                )

            return {
                "object_name": object_name,
                "bucket_name": bucket_name,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "page_count": extracted_text.count("\n\n") + 1,  # 대략적인 페이지 수
                "status": "success",
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PDF 처리 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF 처리 실패: {str(e)}")

    async def get_all_pdf_files(
        self, bucket_name: str = None, prefix: str = ""
    ) -> List[str]:
        """
        MinIO 버킷의 모든 PDF 파일 목록 반환
        """
        bucket_name = bucket_name or settings.minio_default_bucket

        try:
            loop = asyncio.get_event_loop()
            all_objects = await loop.run_in_executor(
                self.executor, list_objects, bucket_name, prefix
            )

            pdf_files = [obj for obj in all_objects if obj.lower().endswith(".pdf")]
            return pdf_files

        except Exception as e:
            logger.error(f"PDF 파일 목록 조회 실패: {str(e)}")
            return []

    async def batch_process_pdfs(
        self, object_names: List[str], bucket_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        여러 PDF 파일을 배치로 처리
        """
        bucket_name = bucket_name or settings.minio_default_bucket
        results = []

        for object_name in object_names:
            try:
                result = await self.process_pdf_from_minio(object_name, bucket_name)
                results.append(result)
            except HTTPException as e:
                results.append(
                    {
                        "object_name": object_name,
                        "bucket_name": bucket_name,
                        "status": "error",
                        "error": str(e.detail),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "object_name": object_name,
                        "bucket_name": bucket_name,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results

    async def check_pdf_exists(self, object_name: str, bucket_name: str = None) -> bool:
        """
        PDF 파일이 존재하는지 확인
        """
        bucket_name = bucket_name or settings.minio_default_bucket

        try:
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(
                self.executor, object_exists, bucket_name, object_name
            )
            return exists
        except Exception as e:
            logger.error(f"PDF 존재 확인 실패: {str(e)}")
            return False

        try:
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(
                self.executor, object_exists, bucket_name, object_name
            )
            return exists
        except Exception as e:
            logger.error(f"PDF 존재 확인 실패: {str(e)}")
            return False


# 전역 인스턴스
pdf_service = PDFProcessingService()
