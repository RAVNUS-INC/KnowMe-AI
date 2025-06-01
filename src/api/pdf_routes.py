from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from src.services.pdf_service import pdf_service

router = APIRouter(prefix="/pdfs", tags=["PDF Processing"])


# 응답 모델들
class PDFTextResponse(BaseModel):
    object_name: str
    bucket_name: str
    extracted_text: str
    text_length: int
    page_count: Optional[int] = None
    status: str = "success"


class PDFListResponse(BaseModel):
    files: List[str]
    total_count: int
    bucket_name: str


class BatchPDFResponse(BaseModel):
    results: List[PDFTextResponse]
    success_count: int
    error_count: int


class ErrorResponse(BaseModel):
    error: str
    detail: str
    object_name: Optional[str] = None


# 요청 모델들
class PDFProcessRequest(BaseModel):
    object_name: str
    bucket_name: Optional[str] = None


class BatchPDFProcessRequest(BaseModel):
    object_names: List[str]
    bucket_name: Optional[str] = None


# PDF API Routes
@router.get("/", response_model=PDFListResponse)
async def list_pdfs(
    bucket_name: Optional[str] = Query(None, description="버킷 이름"),
    prefix: str = Query("", description="파일 이름 접두사 필터"),
) -> PDFListResponse:
    """
    PDF 파일 목록을 조회합니다.
    """
    try:
        files = await pdf_service.get_all_pdf_files(
            bucket_name=bucket_name, prefix=prefix
        )
        actual_bucket = bucket_name or "default"

        return PDFListResponse(
            files=files, total_count=len(files), bucket_name=actual_bucket
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 목록 조회 실패: {str(e)}")


@router.get("/{object_name}/text", response_model=PDFTextResponse)
async def extract_pdf_text(
    object_name: str, bucket_name: Optional[str] = Query(None, description="버킷 이름")
) -> PDFTextResponse:
    """
    특정 PDF 파일의 텍스트를 추출합니다.
    """
    try:
        result = await pdf_service.process_pdf_from_minio(
            object_name=object_name, bucket_name=bucket_name
        )
        return PDFTextResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 텍스트 추출 실패: {str(e)}")


@router.post("/extract", response_model=PDFTextResponse)
async def extract_pdf_by_request(request: PDFProcessRequest) -> PDFTextResponse:
    """
    요청 본문으로 PDF 텍스트를 추출합니다.
    """
    try:
        result = await pdf_service.process_pdf_from_minio(
            object_name=request.object_name, bucket_name=request.bucket_name
        )
        return PDFTextResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 텍스트 추출 실패: {str(e)}")


@router.post("/batch-extract", response_model=BatchPDFResponse)
async def batch_extract_pdf_text(request: BatchPDFProcessRequest) -> BatchPDFResponse:
    """
    여러 PDF 파일의 텍스트를 배치로 추출합니다.
    """
    try:
        results = await pdf_service.batch_process_pdfs(
            object_names=request.object_names, bucket_name=request.bucket_name
        )

        success_results = [r for r in results if r.get("status") == "success"]
        error_results = [r for r in results if r.get("status") != "success"]

        return BatchPDFResponse(
            results=[PDFTextResponse(**r) for r in success_results],
            success_count=len(success_results),
            error_count=len(error_results),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 PDF 처리 실패: {str(e)}")


@router.get("/{object_name}/exists")
async def check_pdf_exists(
    object_name: str, bucket_name: Optional[str] = Query(None, description="버킷 이름")
) -> dict:
    """
    PDF 파일이 존재하는지 확인합니다.
    """
    try:
        exists = await pdf_service.check_pdf_exists(
            object_name=object_name, bucket_name=bucket_name
        )
        return {
            "object_name": object_name,
            "exists": exists,
            "bucket_name": bucket_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 존재 확인 실패: {str(e)}")
