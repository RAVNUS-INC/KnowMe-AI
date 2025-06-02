from fastapi import APIRouter
<<<<<<< HEAD

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
=======
from typing import List, Dict, Any

router = APIRouter()

@router.get("/documents", response_model=List[Dict[str, Any]])
async def get_documents() -> List[Dict[str, Any]]:
    """Retrieve all documents."""
    pass

@router.post("/documents", response_model=Dict[str, Any])
async def add_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new document."""
    pass

@router.get("/documents/{document_id}", response_model=Dict[str, Any])
async def get_document(document_id: str) -> Dict[str, Any]:
    """Retrieve a document by its ID."""
    pass

@router.delete("/documents/{document_id}", response_model=Dict[str, Any])
async def delete_document(document_id: str) -> Dict[str, Any]:
    """Delete a document by its ID."""
    pass

@router.put("/documents/{document_id}", response_model=Dict[str, Any])
async def update_document(document_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
    """Update a document by its ID."""
    pass
>>>>>>> 6f46e8d (feat: initialize langchain project)
