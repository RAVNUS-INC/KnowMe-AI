import io
import logging
from typing import Optional
import PyPDF2
import fitz  # PyMuPDF - 더 나은 텍스트 추출을 위해

from src.storage.minio_client import get_object

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """PDF에서 텍스트를 추출하는 클래스"""

    @staticmethod
    def extract_text_from_bytes(pdf_bytes: io.BytesIO) -> Optional[str]:
        """
        BytesIO 객체에서 PDF 텍스트 추출 (PyMuPDF 사용)
        """
        try:
            pdf_bytes.seek(0)
            doc = fitz.open(stream=pdf_bytes.read(), filetype="pdf")
            text = ""

            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
                text += "\n\n"  # 페이지 구분

            doc.close()
            return text.strip()

        except Exception as e:
            logger.error(f"PyMuPDF로 텍스트 추출 실패: {str(e)}")
            # PyPDF2로 fallback
            return PDFTextExtractor._extract_with_pypdf2(pdf_bytes)

    @staticmethod
    def _extract_with_pypdf2(pdf_bytes: io.BytesIO) -> Optional[str]:
        """
        PyPDF2를 사용한 fallback 텍스트 추출
        """
        try:
            pdf_bytes.seek(0)
            reader = PyPDF2.PdfReader(pdf_bytes)
            text = ""

            for page in reader.pages:
                text += page.extract_text()
                text += "\n\n"

            return text.strip()

        except Exception as e:
            logger.error(f"PyPDF2로 텍스트 추출 실패: {str(e)}")
            return None

    @staticmethod
    def extract_from_minio(bucket_name: str, object_name: str) -> Optional[str]:
        """
        MinIO에서 PDF를 가져와서 텍스트 추출
        """
        pdf_data = get_object(bucket_name, object_name)
        if pdf_data is None:
            logger.error(f"MinIO에서 PDF 다운로드 실패: {bucket_name}/{object_name}")
            return None

        return PDFTextExtractor.extract_text_from_bytes(pdf_data)
