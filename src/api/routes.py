from fastapi import APIRouter

from .pdf_routes import router as pdf_router
from .document_routes import router as document_router

# 메인 라우터
router = APIRouter()

# 서브 라우터들을 포함
router.include_router(pdf_router)
router.include_router(document_router)


# 헬스체크 엔드포인트
@router.get("/health")
async def health_check():
    """
    API 상태를 확인합니다.
    """
    return {"status": "healthy", "message": "KnowMe AI API is running"}


# API 정보 엔드포인트
@router.get("/info")
async def api_info():
    """
    API 정보를 반환합니다.
    """
    return {
        "name": "KnowMe AI API",
        "version": "1.0.0",
        "description": "Document processing and text extraction API",
        "endpoints": {
            "documents": "Document management",
            "pdfs": "PDF text extraction and processing",
        },
    }
