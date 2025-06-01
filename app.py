"""
FastAPI 애플리케이션

PDF 텍스트 추출 및 문서 관리를 위한 API 서버
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.api.routes import router
from src.storage.minio_client import initialize_buckets
from config.settings import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 KnowMe AI API 시작")

    # MinIO 버킷 초기화
    try:
        initialize_buckets()
        logger.info("✅ MinIO 버킷 초기화 완료")
    except Exception as e:
        logger.error(f"❌ MinIO 버킷 초기화 실패: {e}")

    yield

    # 종료 시 실행
    logger.info("👋 KnowMe AI API 종료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="KnowMe AI API",
    description="Document processing and PDF text extraction API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
app.include_router(router, prefix="/api/v1")


# 루트 엔드포인트
@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "KnowMe AI API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": "/api/v1",
    }


# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 에러 핸들러"""
    logger.error(f"예상치 못한 오류: {exc}")
    return HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=getattr(settings, "api_host", "0.0.0.0"),
        port=getattr(settings, "api_port", 8000),
        reload=True,
        log_level="info",
    )
