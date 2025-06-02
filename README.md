# KnowMe AI - 개인화 AI 분석 및 추천 시스템

## 개요

KnowMe AI는 벡터 데이터베이스와 OpenAI GPT를 활용한 개인화 AI 서비스입니다. 포트폴리오 문서를 분석하여 사용자에게 맞춤형 대외활동 추천, 채용 공고 추천, 포트폴리오 강점/약점 분석을 제공합니다. **순수 Python 서비스**로 구현되어 CLI 도구와 RabbitMQ 메시지 기반 시스템을 통해 사용할 수 있습니다.

## 주요 기능

- **🎯 개인화 AI 분석**: OpenAI GPT를 활용한 포트폴리오 기반 맞춤 분석
- **📋 대외활동 추천**: 사용자 프로필 기반 개인화 활동 추천
- **💼 채용 공고 추천**: 스킬과 경력에 맞는 적합한 직무 추천
- **📊 포트폴리오 분석**: 강점/약점 평가 및 개선 방안 제시
- **🔍 벡터 검색**: ChromaDB를 이용한 의미 기반 문서 검색
- **🚀 CLI 도구**: 명령줄에서 간편하게 사용할 수 있는 인터페이스
- **📨 메시지 기반 처리**: RabbitMQ를 통한 비동기 작업 처리

## 🚀 새로운 AI 추천 기능

### 1. 대외활동 추천 🎯

- **포트폴리오 기반 분석**: 기존 프로젝트와 스킬을 바탕으로 적합한 활동 추천
- **개인화 필터링**: 관심분야, 선호 지역, 활동 유형별 맞춤 추천
- **성장 경로 제시**: 현재 수준에서 다음 단계로 나아갈 활동 제안

### 2. 채용 공고 추천 💼

- **스킬 매칭**: 보유 기술과 경험에 맞는 직무 추천
- **경력 단계별 추천**: 신입/경력직 구분한 적합한 포지션 제안
- **시장 분석**: 희망 분야의 채용 트렌드와 요구사항 분석

### 3. 포트폴리오 분석 📊

- **강점/약점 평가**: AI 기반 포트폴리오 종합 분석을 간결한 문장으로 제공
- **추천 포지션**: 분석 결과를 바탕으로 가장 적합한 직무 추천
- **간단한 JSON 형식**: `strength`, `weakness`, `recommend_position` 3개 필드로 구성된 명확한 결과
- **실행 가능한 인사이트**: 복잡한 데이터가 아닌 실용적이고 이해하기 쉬운 분석 결과

## 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI 도구       │───▶│  PersonalizedAI │───▶│   OpenAI GPT    │
│  (사용자 입력)   │    │    Service      │    │  (AI 분석)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │                       │
┌─────────────────┐             ▼                       ▼
│   RabbitMQ      │    ┌─────────────────┐    ┌─────────────────┐
│   메시지 큐      │◀───│   ChromaDB      │◀───│  벡터 검색 및    │
└─────────────────┘    │   벡터 DB       │    │  컨텍스트 추출   │
                       └─────────────────┘    └─────────────────┘
```

**🔄 순수 Python 서비스 아키텍처**

- FastAPI 없이 순수 Python 서비스로 구현
- CLI 도구를 통한 직관적인 사용자 인터페이스
- RabbitMQ 메시지 기반 비동기 처리 지원
- 벡터 데이터베이스를 통한 의미 기반 검색

## 프로젝트 구조

```
knowme_ai/
├── ai_cli.py                  # 🆕 CLI 도구 (메인 인터페이스)
├── src/
│   ├── main.py                # RabbitMQ 메시지 처리 워커
│   ├── services/              # 🆕 AI 서비스
│   │   └── personalized_ai_service.py  # 개인화 AI 서비스
│   ├── database/              # 벡터 데이터베이스
│   │   └── vector_database.py
│   ├── config/                # 설정 관리
│   │   └── settings.py
│   ├── task_queue/            # RabbitMQ 관리
│   │   ├── rabbitmq_client.py
│   │   ├── task_manager.py
│   │   └── task_handlers.py
│   ├── models/                # 데이터 모델
│   └── utils/                 # 유틸리티
├── tests/                     # 테스트
├── chroma_db/                 # 벡터 DB 저장소
├── docker-compose.yml         # Docker 환경
└── requirements.txt           # 의존성
```

## 설치 및 설정

### 1. 필수 요구사항

- Python 3.12+
- OpenAI API 키
- Docker & Docker Compose (선택사항 - RabbitMQ 사용시)

### 2. 프로젝트 클론 및 의존성 설치

```powershell
git clone <repository-url>
cd knowme_ai
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```powershell
# .env 파일 생성 및 설정
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_DB_PATH=./chroma_db
```

### 4. Docker 서비스 시작 (선택사항)

```powershell
# RabbitMQ 등 백엔드 서비스가 필요한 경우
docker-compose up -d
```

## 🎯 사용 방법

### 1. CLI 도구 사용 (추천)

KnowMe AI는 사용하기 쉬운 CLI 도구를 제공합니다:

#### 포트폴리오 강점/약점 분석

```powershell
# 기본 분석
python ai_cli.py portfolio

# 특정 영역 집중 분석
python ai_cli.py portfolio --focus "기술,경험"

# 테스트 모드 (OpenAI API 호출 없이)
python ai_cli.py portfolio --test
```

#### 대외활동 추천

```powershell
# 기본 추천
python ai_cli.py activities

# 선호도 포함 추천
python ai_cli.py activities --preferences '{"관심분야": "AI", "지역": "서울"}'

# 테스트 모드
python ai_cli.py activities --test
```

#### 채용 공고 추천

```powershell
# 기본 추천
python ai_cli.py jobs

# 테스트 모드
python ai_cli.py jobs --test
```

#### 종합 분석

```powershell
# 모든 분석을 한번에
python ai_cli.py comprehensive

# JSON 형태로 상세 결과
python ai_cli.py comprehensive --json

# 테스트 모드
python ai_cli.py comprehensive --test --json
```

### 2. Python 코드에서 직접 사용

```python
from src.services.personalized_ai_service import PersonalizedAIService

# 서비스 초기화
service = PersonalizedAIService()

# 포트폴리오 분석
portfolio_result = service.analyze_portfolio_strengths_weaknesses()
print(f"평가: {portfolio_result['overall_assessment']['grade']}")

# 대외활동 추천
activities_result = service.recommend_activities()
for activity in activities_result['recommendations']:
    print(f"추천: {activity['title']}")

# 채용 공고 추천
jobs_result = service.recommend_jobs()
for job in jobs_result['job_recommendations']:
    print(f"직무: {job['position']}")
```

### 3. RabbitMQ 메시지 기반 사용 (고급)

RabbitMQ를 통한 비동기 처리가 필요한 경우:

#### 워커 프로세스 시작

```powershell
# RabbitMQ 서비스 시작
docker-compose up -d

# 메시지 처리 워커 시작
python src/main.py
```

#### 테스트 클라이언트 실행

```powershell
# 새 터미널에서 RabbitMQ 테스트
python tests/test_rabbitmq_recommendations.py
```

## 🛠️ 개발 및 테스트

### 단위 테스트 실행

```powershell
# 모든 테스트 실행
pytest tests/

# 특정 테스트 실행
pytest tests/test_vector_database.py
```

### 벡터 데이터베이스 상태 확인

```powershell
# 벡터 DB 테스트
python tests/test_vector_database.py
```

## 📚 API 참조

### PersonalizedAIService 클래스

```python
class PersonalizedAIService:
    def __init__(self, test_mode: bool = False):
        """
        Args:
            test_mode: True일 경우 OpenAI API 호출 없이 모의 응답 반환
        """

    def recommend_activities(self, preferences: dict = None) -> dict:
        """대외활동 추천"""

    def recommend_jobs(self, criteria: dict = None) -> dict:
        """채용 공고 추천"""    def analyze_portfolio_strengths_weaknesses(self, focus_areas: list = None) -> dict:
        """
        포트폴리오 강점/약점 분석

        Returns:
            {
                "success": True,
                "strength": "포트폴리오의 주요 강점을 종합한 문장",
                "weakness": "포트폴리오의 주요 약점을 종합한 문장",
                "recommend_position": "추천 포지션",
                "generated_at": "2025-06-03T03:22:44.984111"
            }
        """
```

### CLI 명령어 상세

```powershell
# 도움말
python ai_cli.py --help
python ai_cli.py portfolio --help

# 모든 명령에 공통 옵션
--test          # 테스트 모드 활성화
--json          # JSON 형태 출력 (comprehensive 명령)
--focus         # 분석 영역 지정 (portfolio 명령)
--preferences   # 선호도 JSON 문자열 (activities 명령)
```

## 🔧 설정

### 환경 변수

```bash
# .env 파일
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_DB_PATH=./chroma_db
OPENAI_MODEL=gpt-4o-mini

# RabbitMQ 설정 (선택사항)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=hello
```

### 설정 파일 수정

`src/config/settings.py`에서 시스템 설정을 변경할 수 있습니다:

```python
class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    vector_db_path: str = "./chroma_db"
    # ... 기타 설정
```

## 🚨 문제 해결

### 일반적인 문제

1. **OpenAI API 키 오류**

   ```
   해결: .env 파일에 OPENAI_API_KEY 설정 확인
   ```

2. **벡터 데이터베이스 연결 실패**

   ```
   해결: chroma_db 폴더 권한 확인, 또는 삭제 후 재생성
   ```

3. **CLI 도구 실행 오류**
   ```
   해결:
   cd c:\Workspace\knowme_ai
   python -m pip install -r requirements.txt
   python ai_cli.py portfolio --test
   ```

### 로깅

상세한 로그는 콘솔에 출력됩니다. 로그 레벨을 변경하려면:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📋 할 일 목록

- [ ] 웹 UI 인터페이스 추가
- [ ] 더 많은 포트폴리오 문서 유형 지원
- [ ] 실시간 채용 공고 크롤링 연동
- [ ] 사용자 피드백 기반 추천 개선
- [ ] 다국어 지원

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 연락처

프로젝트 관련 문의사항이나 버그 리포트는 GitHub Issues를 이용해 주세요.

---

**KnowMe AI** - 당신의 성장을 위한 AI 파트너 🚀
