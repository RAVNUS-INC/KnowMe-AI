# 🚀 RabbitMQ 기반 AI 추천 시스템 - 완전 실행 가이드

## 📋 시스템 개요

이 시스템은 **FastAPI 없이 순수 RabbitMQ 메시지**만으로 AI 추천 기능을 제공합니다.

- 메타데이터 기반 벡터 검색
- OpenAI GPT를 활용한 개인화 추천
- 비동기 메시지 처리

## 🛠️ 사전 준비

### 1. 필수 소프트웨어

- Python 3.8+
- Docker & Docker Compose
- OpenAI API 키

### 2. 환경 설정

```powershell
# 1. 환경 변수 파일 생성
Copy-Item .env.example .env

# 2. .env 파일 편집 - OpenAI API 키 설정 (필수!)
# OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Python 패키지 설치

```powershell
pip install -r requirements.txt
```

## 🐳 Docker 서비스 시작

```powershell
# 모든 인프라 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

**시작되는 서비스들:**

- RabbitMQ (포트 5672, 관리 UI: 15672)
- ChromaDB (포트 8000)
- MinIO (포트 9000)
- MySQL (포트 3306)

## 🔧 시스템 실행

### 1단계: 워커 프로세스 시작

```powershell
# 메인 워커 시작 (메시지 처리기)
python src/main.py
```

워커가 시작되면 다음과 같은 로그를 볼 수 있습니다:

```
INFO - 메시지 처리기 시작
INFO - RabbitMQ 연결 성공
INFO - 태스크 핸들러 등록 완료
```

### 2단계: 클라이언트에서 추천 요청

**새 터미널 창에서:**

#### 방법 1: 제공된 테스트 스크립트 사용

```powershell
# 기본 테스트 실행
python test_rabbitmq_recommendations.py

# 또는 새로운 클라이언트 예제 실행
python rabbitmq_client_example.py activity
python rabbitmq_client_example.py job
python rabbitmq_client_example.py multiple
```

#### 방법 2: 직접 Python 코드 실행

```python
import asyncio
from src.queue.rabbitmq_client import RabbitMQClient

async def send_recommendation():
    client = RabbitMQClient()

    # 대외활동 추천 요청
    message = {
        "task_type": "recommend_activities_with_metadata",
        "data": {
            "user_profile": {
                "user_id": "test_user",
                "major": "컴퓨터공학",
                "interests": ["AI", "창업"],
                "skills": ["Python", "머신러닝"],
                "experience_level": "중급"
            },
            "metadata_filters": {
                "activityField": "창업",
                "activityDuration": {"min": 7, "max": 90}
            },
            "n_results": 5
        }
    }

    await client.send_message(message)
    print("✅ 추천 요청 전송 완료!")

# 실행
asyncio.run(send_recommendation())
```

## 📊 모니터링 및 확인

### 1. RabbitMQ 관리 UI

- **URL**: http://localhost:15672
- **로그인**: admin / hello
- 큐 상태, 메시지 수, 처리 속도 등을 실시간 모니터링

### 2. 워커 로그 확인

워커 프로세스에서 다음과 같은 로그를 확인할 수 있습니다:

```
INFO - 메타데이터 기반 대외활동 추천 시작: test_user
INFO - 벡터 검색 실행 중...
INFO - AI 추천 생성 중...
INFO - 메타데이터 기반 대외활동 추천 완료: 5개 추천
```

### 3. 벡터 데이터베이스 상태 확인

```python
from src.database.vector_database import ChromaVectorDB

# 활동 데이터베이스 확인
activity_db = ChromaVectorDB(collection_name="activities")
print(f"저장된 활동 수: {activity_db.collection.count()}")

# 채용공고 데이터베이스 확인
job_db = ChromaVectorDB(collection_name="recruitments")
print(f"저장된 채용공고 수: {job_db.collection.count()}")
```

## 🎯 지원하는 추천 타입

### 1. 메타데이터 기반 대외활동 추천

```json
{
  "task_type": "recommend_activities_with_metadata",
  "data": {
    "user_profile": {
      "user_id": "string",
      "major": "string",
      "interests": ["list"],
      "skills": ["list"],
      "experience_level": "string",
      "preferred_location": "string"
    },
    "metadata_filters": {
      "category": "string",
      "activityField": "string",
      "activityDuration": {"min": int, "max": int},
      "location": "string"
    },
    "n_results": int
  }
}
```

### 2. 메타데이터 기반 채용공고 추천

```json
{
  "task_type": "recommend_jobs_with_metadata",
  "data": {
    "user_profile": {
      "user_id": "string",
      "major": "string",
      "skills": ["list"],
      "desired_role": "string",
      "experience_years": int,
      "company_size_preference": "string"
    },
    "metadata_filters": {
      "requiredExperience": {"min": int, "max": int},
      "company": "string"
    },
    "n_results": int
  }
}
```

### 3. 기존 기능들

- `embedding_generation`: 텍스트 임베딩 생성
- `recommend_activity`: 기본 대외활동 추천
- `recommend_recruitment`: 기본 채용공고 추천

## 🚨 문제 해결

### OpenAI API 키 오류

```
Error: OpenAI API key not found
```

**해결**: `.env` 파일에서 `OPENAI_API_KEY` 설정 확인

### RabbitMQ 연결 실패

```
Error: Connection failed to RabbitMQ
```

**해결**:

```powershell
docker-compose restart rabbitmq
docker-compose logs rabbitmq
```

### ChromaDB 오류

```
Error: Could not connect to ChromaDB
```

**해결**: ChromaDB 디렉토리 권한 확인 및 재시작

### 워커 프로세스 오류

**해결**:

1. Python 경로 확인
2. 패키지 설치 상태 확인
3. 환경 변수 확인

## 🔄 시스템 중지

```powershell
# 워커 프로세스 중지: Ctrl+C

# Docker 서비스 중지
docker-compose down

# 데이터까지 완전 삭제 (주의!)
docker-compose down -v
```

## 📈 성능 최적화

### 여러 워커 인스턴스 실행

```powershell
# 터미널 1
python src/main.py

# 터미널 2
python src/main.py

# 터미널 3
python src/main.py
```

### 메시지 처리 속도 모니터링

```powershell
docker exec knowme_ai-rabbitmq-1 rabbitmqctl list_queues
```

이제 완전히 RabbitMQ 기반으로 동작하는 AI 추천 시스템이 준비되었습니다! 🎉
