# know me

24-25 SW창업캡스톤 디자인
지도교수: 정지용
참가학생: 
# KnowMe AI - 비동기 문서 처리 시스템

## 개요

KnowMe AI는 RabbitMQ 기반의 비동기 태스크 처리를 통해 문서를 효율적으로 관리하고 처리하는 시스템입니다. 벡터 데이터베이스, 임베딩 생성, 객체 저장소를 통합하여 완전한 문서 처리 파이프라인을 제공합니다.

## 주요 기능

- **비동기 태스크 처리**: RabbitMQ를 통한 메시지 기반 비동기 작업 처리
- **벡터 데이터베이스**: ChromaDB를 이용한 문서 임베딩 저장 및 검색
- **임베딩 생성**: Sentence Transformers를 활용한 고품질 문서 임베딩
- **객체 저장소**: MinIO를 통한 대용량 파일 저장 및 관리
- **실시간 모니터링**: 태스크 상태 및 시스템 모니터링

## 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   문서 업로드    │───▶│   RabbitMQ      │───▶│  태스크 워커     │
│                │    │   메시지 큐      │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐             ▼
│   MinIO         │◀───│   ChromaDB      │    ┌─────────────────┐
│   객체 저장소    │    │   벡터 DB       │◀───│  문서 처리       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 프로젝트 구조

```
knowme_ai/
├── src/
│   ├── main.py                # 메인 애플리케이션 (비동기 태스크 처리)
│   ├── database/              # 벡터 데이터베이스 관리
│   │   └── vector_database.py
│   ├── embedding/             # 임베딩 생성
│   │   └── embedder.py
│   ├── storage/               # MinIO 객체 저장소
│   │   └── minio_client.py
│   ├── queue/                 # RabbitMQ 메시지 큐
│   │   ├── rabbitmq_client.py # RabbitMQ 클라이언트
│   │   ├── task_manager.py    # 태스크 관리자
│   │   └── task_handlers.py   # 태스크 핸들러들
│   ├── api/                   # REST API
│   ├── models/                # 데이터 모델
│   └── utils/                 # 유틸리티 함수들
├── tests/                     # 단위 테스트
├── config/                    # 설정 파일
│   └── settings.py
├── docker-compose.yml         # Docker 환경 설정
├── requirements.txt           # Python 의존성
├── examples.py                # 사용 예제
└── README.md
```

## 설치 및 설정

### 1. 필수 요구사항

- Python 3.8+
- Docker & Docker Compose
- Git

### 2. 프로젝트 클론 및 의존성 설치

```powershell
git clone <repository-url>
cd knowme_ai
pip install -r requirements.txt
```

### 3. Docker 서비스 시작

```powershell
docker-compose up -d
```

이 명령어는 다음 서비스들을 시작합니다:

- **RabbitMQ**: 메시지 큐 (포트 5672, 관리 UI: 15672)
- **ChromaDB**: 벡터 데이터베이스 (포트 8000)
- **MinIO**: 객체 저장소 (포트 9000, 콘솔: 9001)
- **MySQL**: 메타데이터 저장 (포트 3306)

## 사용 방법

### 1. 메인 애플리케이션 실행

```powershell
python src/main.py
```

### 2. 테스트 메시지 전송

```powershell
python src/main.py test
```

### 3. 사용 예제 실행

```powershell
python examples.py
```

## 지원하는 태스크 타입

### 문서 처리 (`document_processing`)

```json
{
  "task_type": "document_processing",
  "document_id": "doc_001",
  "file_path": "document.txt"
}
```

### 임베딩 생성 (`embedding_generation`)

```json
{
  "task_type": "embedding_generation",
  "document_id": "doc_001",
  "text": "처리할 텍스트 내용"
}
```

### 파일 업로드 (`file_upload`)

```json
{
  "task_type": "file_upload",
  "local_path": "local_file.txt",
  "bucket_name": "documents",
  "object_name": "remote_file.txt"
}
```

### 벡터 DB 삽입 (`vector_insert`)

```json
{
    "task_type": "vector_insert",
    "document_id": "doc_001",
    "embedding": [0.1, 0.2, 0.3, ...],
    "metadata": {"title": "문서 제목"}
}
```

### 알림 전송 (`notification`)

```json
{
  "task_type": "notification",
  "message": "처리 완료",
  "recipient": "user@example.com"
}
```

## 모니터링

### RabbitMQ 관리 콘솔

- URL: http://localhost:15672
- 기본 계정: guest/guest

### MinIO 콘솔

- URL: http://localhost:9001
- 기본 계정: minioadmin/minioadmin

### ChromaDB

- URL: http://localhost:8000

## 개발 및 테스트

### 단위 테스트 실행

```powershell
python -m pytest tests/ -v
```

### 코드 품질 검사

```powershell
# flake8 설치 후 실행
pip install flake8
flake8 src/
```

## 설정 파일

`config/settings.py`에서 다음 설정들을 수정할 수 있습니다:

- **RABBITMQ_HOST**: RabbitMQ 서버 호스트
- **MINIO_ENDPOINT**: MinIO 서버 엔드포인트
- **EMBEDDING_MODEL**: 사용할 임베딩 모델
- **MAX_CONCURRENT_TASKS**: 최대 동시 실행 태스크 수

## 문제 해결

### 일반적인 문제들

1. **RabbitMQ 연결 실패**

   ```powershell
   docker-compose restart rabbitmq
   ```

2. **MinIO 접근 불가**

   ```powershell
   docker-compose restart minio
   ```

3. **ChromaDB 초기화 문제**
   ```powershell
   Remove-Item -Recurse -Force chroma_db/
   docker-compose restart chromadb
   ```

### 로그 확인

```powershell
# 애플리케이션 로그
python src/main.py

# Docker 서비스 로그
docker-compose logs -f [service_name]
```

## 기여하기

1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/new-feature`)
3. 변경사항을 커밋합니다 (`git commit -am 'Add new feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/new-feature`)
5. Pull Request를 생성합니다

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 연락처

문의사항이 있으시면 이슈를 생성해 주세요.
