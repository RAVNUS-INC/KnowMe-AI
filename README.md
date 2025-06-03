# KnowMe AI - 개인화 AI 분석 및 추천 시스템

## 개요

KnowMe AI는 벡터 데이터베이스와 OpenAI GPT를 활용한 개인화 AI 서비스입니다. 포트폴리오 문서를 분석하여 사용자에게 맞춤형 대외활동 추천, 채용 공고 추천, 포트폴리오 강점/약점 분석을 제공합니다. **순수 Python 서비스**로 구현되어 RabbitMQ 메시지 기반 시스템을 통해 사용할 수 있습니다.

## 주요 기능

- **📊 포트폴리오 분석**: 강점/약점 평가 및 개선 방안 제시
- **📨 메시지 기반 처리**: RabbitMQ를 통한 비동기 작업 처리
- 
## 🚀 새로운 AI 추천 기능

### 1. 포트폴리오 분석 📊

- **강점/약점 평가**: AI 기반 포트폴리오 종합 분석을 간결한 문장으로 제공
- **추천 포지션**: 분석 결과를 바탕으로 가장 적합한 직무 추천
- **간단한 JSON 형식**: `strength`, `weakness`, `recommend_position` 3개 필드로 구성된 명확한 결과
- **실행 가능한 인사이트**: 복잡한 데이터가 아닌 실용적이고 이해하기 쉬운 분석 결과

## 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Python 서비스   │───▶│  PersonalizedAI │───▶│   OpenAI GPT    │
│  (프로그래밍)    │    │    Service      │    │  (AI 분석)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │                       │
┌─────────────────┐             ▼                       ▼
│   RabbitMQ      │    ┌─────────────────┐    ┌─────────────────┐
│   메시지 큐      │◀───│   ChromaDB      │◀───│  벡터 검색 및    │
└─────────────────┘    │   벡터 DB       │    │  컨텍스트 추출   │
                       └─────────────────┘    └─────────────────┘
```

**🔄 순수 Python 서비스 아키텍처**

- 순수 Python 서비스로 구현
- RabbitMQ 메시지 기반 비동기 처리 지원

## 프로젝트 구조

## 프로젝트 구조

```
knowme_ai/
├── src/
│   ├── main.py                # RabbitMQ 메시지 처리 워커
│   ├── services/              # AI 서비스
│   │   └── personalized_ai_service.py  # 개인화 AI 서비스
│   ├── config/                # 설정 관리
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── task_queue/            # RabbitMQ 관리
│   │   ├── __init__.py
│   │   ├── rabbitmq_client.py
│   │   ├── task_manager.py
│   │   └── task_handlers.py
│   └── utils/                 # 유틸리티
│       ├── __init__.py
│       ├── logger.py          # 로깅 관리
│       └── pdf_extractor.py   # PDF 문서 처리
├── docker-compose.yml         # Docker 환경
├── pyproject.toml             # 프로젝트 설정 (uv 패키지 관리)
├── requirements.txt           # 의존성
└── uv.lock                    # uv 잠금 파일
```

**주요 파일 설명:**
- `src/main.py`: RabbitMQ 워커 프로세스의 진입점
- `src/services/personalized_ai_service.py`: 핵심 AI 분석 및 추천 서비스
- `src/utils/pdf_extractor.py`: PDF 포트폴리오 문서 처리
- `pyproject.toml`: uv 패키지 매니저를 위한 프로젝트 설정

## 설치 및 설정

### 1. 필수 요구사항

- Python 3.12+
- OpenAI API 키
- Docker & Docker Compose (선택사항 - RabbitMQ 사용시)

### 2. 프로젝트 클론 및 의존성 설치

```bash
git clone <repository-url>
cd knowme_ai

# uv를 사용한 의존성 설치 (권장)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성 및 설정
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_DB_PATH=./chroma_db
```

### 4. Docker 서비스 시작 (선택사항)

```bash
# RabbitMQ 등 백엔드 서비스가 필요한 경우
docker-compose up -d
```

## 🎯 사용 방법

### 1. Python 코드에서 직접 사용 (메인 방법)

```python
from src.services.personalized_ai_service import PersonalizedAIService

# 서비스 초기화
service = PersonalizedAIService()

# 포트폴리오 분석
portfolio_result = service.analyze_portfolio_strengths_weaknesses()
print(f"강점: {portfolio_result['strength']}")
print(f"약점: {portfolio_result['weakness']}")
print(f"추천 포지션: {portfolio_result['recommend_position']}")

# 대외활동 추천
activities_result = service.recommend_activities()
for activity in activities_result['recommendations']:
    print(f"추천: {activity['title']}")

# 채용 공고 추천
jobs_result = service.recommend_jobs()
for job in jobs_result['job_recommendations']:
    print(f"직무: {job['position']}")
```

### 2. RabbitMQ 메시지 기반 사용 (고급)

RabbitMQ를 통한 비동기 처리가 필요한 경우:

#### 워커 프로세스 시작

```bash
# RabbitMQ 서비스 시작
docker-compose up -d

# 메시지 처리 워커 시작
python src/main.py
```

#### 테스트 클라이언트 실행

```bash
# 새 터미널에서 RabbitMQ 테스트
python -m pytest -v
```

## 🛠️ 개발 및 테스트

### 단위 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행 (예시)
python test_portfolio_analysis.py
```

### PDF 문서 처리 테스트

```bash
# PDF 추출 기능 테스트
python -c "from src.utils.pdf_extractor import PDFExtractor; print('PDF extractor works!')"
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

    def recommend_activities(self, preferences: dict = None, user_id: str = None) -> dict:
        """
        대외활동 추천
        
        Returns:
            {
                "success": True,
                "recommendations": [
                    {
                        "activity_type": "활동 유형",
                        "title": "활동명",
                        "description": "활동 설명",
                        "relevance_reason": "추천 이유",
                        "expected_benefits": ["혜택1", "혜택2"],
                        "difficulty_level": "난이도",
                        "time_commitment": "소요 시간"
                    }
                ],
                "overall_strategy": "전체 전략",
                "priority_areas": ["우선영역1", "우선영역2"]
            }
        """

    def recommend_jobs(self, criteria: dict = None, user_id: str = None) -> dict:
        """
        채용 공고 추천
        
        Returns:
            {
                "success": True,
                "job_recommendations": [
                    {
                        "position": "직무명",
                        "company_type": "회사 유형",
                        "match_score": "매칭 점수",
                        "required_skills": ["필요 스킬"],
                        "growth_potential": "성장 가능성",
                        "why_suitable": "적합 이유"
                    }
                ],
                "market_insights": "시장 분석",
                "career_advice": "커리어 조언"
            }
        """

    def analyze_portfolio_strengths_weaknesses(self, focus_areas: list = None, user_id: str = None) -> dict:
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

    def get_comprehensive_insights(self, user_id: str = None) -> dict:
        """종합적인 분석 결과 제공"""

    def analyze_portfolio_from_data(self, portfolio_data: dict) -> dict:
        """특정 포트폴리오 데이터를 기반으로 분석"""
```

### CLI 명령어 상세

현재 프로젝트는 CLI 도구 대신 Python 모듈로 직접 사용하도록 설계되어 있습니다. 다음과 같이 사용할 수 있습니다:

```bash
# 서비스 직접 실행
python -c "
from src.services.personalized_ai_service import PersonalizedAIService
service = PersonalizedAIService(test_mode=True)
result = service.analyze_portfolio_strengths_weaknesses()
print(result)
"

# 메인 워커 실행
python src/main.py
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

3. **Python 모듈 import 오류**
   ```bash
   # 해결방법
   cd /Users/seongyun/Code/KnowMe-AI
   uv sync  # 또는 pip install -r requirements.txt
   export PYTHONPATH=/Users/seongyun/Code/KnowMe-AI:$PYTHONPATH
   python -c "from src.services.personalized_ai_service import PersonalizedAIService; print('Import successful')"
   ```

### 로깅

상세한 로그는 콘솔에 출력됩니다. 로그 레벨을 변경하려면:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📋 할 일 목록

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
