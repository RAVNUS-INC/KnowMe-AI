"""
사용 예제

RabbitMQ 기반 비동기 태스크 처리 시스템의 사용 예제들
"""

import asyncio
import json
from queue.rabbitmq_client import RabbitMQClient
from queue.task_manager import TaskManager
from queue.task_handlers import document_processing_task

async def example_basic_usage():
    """기본 사용 예제"""
    print("=== 기본 사용 예제 ===")
    
    # RabbitMQ 클라이언트 생성
    client = RabbitMQClient(host='localhost', queue_name='example_queue')
    
    # 태스크 매니저 생성
    task_manager = TaskManager()
    
    # 핸들러 등록
    task_manager.register_handler('test_task', test_task_handler)
    
    # 메시지 발송
    test_message = {
        'task_type': 'test_task',
        'data': '테스트 데이터',
        'timestamp': '2024-01-01T00:00:00'
    }
    client.publish_json(test_message)
    
    # 메시지 처리
    await client.async_consume(task_manager.process_message)

async def test_task_handler(data):
    """테스트 태스크 핸들러"""
    print(f"태스크 처리 중: {data}")
    await asyncio.sleep(1)
    print("태스크 완료!")

async def example_document_processing():
    """문서 처리 예제"""
    print("=== 문서 처리 예제 ===")
    
    client = RabbitMQClient(queue_name='document_queue')
    
    # 문서 처리 메시지 전송
    doc_message = {
        'task_type': 'document_processing',
        'document_id': 'doc_12345',
        'file_path': 'sample_document.txt',
        'metadata': {
            'author': '홍길동',
            'created_at': '2024-01-01',
            'category': '기술문서'
        }
    }
    
    client.publish_json(doc_message)
    client.close()
    print("문서 처리 요청 전송 완료")

async def example_batch_processing():
    """배치 처리 예제"""
    print("=== 배치 처리 예제 ===")
    
    client = RabbitMQClient(queue_name='batch_queue')
    
    # 여러 태스크를 한번에 전송
    tasks = [
        {
            'task_type': 'embedding_generation',
            'document_id': f'doc_{i:03d}',
            'text': f'문서 {i}의 내용입니다.'
        }
        for i in range(10)
    ]
    
    for task in tasks:
        client.publish_json(task)
    
    client.close()
    print(f"{len(tasks)}개의 임베딩 생성 태스크 전송 완료")

async def example_file_pipeline():
    """파일 처리 파이프라인 예제"""
    print("=== 파일 처리 파이프라인 예제 ===")
    
    client = RabbitMQClient(queue_name='pipeline_queue')
    
    # 파이프라인: 파일 업로드 -> 문서 처리 -> 임베딩 생성 -> 벡터 DB 저장
    pipeline_tasks = [
        {
            'task_type': 'file_upload',
            'local_path': 'documents/report.pdf',
            'bucket_name': 'documents',
            'object_name': 'reports/2024/report.pdf'
        },
        {
            'task_type': 'document_processing',
            'document_id': 'report_2024',
            'file_path': 'documents/report.pdf'
        },
        {
            'task_type': 'embedding_generation',
            'document_id': 'report_2024',
            'text': '2024년 연간 보고서 내용...'
        },
        {
            'task_type': 'vector_insert',
            'document_id': 'report_2024',
            'embedding': [0.1, 0.2, 0.3],  # 실제로는 384차원 벡터
            'metadata': {
                'title': '2024년 연간 보고서',
                'type': 'report',
                'year': 2024
            }
        },
        {
            'task_type': 'notification',
            'message': '문서 처리가 완료되었습니다: 2024년 연간 보고서',
            'recipient': 'admin@company.com',
            'type': 'success'
        }
    ]
    
    for task in pipeline_tasks:
        client.publish_json(task)
        await asyncio.sleep(0.1)  # 순차 처리를 위한 짧은 지연
    
    client.close()
    print("파일 처리 파이프라인 태스크 전송 완료")

def run_examples():
    """예제 실행"""
    print("KnowMe AI 태스크 처리 시스템 예제")
    print("=" * 50)
    
    # 비동기 예제들 실행
    asyncio.run(example_document_processing())
    asyncio.run(example_batch_processing())
    asyncio.run(example_file_pipeline())
    
    print("\n모든 예제 태스크가 큐에 전송되었습니다.")
    print("메인 애플리케이션을 실행하여 태스크를 처리하세요:")
    print("python src/main.py")

if __name__ == "__main__":
    run_examples()
