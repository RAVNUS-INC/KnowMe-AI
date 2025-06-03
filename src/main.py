"""
메인 애플리케이션

RabbitMQ에서 메시지를 받아 비동기 태스크를 처리하는 메인 애플리케이션
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from task_queue.rabbitmq_client import RabbitMQClient
from task_queue.task_manager import TaskManager
from task_queue.task_handlers import (
    analyze_portfolio_task,
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MessageProcessor:
    """메시지 처리기 클래스"""

    def __init__(self, rabbitmq_host: str = "localhost"):
        self.rabbitmq_client = RabbitMQClient(host=rabbitmq_host)
        self.task_manager = TaskManager(rabbitmq_client=self.rabbitmq_client)
        self.is_running = False

        # 태스크 핸들러 등록
        self._register_handlers()

    def _register_handlers(self):
        """태스크 핸들러들을 등록"""
        self.task_manager.register_handler(
            "ANALYZE",
            analyze_portfolio_task,
        )

    async def start_processing(self):
        """메시지 처리 시작"""
        logger.info("메시지 처리기 시작")
        self.is_running = True

        try:
            # RabbitMQ에서 메시지를 비동기로 소비
            await self.rabbitmq_client.async_consume(self.task_manager.process_message)
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {str(e)}")
        finally:
            self.stop_processing()

    def stop_processing(self):
        """메시지 처리 중지"""
        logger.info("메시지 처리기 중지")
        self.is_running = False
        self.rabbitmq_client.close()

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        return {
            "is_running": self.is_running,
            "running_tasks": self.task_manager.get_running_tasks(),
        }


async def main():
    """메인 함수"""
    # 메시지 처리기 생성
    processor = MessageProcessor()

    # 신호 처리 함수
    def signal_handler(signum, frame):
        logger.info(f"신호 수신: {signum}")
        processor.stop_processing()
        sys.exit(0)

    # 신호 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 상태 모니터링 태스크
    async def status_monitor():
        while processor.is_running:
            status = processor.get_status()
            logger.info(
                f"현재 상태 - 실행 중: {status['is_running']}, "
                f"실행 중인 태스크 수: {len(status['running_tasks'])}"
            )
            await asyncio.sleep(30)  # 30초마다 상태 출력

    # 메시지 처리 시작
    try:
        # 상태 모니터링과 메시지 처리를 동시에 실행
        await asyncio.gather(processor.start_processing(), status_monitor())
    except KeyboardInterrupt:
        logger.info("사용자에 의한 중단")
    except Exception as e:
        logger.error(f"애플리케이션 오류: {str(e)}")
    finally:
        processor.stop_processing()


# 메시지 전송 테스트 함수들
def send_test_messages():
    """테스트 메시지 전송"""
    client = RabbitMQClient()

    # 문서 처리 태스크
    client.publish_json(
        {
            "task_type": "document_processing",
            "document_id": "doc_001",
            "file_path": "test_document.txt",
        }
    )

    # 임베딩 생성 태스크
    client.publish_json(
        {
            "task_type": "embedding_generation",
            "document_id": "doc_001",
            "text": "이것은 테스트 문서입니다.",
        }
    )

    # 파일 업로드 태스크
    client.publish_json(
        {
            "task_type": "file_upload",
            "local_path": "test_file.txt",
            "bucket_name": "documents",
            "object_name": "test_file.txt",
        }
    )

    # 알림 태스크
    client.publish_json(
        {
            "task_type": "notification",
            "message": "문서 처리가 완료되었습니다.",
            "recipient": "user@example.com",
            "type": "success",
        }
    )

    client.close()
    logger.info("테스트 메시지 전송 완료")


if __name__ == "__main__":
    # 명령행 인수에 따라 실행 모드 결정
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        send_test_messages()
    else:
        asyncio.run(main())
