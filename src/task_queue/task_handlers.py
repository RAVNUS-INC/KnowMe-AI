"""
태스크 핸들러들

다양한 종류의 비동기 태스크를 처리하는 핸들러 함수들
"""

import logging
from typing import Dict, Any
from datetime import datetime

from services.personalized_ai_service import PersonalizedAIService

logger = logging.getLogger(__name__)


async def analyze_portfolio_task(data: Dict[str, Any]):
    """
    작업 큐에서 온 새로운 데이터 형식을 사용하는 포트폴리오 분석 태스크

    Args:
        data: {
            "analysisId": int,
            "taskType": "ANALYZE",
            "userId": int,
            "parameters": {
                "activities": [...],
                "educations": [...],
                "analysisId": int,
                "userId": int
            }
        }
    """
    try:
        # 작업 큐 형식에서 데이터 추출
        analysis_id = data.get("analysisId")
        user_id = data.get("userId")
        parameters = data.get("parameters", {})

        # parameters에서 실제 분석 데이터 추출
        activities = parameters.get("activities", [])
        educations = parameters.get("educations", [])

        # 추가 ID 확인 (parameters 내부에도 있을 수 있음)
        if not analysis_id:
            analysis_id = parameters.get("analysisId")
        if not user_id:
            user_id = parameters.get("userId")

        logger.info(f"포트폴리오 분석 시작: 분석 ID={analysis_id}, 사용자 ID={user_id}")

        # PersonalizedAIService 인스턴스 생성
        ai_service = PersonalizedAIService(test_mode=False)

        # 분석 데이터 구성
        analysis_data = {
            "activities": activities,
            "educations": educations,
            "userId": user_id,
            "analysisId": analysis_id,
        }

        # 분석 실행
        result = ai_service.analyze_portfolio_from_data(analysis_data)

        logger.info(f"포트폴리오 분석 완료: 분석 ID={analysis_id}")
        return result

    except Exception as e:
        logger.error(f"포트폴리오 분석 태스크 오류: {str(e)}")
        return {
            "success": False,
            "errorMessage": str(e),
            "taskType": "ANALYZE",
            "completedAt": datetime.now().isoformat(),
            "analysis_id": data.get("analysisId"),
            "user_id": data.get("userId"),
        }
