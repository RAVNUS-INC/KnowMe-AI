"""
RabbitMQ 기반 추천 시스템 클라이언트 예제

FastAPI 대신 순수 RabbitMQ 메시지를 통해 추천 요청을 보내는 클라이언트입니다.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import sys
import os

# 프로젝트 루트와 src 폴더를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

from task_queue.rabbitmq_client import RabbitMQClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RecommendationClient:
    """RabbitMQ 기반 추천 클라이언트"""

    def __init__(
        self, rabbitmq_host: str = "localhost", queue_name: str = "task_queue"
    ):
        self.rabbitmq_client = RabbitMQClient(host=rabbitmq_host, queue_name=queue_name)

    async def request_activity_recommendation(
        self,
        user_profile: Dict[str, Any],
        metadata_filters: Dict[str, Any] = None,
        n_results: int = 10,
    ) -> str:
        """대외활동 추천 요청"""
        request_id = f"activity_rec_{user_profile.get('user_id', 'unknown')}_{datetime.now().timestamp()}"

        message = {
            "task_type": "recommend_activities_with_metadata",
            "data": {
                "user_profile": user_profile,
                "metadata_filters": metadata_filters,
                "n_results": n_results,
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
        }

        await self.rabbitmq_client.send_message(message)
        logger.info(f"✅ 대외활동 추천 요청 전송 완료: {request_id}")
        return request_id

    async def request_job_recommendation(
        self,
        user_profile: Dict[str, Any],
        metadata_filters: Dict[str, Any] = None,
        n_results: int = 10,
    ) -> str:
        """채용공고 추천 요청"""
        request_id = f"job_rec_{user_profile.get('user_id', 'unknown')}_{datetime.now().timestamp()}"

        message = {
            "task_type": "recommend_jobs_with_metadata",
            "data": {
                "user_profile": user_profile,
                "metadata_filters": metadata_filters,
                "n_results": n_results,
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
        }

        await self.rabbitmq_client.send_message(message)
        logger.info(f"✅ 채용공고 추천 요청 전송 완료: {request_id}")
        return request_id

    async def request_embedding_generation(self, text: str, document_id: str) -> str:
        """임베딩 생성 요청"""
        request_id = f"embedding_{document_id}_{datetime.now().timestamp()}"

        message = {
            "task_type": "embedding_generation",
            "data": {"text": text, "document_id": document_id},
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
        }

        await self.rabbitmq_client.send_message(message)
        logger.info(f"✅ 임베딩 생성 요청 전송 완료: {request_id}")
        return request_id

    async def close(self):
        """클라이언트 연결 종료"""
        if hasattr(self.rabbitmq_client, "close"):
            await self.rabbitmq_client.close()


# 사용 예제 함수들
async def example_activity_recommendation():
    """대외활동 추천 예제"""
    client = RecommendationClient()

    # 사용자 프로필 정의
    user_profile = {
        "user_id": "student_123",
        "major": "컴퓨터공학",
        "interests": ["AI", "창업", "프로그래밍", "데이터사이언스"],
        "skills": ["Python", "React", "머신러닝", "데이터분석"],
        "experience_level": "중급",
        "preferred_location": "서울",
        "grade": 3,
    }

    # 메타데이터 필터 정의
    metadata_filters = {
        "category": "대외활동",
        "activityField": "창업",
        "activityDuration": {"min": 7, "max": 90},
        "location": "서울",
    }

    try:
        request_id = await client.request_activity_recommendation(
            user_profile=user_profile, metadata_filters=metadata_filters, n_results=5
        )
        logger.info(f"대외활동 추천 요청 ID: {request_id}")
    finally:
        await client.close()


async def example_job_recommendation():
    """채용공고 추천 예제"""
    client = RecommendationClient()

    # 사용자 프로필 정의
    user_profile = {
        "user_id": "jobseeker_456",
        "major": "컴퓨터공학",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS"],
        "desired_role": "백엔드 개발자",
        "experience_years": 2,
        "company_size_preference": "스타트업",
        "preferred_location": "서울",
    }

    # 메타데이터 필터 정의
    metadata_filters = {
        "requiredExperience": {"min": 0, "max": 3},
        "company": "스타트업",
    }

    try:
        request_id = await client.request_job_recommendation(
            user_profile=user_profile, metadata_filters=metadata_filters, n_results=5
        )
        logger.info(f"채용공고 추천 요청 ID: {request_id}")
    finally:
        await client.close()


async def example_multiple_requests():
    """여러 요청을 순차적으로 보내는 예제"""
    client = RecommendationClient()

    try:
        # 1. 임베딩 생성
        await client.request_embedding_generation(
            text="AI 스타트업에서 백엔드 개발자를 찾습니다",
            document_id="job_posting_001",
        )

        # 2. 대외활동 추천
        await client.request_activity_recommendation(
            user_profile={
                "user_id": "test_user",
                "major": "컴퓨터공학",
                "interests": ["AI", "프로그래밍"],
            }
        )

        # 3. 채용공고 추천
        await client.request_job_recommendation(
            user_profile={
                "user_id": "test_user",
                "desired_role": "AI 엔지니어",
                "skills": ["Python", "TensorFlow"],
            }
        )

        logger.info("✅ 모든 요청이 성공적으로 전송되었습니다")

    finally:
        await client.close()


if __name__ == "__main__":
    print("🚀 RabbitMQ 기반 추천 시스템 클라이언트 예제")
    print("=" * 50)

    # 예제 선택
    import sys

    if len(sys.argv) > 1:
        example_type = sys.argv[1]
    else:
        example_type = "activity"

    try:
        if example_type == "activity":
            print("대외활동 추천 예제 실행 중...")
            asyncio.run(example_activity_recommendation())
        elif example_type == "job":
            print("채용공고 추천 예제 실행 중...")
            asyncio.run(example_job_recommendation())
        elif example_type == "multiple":
            print("다중 요청 예제 실행 중...")
            asyncio.run(example_multiple_requests())
        else:
            print("사용법: python rabbitmq_client_example.py [activity|job|multiple]")
            print("기본값으로 대외활동 추천 예제를 실행합니다...")
            asyncio.run(example_activity_recommendation())

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다")
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {str(e)}")
