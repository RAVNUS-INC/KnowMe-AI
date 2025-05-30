"""
RabbitMQ 클라이언트 구현

이 파일은 메시지 큐잉을 위한 RabbitMQ 클라이언트 구현을 포함합니다.
메시지를 게시하고 소비하는 메서드를 정의합니다.
"""

import pika
import logging
import asyncio
import json
from typing import Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# 로깅 설정
logger = logging.getLogger(__name__)

class RabbitMQClient:
    """RabbitMQ 클라이언트 클래스"""

    def __init__(self, host: str = 'localhost', queue_name: str = 'default'):
        """
        RabbitMQ 클라이언트 초기화
        
        Args:
            host: RabbitMQ 서버 호스트
            queue_name: 사용할 큐 이름
        """
        self.host = host
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._connect()

    def _connect(self):
        """RabbitMQ 서버에 연결"""
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            logger.info(f"RabbitMQ에 연결되었습니다. 큐: {self.queue_name}")
        except Exception as e:
            logger.error(f"RabbitMQ 연결 실패: {str(e)}")
            raise

    def publish(self, message: str):
        """메시지를 큐에 게시"""
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 메시지 지속성 설정
                )
            )
            logger.info(f"메시지가 큐에 게시되었습니다: {message}")
        except Exception as e:
            logger.error(f"메시지 게시 실패: {str(e)}")

    def publish_json(self, data: Dict[str, Any]):
        """JSON 데이터를 큐에 게시"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            self.publish(message)
        except Exception as e:
            logger.error(f"JSON 메시지 게시 실패: {str(e)}")

    async def async_consume(self, async_callback: Callable):
        """비동기로 큐에서 메시지를 소비"""
        def callback_wrapper(ch, method, properties, body):
            try:
                # 메시지를 JSON으로 파싱 시도
                try:
                    data = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    data = body.decode('utf-8')
                
                # 비동기 태스크 생성
                asyncio.create_task(async_callback(data))
                logger.info(f"비동기 태스크가 생성되었습니다: {data}")
                
            except Exception as e:
                logger.error(f"메시지 처리 중 오류 발생: {str(e)}")

        try:
            self.channel.basic_consume(
                queue=self.queue_name, 
                on_message_callback=callback_wrapper, 
                auto_ack=True
            )
            logger.info("비동기 메시지 소비를 시작합니다.")
            
            # 논블로킹 방식으로 메시지 처리
            while True:
                self.connection.process_data_events(time_limit=1)
                await asyncio.sleep(0.1)  # 다른 코루틴에게 제어권 양보
                
        except Exception as e:
            logger.error(f"비동기 메시지 소비 실패: {str(e)}")

    def consume(self, callback):
        """큐에서 메시지를 소비 (기존 동기 방식)"""
        try:
            self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
            logger.info("메시지 소비를 시작합니다.")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"메시지 소비 실패: {str(e)}")

    def close(self):
        """RabbitMQ 연결 종료"""
        if self.connection:
            self.connection.close()
            logger.info("RabbitMQ 연결이 종료되었습니다.")
        if self.executor:
            self.executor.shutdown(wait=True)