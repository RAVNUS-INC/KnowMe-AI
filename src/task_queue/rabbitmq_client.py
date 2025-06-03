"""
RabbitMQ 클라이언트 구현

이 파일은 메시지 큐잉을 위한 RabbitMQ 클라이언트 구현을 포함합니다.
메시지를 게시하고 소비하는 메서드를 정의합니다.
"""

import pika
import logging
import asyncio
import json
from typing import Callable, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from config.settings import settings

# 로깅 설정
logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ 클라이언트 클래스"""

    def __init__(
        self,
        host: str = "localhost",
        work_queue: str = "ai.work.queue",
        result_queue: str = "ai.result.queue",
    ):
        """
        RabbitMQ 클라이언트 초기화

        Args:
            host: RabbitMQ 서버 호스트
            work_queue: 작업 요청을 받을 큐 이름
            result_queue: 결과를 보낼 큐 이름
        """
        self.host = host
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.connection = None
        self.channel = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._connect()

    def _connect(self):
        """RabbitMQ 서버에 연결"""
        try:
            # 인증 정보를 포함한 연결 파라미터 설정
            credentials = pika.PlainCredentials(
                username=settings.rabbitmq_user, password=settings.rabbitmq_password
            )
            parameters = pika.ConnectionParameters(
                host=self.host, port=settings.rabbitmq_port, credentials=credentials
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # 작업 큐와 결과 큐 선언
            self.channel.queue_declare(queue=self.work_queue, durable=True)
            self.channel.queue_declare(queue=self.result_queue, durable=True)

            logger.info(
                f"RabbitMQ에 연결되었습니다. 작업 큐: {self.work_queue}, 결과 큐: {self.result_queue}"
            )
        except Exception as e:
            logger.error(f"RabbitMQ 연결 실패: {str(e)}")
            raise

    def publish(self, message: str, queue_name: Optional[str] = None):
        """메시지를 큐에 게시"""
        try:
            target_queue = queue_name or self.result_queue
            self.channel.basic_publish(
                exchange="",
                routing_key=target_queue,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 메시지 지속성 설정
                ),
            )
            logger.info(f"메시지가 큐에 게시되었습니다: {message} -> {target_queue}")
        except Exception as e:
            logger.error(f"메시지 게시 실패: {str(e)}")

    def publish_json(self, data: Dict[str, Any], queue_name: Optional[str] = None):
        """JSON 데이터를 큐에 게시"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            self.publish(message, queue_name)
        except Exception as e:
            logger.error(f"JSON 메시지 게시 실패: {str(e)}")

    def publish_result(self, result_data: Dict[str, Any]):
        """결과를 결과 큐에 게시"""
        self.publish_json(result_data, self.result_queue)

    def publish_to_work_queue(self, work_data: Dict[str, Any]):
        """작업 요청을 작업 큐에 게시"""
        self.publish_json(work_data, self.work_queue)

    async def async_consume_work_queue(self, async_callback: Callable):
        """작업 큐에서 비동기로 메시지를 소비"""

        def callback_wrapper(ch, method, properties, body):
            try:
                # 메시지를 JSON으로 파싱 시도
                try:
                    data = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    data = body.decode("utf-8")

                # 비동기 태스크 생성
                asyncio.create_task(async_callback(data))
                logger.info(f"작업 큐에서 비동기 태스크가 생성되었습니다: {data}")

            except Exception as e:
                logger.error(f"작업 큐 메시지 처리 중 오류 발생: {str(e)}")

        try:
            self.channel.basic_consume(
                queue=self.work_queue,
                on_message_callback=callback_wrapper,
                auto_ack=True,
            )
            logger.info(
                f"작업 큐({self.work_queue})에서 비동기 메시지 소비를 시작합니다."
            )

            # 논블로킹 방식으로 메시지 처리
            while True:
                self.connection.process_data_events(time_limit=1)
                await asyncio.sleep(0.1)  # 다른 코루틴에게 제어권 양보

        except Exception as e:
            logger.error(f"작업 큐 비동기 메시지 소비 실패: {str(e)}")

    async def async_consume(self, async_callback: Callable):
        """비동기로 큐에서 메시지를 소비 (기존 호환성 유지)"""
        await self.async_consume_work_queue(async_callback)

    def consume_work_queue(self, callback):
        """작업 큐에서 메시지를 소비 (동기 방식)"""
        try:
            self.channel.basic_consume(
                queue=self.work_queue, on_message_callback=callback, auto_ack=True
            )
            logger.info(f"작업 큐({self.work_queue})에서 메시지 소비를 시작합니다.")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"작업 큐 메시지 소비 실패: {str(e)}")

    def consume(self, callback):
        """큐에서 메시지를 소비 (기존 동기 방식, 호환성 유지)"""
        self.consume_work_queue(callback)

    def close(self):
        """RabbitMQ 연결 종료"""
        if self.connection:
            self.connection.close()
            logger.info("RabbitMQ 연결이 종료되었습니다.")
        if self.executor:
            self.executor.shutdown(wait=True)
