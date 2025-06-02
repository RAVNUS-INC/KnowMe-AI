"""
RabbitMQ 기반 추천 시스템 테스트 클라이언트

FastAPI 없이 RabbitMQ만을 사용하여 추천 요청을 보내고 결과를 받는 테스트 스크립트입니다.
"""

import json
import logging
from datetime import datetime
import sys
import os

# 프로젝트 루트와 src 폴더를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

from src.task_queue.rabbitmq_client import RabbitMQClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RecommendationTestClient:
    """RabbitMQ 기반 추천 테스트 클라이언트"""

    def __init__(
        self, rabbitmq_host: str = "localhost", queue_name: str = "task_queue"
    ):
        self.rabbitmq_client = RabbitMQClient(host=rabbitmq_host, queue_name=queue_name)

    def test_activity_recommendation(self):
        """대외활동 추천 테스트"""
        logger.info("=== 대외활동 추천 테스트 시작 ===")

        # 테스트 데이터
        user_profile = {
            "user_id": "student123",
            "major": "컴퓨터공학",
            "interests": ["AI", "창업", "프로그래밍"],
            "skills": ["Python", "React", "머신러닝"],
            "experience_level": "중급",
            "preferred_location": "서울",
        }

        metadata_filters = {
            "category": "대외활동",
            "activityField": "창업",
            "activityDuration": {"min": 7, "max": 90},
            "location": "서울",
        }

        message = {
            "task_type": "recommend_activities_with_metadata",
            "data": {
                "user_profile": user_profile,
                "metadata_filters": metadata_filters,
                "n_results": 5,
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": f"activity_test_{datetime.now().timestamp()}",
        }

        try:
            self.rabbitmq_client.publish_json(message)
            logger.info("✅ 대외활동 추천 요청이 RabbitMQ에 성공적으로 전송되었습니다")
            logger.info(
                f"요청 데이터: {json.dumps(message, ensure_ascii=False, indent=2)}"
            )
        except Exception as e:
            logger.error(f"❌ 대외활동 추천 요청 실패: {str(e)}")

    def test_job_recommendation(self):
        """채용공고 추천 테스트"""
        logger.info("=== 채용공고 추천 테스트 시작 ===")

        # 테스트 데이터
        user_profile = {
            "user_id": "jobseeker456",
            "major": "컴퓨터공학",
            "skills": ["Python", "Django", "PostgreSQL", "Docker"],
            "desired_role": "백엔드 개발자",
            "experience_years": 2,
            "company_size_preference": "스타트업",
        }

        metadata_filters = {
            "requiredExperience": {"min": 0, "max": 3},
            "company": "스타트업",
        }

        message = {
            "task_type": "recommend_jobs_with_metadata",
            "data": {
                "user_profile": user_profile,
                "metadata_filters": metadata_filters,
                "n_results": 5,
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": f"job_test_{datetime.now().timestamp()}",
        }

        try:
            self.rabbitmq_client.publish_json(message)
            logger.info("✅ 채용공고 추천 요청이 RabbitMQ에 성공적으로 전송되었습니다")
            logger.info(
                f"요청 데이터: {json.dumps(message, ensure_ascii=False, indent=2)}"
            )
        except Exception as e:
            logger.error(f"❌ 채용공고 추천 요청 실패: {str(e)}")

    def test_basic_activity_recommendation(self):
        """기본 대외활동 추천 테스트 (기존 기능)"""
        logger.info("=== 기본 대외활동 추천 테스트 시작 ===")

        message = {
            "task_type": "recommend_activity",
            "data": {
                "user_preferences": {
                    "interests": ["AI", "프로그래밍"],
                    "experience_level": "초급",
                }
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": f"basic_activity_test_{datetime.now().timestamp()}",
        }

        try:
            self.rabbitmq_client.publish_json(message)
            logger.info(
                "✅ 기본 대외활동 추천 요청이 RabbitMQ에 성공적으로 전송되었습니다"
            )
        except Exception as e:
            logger.error(f"❌ 기본 대외활동 추천 요청 실패: {str(e)}")

    def test_embedding_generation(self):
        """임베딩 생성 테스트"""
        logger.info("=== 임베딩 생성 테스트 시작 ===")

        message = {
            "task_type": "embedding_generation",
            "data": {
                "text": "AI와 머신러닝을 활용한 창업 프로그램 참가자 모집",
                "document_id": "test_doc_123",
            },
            "timestamp": datetime.now().isoformat(),
            "request_id": f"embedding_test_{datetime.now().timestamp()}",
        }

        try:
            self.rabbitmq_client.publish_json(message)
            logger.info("✅ 임베딩 생성 요청이 RabbitMQ에 성공적으로 전송되었습니다")
        except Exception as e:
            logger.error(f"❌ 임베딩 생성 요청 실패: {str(e)}")

    def close(self):
        """클라이언트 연결 종료"""
        if hasattr(self.rabbitmq_client, "close"):
            self.rabbitmq_client.close()


def main():
    """메인 테스트 함수"""
    logger.info("🚀 RabbitMQ 기반 추천 시스템 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now()}")
    logger.info("=" * 60)

    client = RecommendationTestClient()

    try:
        # 1. 기본 기능 테스트
        client.test_embedding_generation()

        client.test_basic_activity_recommendation()

        # 2. 새로운 메타데이터 기반 추천 테스트
        client.test_activity_recommendation()

        client.test_job_recommendation()

        logger.info("=" * 60)
        logger.info("✅ 모든 테스트 요청이 RabbitMQ에 성공적으로 전송되었습니다")
        logger.info(
            "💡 실제 처리 결과를 확인하려면 워커 프로세스(main.py)의 로그를 확인하세요"
        )

    except Exception as e:
        logger.error(f"❌ 테스트 실패: {str(e)}")
    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("테스트가 사용자에 의해 중단되었습니다")
    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {str(e)}")
