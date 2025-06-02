"""
비동기 태스크 매니저

RabbitMQ에서 받은 메시지를 기반으로 비동기 태스크를 실행하는 매니저 클래스
"""

import asyncio
import logging
from typing import Dict, Any, Callable
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class TaskManager:
    """비동기 태스크 관리 클래스"""
    
    def __init__(self):
        self.running_tasks = {}
        self.task_handlers = {}
        
    def register_handler(self, task_type: str, handler: Callable):
        """태스크 타입별 핸들러 등록"""
        self.task_handlers[task_type] = handler
        logger.info(f"태스크 핸들러 등록됨: {task_type}")
    
    async def process_message(self, message_data: Dict[str, Any]):
        """메시지 데이터를 기반으로 태스크 처리"""
        try:
            # 메시지에서 태스크 타입 추출
            task_type = message_data.get('task_type')
            if not task_type:
                logger.error("태스크 타입이 메시지에 포함되지 않음")
                return
            
            # 등록된 핸들러 확인
            if task_type not in self.task_handlers:
                logger.error(f"등록되지 않은 태스크 타입: {task_type}")
                return
            
            # 태스크 ID 생성
            task_id = str(uuid.uuid4())
            
            # 태스크 실행
            handler = self.task_handlers[task_type]
            task = asyncio.create_task(self._execute_task(task_id, handler, message_data))
            
            # 실행 중인 태스크 추가
            self.running_tasks[task_id] = {
                'task': task,
                'type': task_type,
                'started_at': datetime.now(),
                'data': message_data
            }
            
            logger.info(f"태스크 시작됨: {task_id} (타입: {task_type})")
            
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {str(e)}")
    async def _execute_task(self, task_id: str, handler: Callable, data: Dict[str, Any]):
        """태스크 실행"""
        try:
            # 메시지의 data 필드만 핸들러에 전달
            task_data = data.get('data', {})
            await handler(task_data)
            logger.info(f"태스크 완료: {task_id}")
        except Exception as e:
            logger.error(f"태스크 실행 오류 {task_id}: {str(e)}")
        finally:
            # 완료된 태스크 제거
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def get_running_tasks(self) -> Dict[str, Dict]:
        """실행 중인 태스크 목록 반환"""
        return {
            task_id: {
                'type': info['type'],
                'started_at': info['started_at'],
                'data': info['data']
            }
            for task_id, info in self.running_tasks.items()
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """태스크 취소"""
        if task_id in self.running_tasks:
            task_info = self.running_tasks[task_id]
            task_info['task'].cancel()
            del self.running_tasks[task_id]
            logger.info(f"태스크 취소됨: {task_id}")
            return True
        return False
