"""
ChromaDB 최적화 Recruitment 스키마 정의

ChromaDB 벡터 데이터베이스에 최적화된 채용공고 모델입니다.
- 메타데이터: ChromaDB의 메타데이터 제약사항(string, int, float, bool만 지원) 준수
- 임베딩 텍스트: 의미있는 검색을 위한 텍스트 생성
- 문서 구조: ChromaDB의 document, metadata, id 구조에 맞춤

기본 JSON 구조:
{
    "id": 1001,
    "title": "채용공고",
    "company": "google",
    "applicationDeadline": "2025-02-22",
    "tags": [],
    "requiredExperience": 1
}
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
import json
import hashlib
import chromadb
from sentence_transformers import SentenceTransformer
import logging
from pathlib import Path
from contextlib import contextmanager
import uuid

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Recruitment(BaseModel):
    """ChromaDB용 채용공고 메타데이터 모델"""

    # 필수 필드들 (원본 JSON 구조)
    id: int = Field(..., description="채용공고 고유 ID")
    title: str = Field(..., min_length=1, max_length=200, description="채용공고 제목")
    company: str = Field(..., min_length=1, max_length=100, description="회사명")
    applicationDeadline: str = Field(..., description="지원 마감일 (YYYY-MM-DD)")
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    requiredExperience: int = Field(..., ge=0, le=50, description="요구 경력 (년)")

    # ChromaDB 최적화를 위한 추가 필드들
    description: Optional[str] = Field(
        None, max_length=5000, description="채용공고 상세 설명"
    )
    location: Optional[str] = Field(None, max_length=100, description="근무지")
    employment_type: Optional[str] = Field(
        None, description="고용 형태 (정규직, 계약직, 인턴 등)"
    )
    department: Optional[str] = Field(None, max_length=100, description="부서/팀")
    position: Optional[str] = Field(None, max_length=100, description="모집 포지션")
    salary_min: Optional[int] = Field(None, ge=0, description="최소 연봉 (만원)")
    salary_max: Optional[int] = Field(None, ge=0, description="최대 연봉 (만원)")
    benefits: List[str] = Field(default_factory=list, description="복리후생")
    required_skills: List[str] = Field(default_factory=list, description="필수 기술")
    preferred_skills: List[str] = Field(default_factory=list, description="우대 기술")
    education_level: Optional[str] = Field(None, description="학력 요구사항")
    contact_email: Optional[str] = Field(None, description="지원 이메일")
    contact_phone: Optional[str] = Field(None, description="연락처")
    posting_date: Optional[str] = Field(None, description="게시일 (YYYY-MM-DD)")

    # ChromaDB 메타데이터
    document_id: Optional[str] = Field(None, description="ChromaDB 문서 ID")
    collection_name: str = Field(
        default="recruitments", description="ChromaDB 컬렉션명"
    )
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="생성일시"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="수정일시"
    )
    version: int = Field(default=1, description="스키마 버전")
    is_active: bool = Field(default=True, description="활성 상태")

    @validator("applicationDeadline")
    def validate_application_deadline(cls, v):
        """지원 마감일 형식 검증"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("지원 마감일은 YYYY-MM-DD 형식이어야 합니다")
        return v

    @validator("posting_date")
    def validate_posting_date(cls, v):
        """게시일 형식 검증"""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("게시일은 YYYY-MM-DD 형식이어야 합니다")
        return v

    @validator("title")
    def validate_title(cls, v):
        """제목 검증"""
        if not v.strip():
            raise ValueError("채용공고 제목은 비어있을 수 없습니다")
        return v.strip()

    @validator("company")
    def validate_company(cls, v):
        """회사명 검증"""
        if not v.strip():
            raise ValueError("회사명은 비어있을 수 없습니다")
        return v.strip()

    @validator("tags")
    def validate_tags(cls, v):
        """태그 목록 정규화"""
        return [tag.strip() for tag in v if tag.strip()]

    @validator("required_skills", "preferred_skills", "benefits")
    def validate_skill_lists(cls, v):
        """스킬 및 혜택 목록 정규화"""
        return [item.strip() for item in v if item.strip()]

    @validator("salary_max")
    def validate_salary_range(cls, v, values):
        """연봉 범위 검증"""
        if (
            v is not None
            and "salary_min" in values
            and values["salary_min"] is not None
        ):
            if v < values["salary_min"]:
                raise ValueError("최대 연봉은 최소 연봉보다 크거나 같아야 합니다")
        return v

    @validator("contact_email")
    def validate_contact_email(cls, v):
        """연락처 이메일 형식 검증"""
        if v is not None and "@" not in v:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v

    def add_tag(self, tag: str) -> None:
        """태그 추가"""
        if tag and tag not in self.tags:
            self.tags.append(tag.strip())
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """태그 제거"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def add_required_skill(self, skill: str) -> None:
        """필수 기술 추가"""
        if skill and skill.strip() not in self.required_skills:
            self.required_skills.append(skill.strip())
            self.updated_at = datetime.now()

    def add_preferred_skill(self, skill: str) -> None:
        """우대 기술 추가"""
        if skill and skill.strip() not in self.preferred_skills:
            self.preferred_skills.append(skill.strip())
            self.updated_at = datetime.now()

    def remove_required_skill(self, skill: str) -> None:
        """필수 기술 제거"""
        if skill in self.required_skills:
            self.required_skills.remove(skill)
            self.updated_at = datetime.now()

    def remove_preferred_skill(self, skill: str) -> None:
        """우대 기술 제거"""
        if skill in self.preferred_skills:
            self.preferred_skills.remove(skill)
            self.updated_at = datetime.now()

    def update_description(self, description: str) -> None:
        """채용공고 설명 업데이트"""
        self.description = description
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """채용공고 비활성화"""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """채용공고 활성화"""
        self.is_active = True
        self.updated_at = datetime.now()

    def is_deadline_passed(self) -> bool:
        """지원 마감일이 지났는지 확인"""
        try:
            deadline = datetime.strptime(self.applicationDeadline, "%Y-%m-%d").date()
            return date.today() > deadline
        except ValueError:
            return False

    def days_until_deadline(self) -> Optional[int]:
        """지원 마감일까지 남은 일수"""
        try:
            deadline = datetime.strptime(self.applicationDeadline, "%Y-%m-%d").date()
            today = date.today()
            delta = deadline - today
            return delta.days
        except ValueError:
            return None

    def is_deadline_soon(self, days: int = 7) -> bool:
        """마감일 임박 여부 (기본 7일)"""
        remaining_days = self.days_until_deadline()
        return remaining_days is not None and 0 <= remaining_days <= days

    def generate_document_id(self) -> str:
        """ChromaDB용 문서 ID 생성"""
        if not self.document_id:
            timestamp = (
                int(self.created_at.timestamp())
                if self.created_at
                else int(datetime.now().timestamp())
            )
            self.document_id = f"recruitment_{self.id}_{timestamp}"
        return self.document_id

    def to_embedding_text(self) -> str:
        """임베딩 생성용 텍스트 변환"""
        text_parts = []

        # 기본 정보
        text_parts.append(f"채용공고: {self.title}")
        text_parts.append(f"회사: {self.company}")
        text_parts.append(f"경력: {self.requiredExperience}년")

        if self.location:
            text_parts.append(f"근무지: {self.location}")

        if self.department:
            text_parts.append(f"부서: {self.department}")

        if self.position:
            text_parts.append(f"포지션: {self.position}")

        if self.employment_type:
            text_parts.append(f"고용형태: {self.employment_type}")

        # 상세 설명
        if self.description:
            text_parts.append(f"설명: {self.description}")

        # 태그
        if self.tags:
            text_parts.append(f"태그: {', '.join(self.tags)}")

        # 필수 기술
        if self.required_skills:
            text_parts.append(f"필수기술: {', '.join(self.required_skills)}")

        # 우대 기술
        if self.preferred_skills:
            text_parts.append(f"우대기술: {', '.join(self.preferred_skills)}")

        # 복리후생
        if self.benefits:
            text_parts.append(f"복리후생: {', '.join(self.benefits)}")

        # 학력 요구사항
        if self.education_level:
            text_parts.append(f"학력: {self.education_level}")

        # 연봉 정보
        if self.salary_min and self.salary_max:
            text_parts.append(f"연봉: {self.salary_min}-{self.salary_max}만원")
        elif self.salary_min:
            text_parts.append(f"연봉: {self.salary_min}만원 이상")
        elif self.salary_max:
            text_parts.append(f"연봉: {self.salary_max}만원 이하")

        return " ".join(text_parts)

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """ChromaDB 메타데이터용 딕셔너리 변환 (필터링 및 검색 최적화)"""
        # ChromaDB는 특정 타입만 메타데이터로 지원 (string, int, float, bool)
        metadata = {
            "recruitment_id": self.id,
            "title": self.title,
            "company": self.company,
            "application_deadline": self.applicationDeadline,
            "required_experience": self.requiredExperience,
            "tags_count": len(self.tags),
            "required_skills_count": len(self.required_skills),
            "preferred_skills_count": len(self.preferred_skills),
            "benefits_count": len(self.benefits),
            "has_description": bool(self.description),
            "has_location": bool(self.location),
            "has_salary_info": bool(self.salary_min or self.salary_max),
            "is_active": self.is_active,
            "is_deadline_passed": self.is_deadline_passed(),
            "collection_name": self.collection_name,
            "version": self.version,
            "created_timestamp": (
                int(self.created_at.timestamp()) if self.created_at else 0
            ),
            "updated_timestamp": (
                int(self.updated_at.timestamp()) if self.updated_at else 0
            ),
        }

        # 선택적 문자열 필드들
        if self.location:
            metadata["location"] = self.location
        if self.employment_type:
            metadata["employment_type"] = self.employment_type
        if self.department:
            metadata["department"] = self.department
        if self.position:
            metadata["position"] = self.position
        if self.education_level:
            metadata["education_level"] = self.education_level
        if self.contact_email:
            metadata["contact_email"] = self.contact_email
        if self.contact_phone:
            metadata["contact_phone"] = self.contact_phone
        if self.posting_date:
            metadata["posting_date"] = self.posting_date

        # 연봉 정보
        if self.salary_min:
            metadata["salary_min"] = self.salary_min
        if self.salary_max:
            metadata["salary_max"] = self.salary_max

        # 마감일까지 남은 일수
        days_until = self.days_until_deadline()
        if days_until is not None:
            metadata["days_until_deadline"] = days_until
            metadata["is_deadline_soon"] = self.is_deadline_soon()

        # 태그를 JSON 문자열로 저장 (ChromaDB에서 배열 지원 안함)
        if self.tags:
            metadata["tags_json"] = json.dumps(self.tags, ensure_ascii=False)

        # 필수 기술을 JSON 문자열로 저장
        if self.required_skills:
            metadata["required_skills_json"] = json.dumps(
                self.required_skills, ensure_ascii=False
            )

        # 우대 기술을 JSON 문자열로 저장
        if self.preferred_skills:
            metadata["preferred_skills_json"] = json.dumps(
                self.preferred_skills, ensure_ascii=False
            )

        # 복리후생을 JSON 문자열로 저장
        if self.benefits:
            metadata["benefits_json"] = json.dumps(self.benefits, ensure_ascii=False)

        # 주요 태그들 (최대 5개)
        for i, tag in enumerate(self.tags[:5]):
            metadata[f"tag_{i+1}"] = tag

        # 주요 필수 기술들 (최대 5개)
        for i, skill in enumerate(self.required_skills[:5]):
            metadata[f"required_skill_{i+1}"] = skill

        # 주요 우대 기술들 (최대 3개)
        for i, skill in enumerate(self.preferred_skills[:3]):
            metadata[f"preferred_skill_{i+1}"] = skill

        return metadata

    def to_chroma_document(self) -> Dict[str, Any]:
        """ChromaDB 문서 형태로 변환"""
        return {
            "id": self.generate_document_id(),
            "document": self.to_embedding_text(),
            "metadata": self.to_chroma_metadata(),
        }

    def to_metadata_dict(self) -> Dict[str, Any]:
        """레거시 호환용 - to_chroma_metadata 사용 권장"""
        return self.to_chroma_metadata()

    @classmethod
    def from_json_metadata(cls, json_data: Dict[str, Any]) -> "Recruitment":
        """JSON 메타데이터에서 Recruitment 객체 생성"""
        # 필드명 매핑 (camelCase -> snake_case)
        field_mapping = {
            "applicationDeadline": "applicationDeadline",  # 이미 올바른 형태
            "requiredExperience": "requiredExperience",  # 이미 올바른 형태
            "employmentType": "employment_type",
            "salaryMin": "salary_min",
            "salaryMax": "salary_max",
            "requiredSkills": "required_skills",
            "preferredSkills": "preferred_skills",
            "educationLevel": "education_level",
            "contactEmail": "contact_email",
            "contactPhone": "contact_phone",
            "postingDate": "posting_date",
            "documentId": "document_id",
            "collectionName": "collection_name",
            "createdAt": "created_at",
            "updatedAt": "updated_at",
            "isActive": "is_active",
        }

        # 필드명 변환
        converted_data = {}
        for key, value in json_data.items():
            new_key = field_mapping.get(key, key)
            converted_data[new_key] = value

        return cls(**converted_data)

    @classmethod
    def from_chroma_result(cls, chroma_result: Dict[str, Any]) -> "Recruitment":
        """ChromaDB 검색 결과에서 Recruitment 객체 생성"""
        metadata = chroma_result.get("metadata", {})

        # 기본 필드 복원
        recruitment_data = {
            "id": metadata.get("recruitment_id"),
            "title": metadata.get("title"),
            "company": metadata.get("company"),
            "applicationDeadline": metadata.get("application_deadline"),
            "requiredExperience": metadata.get("required_experience", 0),
            "location": metadata.get("location"),
            "employment_type": metadata.get("employment_type"),
            "department": metadata.get("department"),
            "position": metadata.get("position"),
            "education_level": metadata.get("education_level"),
            "contact_email": metadata.get("contact_email"),
            "contact_phone": metadata.get("contact_phone"),
            "posting_date": metadata.get("posting_date"),
            "salary_min": metadata.get("salary_min"),
            "salary_max": metadata.get("salary_max"),
            "collection_name": metadata.get("collection_name", "recruitments"),
            "version": metadata.get("version", 1),
            "is_active": metadata.get("is_active", True),
        }

        # 태그 복원
        tags_json = metadata.get("tags_json")
        if tags_json:
            try:
                recruitment_data["tags"] = json.loads(tags_json)
            except json.JSONDecodeError:
                recruitment_data["tags"] = []
        else:
            recruitment_data["tags"] = []

        # 필수 기술 복원
        required_skills_json = metadata.get("required_skills_json")
        if required_skills_json:
            try:
                recruitment_data["required_skills"] = json.loads(required_skills_json)
            except json.JSONDecodeError:
                recruitment_data["required_skills"] = []
        else:
            recruitment_data["required_skills"] = []

        # 우대 기술 복원
        preferred_skills_json = metadata.get("preferred_skills_json")
        if preferred_skills_json:
            try:
                recruitment_data["preferred_skills"] = json.loads(preferred_skills_json)
            except json.JSONDecodeError:
                recruitment_data["preferred_skills"] = []
        else:
            recruitment_data["preferred_skills"] = []

        # 복리후생 복원
        benefits_json = metadata.get("benefits_json")
        if benefits_json:
            try:
                recruitment_data["benefits"] = json.loads(benefits_json)
            except json.JSONDecodeError:
                recruitment_data["benefits"] = []
        else:
            recruitment_data["benefits"] = []

        # 생성일시 복원
        created_timestamp = metadata.get("created_timestamp")
        if created_timestamp:
            recruitment_data["created_at"] = datetime.fromtimestamp(created_timestamp)

        # 수정일시 복원
        updated_timestamp = metadata.get("updated_timestamp")
        if updated_timestamp:
            recruitment_data["updated_at"] = datetime.fromtimestamp(updated_timestamp)

        return cls(**recruitment_data)

    def get_similarity_score(self, distance: float) -> float:
        """거리 기반 유사도 점수 계산 (0~1, 1이 가장 유사)"""
        return max(0.0, 1.0 - distance)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return self.dict()

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return self.json(ensure_ascii=False, indent=2)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        # Pydantic v2 호환성
        validate_assignment = True
        use_enum_values = True
        schema_extra = {
            "example": {
                "id": 1001,
                "title": "채용공고",
                "company": "google",
                "applicationDeadline": "2025-02-22",
                "tags": [],
                "requiredExperience": 1,
                "description": "백엔드 개발자 모집",
                "location": "서울특별시",
                "employment_type": "정규직",
                "required_skills": ["Python", "Django"],
                "preferred_skills": ["AWS", "Docker"],
                "benefits": ["4대보험", "연차"],
                "collection_name": "recruitments",
            }
        }


# ChromaDB 특화 유틸리티 함수들
def create_recruitment_from_basic_info(
    id: int,
    title: str,
    company: str,
    application_deadline: str,
    required_experience: int = 0,
    collection_name: str = "recruitments",
) -> Recruitment:
    """기본 정보로 채용공고 생성 (ChromaDB 최적화)"""
    return Recruitment(
        id=id,
        title=title,
        company=company,
        applicationDeadline=application_deadline,
        requiredExperience=required_experience,
        tags=[],
        collection_name=collection_name,
    )


def create_sample_recruitments() -> List[Recruitment]:
    """샘플 채용공고 데이터 생성"""
    sample_data = [
        {
            "id": 1001,
            "title": "백엔드 개발자",
            "company": "구글",
            "applicationDeadline": "2025-03-15",
            "tags": ["python", "django", "aws"],
            "requiredExperience": 3,
            "description": "클라우드 기반 백엔드 시스템 개발",
            "location": "서울 강남구",
            "employment_type": "정규직",
            "department": "개발팀",
            "salary_min": 5000,
            "salary_max": 7000,
            "required_skills": ["Python", "Django", "AWS", "Docker"],
            "preferred_skills": ["Kubernetes", "Redis", "PostgreSQL"],
            "benefits": ["4대보험", "연차", "야근수당", "점심제공"],
            "education_level": "대졸 이상",
        },
        {
            "id": 1002,
            "title": "프론트엔드 개발자",
            "company": "네이버",
            "applicationDeadline": "2025-02-28",
            "tags": ["react", "javascript", "typescript"],
            "requiredExperience": 2,
            "description": "모던 웹 프론트엔드 개발",
            "location": "서울 종로구",
            "employment_type": "정규직",
            "department": "UI/UX팀",
            "salary_min": 4000,
            "salary_max": 6000,
            "required_skills": ["React", "JavaScript", "TypeScript", "HTML/CSS"],
            "preferred_skills": ["Next.js", "Redux", "Sass"],
            "benefits": ["4대보험", "연차", "교육지원", "간식제공"],
            "education_level": "대졸 이상",
        },
        {
            "id": 1003,
            "title": "데이터 분석가",
            "company": "카카오",
            "applicationDeadline": "2025-04-01",
            "tags": ["python", "sql", "machine-learning"],
            "requiredExperience": 1,
            "description": "빅데이터 분석 및 ML 모델 개발",
            "location": "서울 서초구",
            "employment_type": "정규직",
            "department": "데이터팀",
            "salary_min": 4500,
            "salary_max": 6500,
            "required_skills": ["Python", "SQL", "Pandas", "NumPy"],
            "preferred_skills": ["TensorFlow", "PyTorch", "Spark", "Airflow"],
            "benefits": ["4대보험", "연차", "재택근무", "주식옵션"],
            "education_level": "대졸 이상",
        },
    ]

    return [Recruitment.from_json_metadata(data) for data in sample_data]


def create_chroma_query_filter(
    companies: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    skills: Optional[List[str]] = None,
    employment_types: Optional[List[str]] = None,
    active_only: bool = True,
    deadline_not_passed: bool = True,
) -> Dict[str, Any]:
    """ChromaDB 쿼리용 필터 생성"""
    where_clause = {}

    if active_only:
        where_clause["is_active"] = True

    if deadline_not_passed:
        where_clause["is_deadline_passed"] = False

    if companies:
        where_clause["company"] = {"$in": companies}

    if locations:
        where_clause["location"] = {"$in": locations}

    if min_experience is not None:
        where_clause["required_experience"] = {"$gte": min_experience}

    if max_experience is not None:
        if "required_experience" in where_clause:
            where_clause["required_experience"]["$lte"] = max_experience
        else:
            where_clause["required_experience"] = {"$lte": max_experience}

    if employment_types:
        where_clause["employment_type"] = {"$in": employment_types}

    # 스킬 필터링은 개별 skill 필드들을 체크
    if skills:
        skill_conditions = []
        for i in range(1, 6):  # required_skill_1~5 체크
            skill_conditions.extend(
                [{f"required_skill_{i}": skill} for skill in skills]
            )
        for i in range(1, 4):  # preferred_skill_1~3 체크
            skill_conditions.extend(
                [{f"preferred_skill_{i}": skill} for skill in skills]
            )

        if skill_conditions:
            where_clause["$or"] = skill_conditions

    return where_clause


def validate_recruitment_metadata(metadata: Dict[str, Any]) -> bool:
    """Recruitment 메타데이터 유효성 검사"""
    required_fields = [
        "recruitment_id",
        "title",
        "company",
        "application_deadline",
        "required_experience",
    ]

    for field in required_fields:
        if field not in metadata:
            return False

    # 타입 검사
    if not isinstance(metadata["recruitment_id"], int):
        return False
    if not isinstance(metadata["title"], str):
        return False
    if not isinstance(metadata["company"], str):
        return False
    if not isinstance(metadata["required_experience"], int):
        return False

    # 날짜 형식 검사
    try:
        datetime.strptime(metadata["application_deadline"], "%Y-%m-%d")
    except (ValueError, TypeError):
        return False

    return True


# Recruitment 전용 ChromaDB 관리자
class RecruitmentChromaManager:
    """채용공고 전용 ChromaDB 관리자"""

    def __init__(
        self,
        collection_name: str = "recruitments",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "jhgan/ko-sbert-nli",
    ) -> None:
        """
        채용공고 ChromaDB 관리자 초기화

        Args:
            collection_name: 컬렉션 이름
            persist_directory: 데이터 저장 디렉토리
            embedding_model: 임베딩 모델명 (한국어 최적화)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # 한국어 임베딩 모델 초기화 (fallback 포함)
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"한국어 임베딩 모델 로드 성공: {embedding_model}")
        except Exception as e:
            logger.warning(f"한국어 모델 로드 실패, 기본 모델 사용: {e}")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 컬렉션 초기화
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """컬렉션 초기화 또는 기존 컬렉션 로드"""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "채용공고 벡터 저장소"},
            )
            logger.info(f"채용공고 컬렉션 '{self.collection_name}' 초기화 완료")
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {str(e)}")
            raise

    def add_recruitment(self, recruitment: Recruitment) -> bool:
        """단일 채용공고 추가"""
        try:
            return self.add_recruitments([recruitment])
        except Exception as e:
            logger.error(f"채용공고 추가 실패 (ID: {recruitment.id}): {str(e)}")
            return False

    def add_recruitments(self, recruitments: List[Recruitment]) -> bool:
        """배치로 채용공고들 추가"""
        try:
            if not recruitments:
                logger.warning("추가할 채용공고가 없습니다")
                return True

            # 임베딩용 텍스트 생성
            documents = [r.to_embedding_text() for r in recruitments]

            # ChromaDB 메타데이터 변환
            metadatas = [r.to_chroma_metadata() for r in recruitments]

            # ID 생성 (기존 ID 기반)
            ids = [f"recruitment_{r.id}" for r in recruitments]

            # 임베딩 생성
            embeddings = self._generate_embeddings(documents)

            # 컬렉션에 추가
            self.collection.add(
                embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids
            )

            logger.info(f"{len(recruitments)}개 채용공고 추가 완료")
            return True

        except Exception as e:
            logger.error(f"배치 채용공고 추가 실패: {str(e)}")
            return False

    def search_recruitments(
        self, query: str, n_results: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """채용공고 검색"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._generate_embeddings([query])[0]

            # ChromaDB 검색
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results, where=filters
            )

            # 결과 변환
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    result_data = {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": (
                            results["distances"][0][i] if results["distances"] else None
                        ),
                        "similarity_score": (
                            1 - results["distances"][0][i]
                            if results["distances"]
                            else None
                        ),
                    }

                    # Recruitment 객체로 복원
                    try:
                        recruitment = Recruitment.from_chroma_result(result_data)
                        result_data["recruitment"] = recruitment
                    except Exception as e:
                        logger.warning(f"채용공고 객체 복원 실패: {e}")

                    formatted_results.append(result_data)

            logger.info(f"채용공고 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results

        except Exception as e:
            logger.error(f"채용공고 검색 실패: {str(e)}")
            return []

    def get_recruitment_by_id(self, recruitment_id: int) -> Optional[Recruitment]:
        """ID로 채용공고 조회"""
        try:
            chroma_id = f"recruitment_{recruitment_id}"
            results = self.collection.get(ids=[chroma_id])

            if results["ids"]:
                result_data = {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0],
                }
                return Recruitment.from_chroma_result(result_data)

            return None

        except Exception as e:
            logger.error(f"채용공고 조회 실패 (ID: {recruitment_id}): {str(e)}")
            return None

    def update_recruitment(self, recruitment: Recruitment) -> bool:
        """채용공고 업데이트"""
        try:
            chroma_id = f"recruitment_{recruitment.id}"

            # 기존 데이터 확인
            existing = self.collection.get(ids=[chroma_id])
            if not existing["ids"]:
                logger.warning(
                    f"업데이트할 채용공고를 찾을 수 없습니다 (ID: {recruitment.id})"
                )
                return False

            # 새 데이터로 업데이트
            document = recruitment.to_embedding_text()
            metadata = recruitment.to_chroma_metadata()
            embedding = self._generate_embeddings([document])[0]

            self.collection.update(
                ids=[chroma_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )

            logger.info(f"채용공고 업데이트 완료 (ID: {recruitment.id})")
            return True

        except Exception as e:
            logger.error(f"채용공고 업데이트 실패 (ID: {recruitment.id}): {str(e)}")
            return False

    def delete_recruitment(self, recruitment_id: int) -> bool:
        """채용공고 삭제"""
        try:
            chroma_id = f"recruitment_{recruitment_id}"
            self.collection.delete(ids=[chroma_id])

            logger.info(f"채용공고 삭제 완료 (ID: {recruitment_id})")
            return True

        except Exception as e:
            logger.error(f"채용공고 삭제 실패 (ID: {recruitment_id}): {str(e)}")
            return False

    def search_by_company(
        self, company: str, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """회사명으로 채용공고 검색"""
        filters = {"company": {"$eq": company}}
        return self.search_recruitments("", n_results=n_results, filters=filters)

    def search_by_experience(
        self, min_exp: int, max_exp: int, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """경력 범위로 채용공고 검색"""
        filters = {"required_experience": {"$gte": min_exp, "$lte": max_exp}}
        return self.search_recruitments("", n_results=n_results, filters=filters)

    def search_active_recruitments(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """활성 채용공고 검색 (마감일이 지나지 않은 것들)"""
        today = datetime.now().strftime("%Y-%m-%d")
        filters = {"application_deadline": {"$gte": today}}
        return self.search_recruitments("", n_results=n_results, filters=filters)

    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_recruitments": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {str(e)}")
            return {}

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise

    @contextmanager
    def batch_operation(self):
        """배치 작업을 위한 컨텍스트 매니저"""
        logger.info("배치 작업 시작")
        try:
            yield self
        except Exception as e:
            logger.error(f"배치 작업 중 오류 발생: {str(e)}")
            raise
        finally:
            logger.info("배치 작업 완료")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"컨텍스트 매니저 종료 중 오류: {exc_val}")
        return False


# 편의 함수들
def create_recruitment_manager(
    collection_name: str = "recruitments", persist_directory: str = "./chroma_db"
) -> RecruitmentChromaManager:
    """채용공고 관리자 생성 편의 함수"""
    return RecruitmentChromaManager(
        collection_name=collection_name, persist_directory=persist_directory
    )


def search_recruitments_by_keywords(
    manager: RecruitmentChromaManager, keywords: List[str], n_results: int = 10
) -> List[Dict[str, Any]]:
    """키워드 리스트로 채용공고 검색"""
    query = " ".join(keywords)
    return manager.search_recruitments(query, n_results=n_results)
