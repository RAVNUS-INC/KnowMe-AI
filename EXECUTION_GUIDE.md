# RabbitMQ 기반 AI 추천 시스템 실행 가이드

## 🚀 시스템 실행 방법

### 1. 환경 설정

```powershell
# 1. 환경 변수 파일 생성
Copy-Item .env.example .env

# 2. .env 파일에서 OpenAI API 키 설정 (필수!)
# OPENAI_API_KEY=your_actual_api_key_here
```

### 2. Docker 서비스 시작

```powershell
# RabbitMQ, ChromaDB, MinIO 등 인프라 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

### 3. Python 의존성 설치

```powershell
# 필요한 패키지 설치
pip install -r requirements.txt
```

### 4. 워커 프로세스 시작

```powershell
# 메인 워커 프로세스 시작 (메시지 처리기)
python src/main.py
```

## 🧪 테스트 방법

### 방법 1: RabbitMQ 테스트 클라이언트 사용

**새 터미널 창에서:**

```powershell
# RabbitMQ 기반 추천 테스트 실행
python test_rabbitmq_recommendations.py
```

### 방법 2: 직접 메시지 전송

```python
import asyncio
import json
from src.queue.rabbitmq_client import RabbitMQClient

async def send_recommendation_request():
    client = RabbitMQClient()

    # 대외활동 추천 요청
    message = {
        "task_type": "recommend_activities_with_metadata",
        "data": {
            "user_profile": {
                "user_id": "test_user",
                "major": "컴퓨터공학",
                "interests": ["AI", "창업"],
                "skills": ["Python", "머신러닝"]
            },
            "metadata_filters": {
                "activityField": "창업",
                "activityDuration": {"min": 7, "max": 90}
            },
            "n_results": 5
        }
    }

    await client.send_message(message)
    print("추천 요청 전송 완료!")

# 실행
asyncio.run(send_recommendation_request())
```

## 📊 모니터링 및 확인

### 1. RabbitMQ 관리 UI

- URL: http://localhost:15672
- 사용자명: admin
- 비밀번호: hello

### 2. 로그 확인

- 워커 프로세스 로그에서 처리 결과 확인
- 각 추천 요청의 처리 상태와 결과 모니터링

### 3. ChromaDB 데이터 확인

```python
from src.database.vector_database import ChromaVectorDB

# 활동 데이터 확인
activity_db = ChromaVectorDB(collection_name="activities")
print(f"저장된 활동 수: {activity_db.collection.count()}")

# 채용공고 데이터 확인
job_db = ChromaVectorDB(collection_name="recruitments")
print(f"저장된 채용공고 수: {job_db.collection.count()}")
```

## 🔧 문제 해결

### OpenAI API 키 오류

```
Error: OpenAI API key not found
```

- `.env` 파일에서 `OPENAI_API_KEY` 설정 확인
- 유효한 OpenAI API 키인지 확인

### RabbitMQ 연결 오류

```
Error: Connection failed to RabbitMQ
```

- Docker 서비스가 실행 중인지 확인: `docker-compose ps`
- RabbitMQ 포트(5672) 접근 가능한지 확인

### ChromaDB 연결 오류

```
Error: Could not connect to ChromaDB
```

- ChromaDB 디렉토리 권한 확인
- 포트 8000이 사용 중인지 확인

## 📈 성능 모니터링

### 메시지 처리 속도

```powershell
# RabbitMQ 큐 상태 확인
docker exec knowme_ai-rabbitmq-1 rabbitmqctl list_queues
```

### 시스템 리소스

```powershell
# Docker 컨테이너 리소스 사용량
docker stats
```

## 🎯 추천 결과 예시

성공적인 추천 실행 시 다음과 같은 결과를 볼 수 있습니다:

```
2024-06-01 10:00:00 - INFO - 메타데이터 기반 대외활동 추천 시작: test_user
2024-06-01 10:00:02 - INFO - 벡터 검색 완료: 5개 결과 발견
2024-06-01 10:00:05 - INFO - AI 추천 생성 완료
2024-06-01 10:00:05 - INFO - 메타데이터 기반 대외활동 추천 완료: 5개 추천
```
