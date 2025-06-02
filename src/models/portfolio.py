"""
ChromaDB 최적화 Portfolio 스키마 정의

ChromaDB 벡터 데이터베이스에 최적화된 사용자 포트폴리오 모델입니다.
- 메타데이터: ChromaDB의 메타데이터 제약사항(string, int, float, bool만 지원) 준수
- 임베딩 텍스트: 의미있는 검색을 위한 텍스트 생성
- 문서 구조: ChromaDB의 document, metadata, id 구조에 맞춤
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import json
import hashlib


class EducationItem(BaseModel):
    """교육 이력 항목 모델 - ChromaDB 메타데이터 최적화"""

    institution: str = Field(..., description="교육 기관명")
    degree: Optional[str] = Field(None, description="학위/자격증명")
    field_of_study: Optional[str] = Field(None, description="전공/분야")
    start_date: Optional[str] = Field(None, description="시작일 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료일 (YYYY-MM-DD)")
    is_current: bool = Field(False, description="현재 재학/수강 중 여부")
    description: Optional[str] = Field(None, description="교육 내용 설명")

    def to_searchable_text(self) -> str:
        """검색 가능한 텍스트로 변환 (임베딩용)"""
        parts = [
            self.institution,
            self.degree or "",
            self.field_of_study or "",
            self.description or "",
        ]
        return " ".join(filter(None, parts))

    def to_metadata_dict(self) -> Dict[str, Any]:
        """ChromaDB 메타데이터용 딕셔너리 변환"""
        return {
            "institution": self.institution,
            "degree": self.degree,
            "field_of_study": self.field_of_study,
            "is_current": self.is_current,
            "start_year": self.start_date[:4] if self.start_date else None,
            "end_year": self.end_date[:4] if self.end_date else None,
        }

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Portfolio(BaseModel):
    """ChromaDB용 사용자 포트폴리오 메타데이터 모델"""

    # 필수 필드들 (원본 JSON 구조)
    user_id: int = Field(..., description="사용자 고유 ID")
    user_name: str = Field(..., min_length=1, max_length=100, description="사용자 이름")
    age: int = Field(..., ge=0, le=150, description="나이")
    education: List[EducationItem] = Field(
        default_factory=list, description="교육 이력 목록"
    )

    # ChromaDB 최적화를 위한 추가 필드들
    email: Optional[str] = Field(None, description="이메일 주소")
    phone: Optional[str] = Field(None, description="전화번호")
    location: Optional[str] = Field(None, description="거주지")
    bio: Optional[str] = Field(None, max_length=1000, description="자기소개")
    skills: List[str] = Field(default_factory=list, description="보유 기술/스킬")
    experience: List[Dict[str, Any]] = Field(
        default_factory=list, description="경력 사항"
    )
    projects: List[Dict[str, Any]] = Field(
        default_factory=list, description="프로젝트 이력"
    )

    # ChromaDB 메타데이터
    document_id: Optional[str] = Field(None, description="ChromaDB 문서 ID")
    collection_name: str = Field(default="portfolios", description="ChromaDB 컬렉션명")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="생성일시"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="수정일시"
    )
    version: int = Field(default=1, description="스키마 버전")

    @validator("email")
    def validate_email(cls, v):
        """이메일 형식 검증"""
        if v is not None and "@" not in v:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v

    @validator("user_name")
    def validate_user_name(cls, v):
        """사용자 이름 검증"""
        if not v.strip():
            raise ValueError("사용자 이름은 비어있을 수 없습니다")
        return v.strip()

    @validator("skills")
    def validate_skills(cls, v):
        """스킬 목록 정규화"""
        return [skill.strip() for skill in v if skill.strip()]

    def add_education(self, education_item: EducationItem) -> None:
        """교육 이력 추가"""
        self.education.append(education_item)
        self.updated_at = datetime.now()

    def add_skill(self, skill: str) -> None:
        """스킬 추가"""
        if skill and skill not in self.skills:
            self.skills.append(skill.strip())
            self.updated_at = datetime.now()

    def remove_skill(self, skill: str) -> None:
        """스킬 제거"""
        if skill in self.skills:
            self.skills.remove(skill)
            self.updated_at = datetime.now()

    def update_bio(self, bio: str) -> None:
        """자기소개 업데이트"""
        self.bio = bio
        self.updated_at = datetime.now()

    def generate_document_id(self) -> str:
        """ChromaDB용 문서 ID 생성"""
        if not self.document_id:
            self.document_id = (
                f"portfolio_{self.user_id}_{int(self.created_at.timestamp())}"
            )
        return self.document_id

    def to_embedding_text(self) -> str:
        """임베딩 생성용 텍스트 변환"""
        text_parts = []

        # 기본 정보
        text_parts.append(f"사용자: {self.user_name}")
        text_parts.append(f"나이: {self.age}세")

        if self.location:
            text_parts.append(f"거주지: {self.location}")

        # 자기소개
        if self.bio:
            text_parts.append(f"소개: {self.bio}")

        # 스킬
        if self.skills:
            text_parts.append(f"기술: {', '.join(self.skills)}")

        # 교육 이력
        for edu in self.education:
            text_parts.append(f"교육: {edu.to_searchable_text()}")

        # 경력
        for exp in self.experience:
            if isinstance(exp, dict):
                company = exp.get("company", "")
                position = exp.get("position", "")
                description = exp.get("description", "")
                text_parts.append(f"경력: {company} {position} {description}")

        # 프로젝트
        for proj in self.projects:
            if isinstance(proj, dict):
                name = proj.get("name", "")
                description = proj.get("description", "")
                text_parts.append(f"프로젝트: {name} {description}")

        return " ".join(text_parts)

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """ChromaDB 메타데이터용 딕셔너리 변환 (필터링 및 검색 최적화)"""
        # ChromaDB는 특정 타입만 메타데이터로 지원 (string, int, float, bool)
        metadata = {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "age": self.age,
            "skills_count": len(self.skills),
            "education_count": len(self.education),
            "experience_count": len(self.experience),
            "projects_count": len(self.projects),
            "has_bio": bool(self.bio),
            "has_email": bool(self.email),
            "has_location": bool(self.location),
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
        if self.email:
            metadata["email"] = self.email
        if self.location:
            metadata["location"] = self.location
        if self.phone:
            metadata["phone"] = self.phone

        # 스킬을 JSON 문자열로 저장 (ChromaDB에서 배열 지원 안함)
        if self.skills:
            metadata["skills_json"] = json.dumps(self.skills, ensure_ascii=False)

        # 주요 교육 기관들 (최대 3개)
        education_institutions = [edu.institution for edu in self.education[:3]]
        for i, institution in enumerate(education_institutions):
            metadata[f"education_institution_{i+1}"] = institution

        # 주요 스킬들 (최대 5개)
        for i, skill in enumerate(self.skills[:5]):
            metadata[f"skill_{i+1}"] = skill

        return metadata

    def to_chroma_document(self) -> Dict[str, Any]:
        """ChromaDB 문서 형태로 변환"""
        return {
            "id": self.generate_document_id(),
            "document": self.to_embedding_text(),
            "metadata": self.to_chroma_metadata(),
        }

    @classmethod
    def from_json_metadata(cls, json_data: Dict[str, Any]) -> "Portfolio":
        """JSON 메타데이터에서 Portfolio 객체 생성"""
        return cls(**json_data)

    @classmethod
    def from_chroma_result(cls, chroma_result: Dict[str, Any]) -> "Portfolio":
        """ChromaDB 검색 결과에서 Portfolio 객체 생성"""
        metadata = chroma_result.get("metadata", {})

        # 기본 필드 복원
        portfolio_data = {
            "user_id": metadata.get("user_id"),
            "user_name": metadata.get("user_name"),
            "age": metadata.get("age"),
            "email": metadata.get("email"),
            "location": metadata.get("location"),
            "phone": metadata.get("phone"),
            "collection_name": metadata.get("collection_name", "portfolios"),
            "version": metadata.get("version", 1),
        }

        # 스킬 복원
        skills_json = metadata.get("skills_json")
        if skills_json:
            try:
                portfolio_data["skills"] = json.loads(skills_json)
            except json.JSONDecodeError:
                portfolio_data["skills"] = []
        else:
            portfolio_data["skills"] = []

        # 교육 이력 복원 (기본 정보만)
        education_items = []
        for i in range(1, 4):  # education_institution_1~3
            institution = metadata.get(f"education_institution_{i}")
            if institution:
                education_items.append(EducationItem(institution=institution))
        portfolio_data["education"] = education_items

        # ChromaDB 문서 ID 설정
        portfolio_data["document_id"] = chroma_result.get("id")

        # 타임스탬프 복원
        created_ts = metadata.get("created_timestamp")
        updated_ts = metadata.get("updated_timestamp")

        if created_ts:
            portfolio_data["created_at"] = datetime.fromtimestamp(created_ts)
        if updated_ts:
            portfolio_data["updated_at"] = datetime.fromtimestamp(updated_ts)

        return cls(**portfolio_data)

    def to_metadata_dict(self) -> Dict[str, Any]:
        """레거시 호환용 - to_chroma_metadata 사용 권장"""
        return self.to_chroma_metadata()

    class Config:
        """Pydantic 설정"""

        json_encoders = {datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "user_name": "asdf",
                "age": 23,
                "education": [],
                "email": "asdf@example.com",
                "location": "Seoul, Korea",
                "bio": "안녕하세요. 개발자 지망생입니다.",
                "skills": ["Python", "JavaScript", "React"],
                "experience": [],
                "projects": [],
                "collection_name": "portfolios",
            }
        }


# ChromaDB 특화 유틸리티 함수들
def create_portfolio_from_basic_info(
    user_id: int, user_name: str, age: int, collection_name: str = "portfolios"
) -> Portfolio:
    """기본 정보로 포트폴리오 생성 (ChromaDB 최적화)"""
    return Portfolio(
        user_id=user_id,
        user_name=user_name,
        age=age,
        education=[],
        collection_name=collection_name,
    )


def validate_portfolio_metadata(metadata: Dict[str, Any]) -> bool:
    """포트폴리오 메타데이터 유효성 검사"""
    try:
        Portfolio.from_json_metadata(metadata)
        return True
    except Exception:
        return False


def create_chroma_query_filter(
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    skills: Optional[List[str]] = None,
    location: Optional[str] = None,
    min_experience_count: Optional[int] = None,
) -> Dict[str, Any]:
    """ChromaDB 쿼리용 필터 생성"""
    filter_conditions = {}

    if min_age is not None:
        filter_conditions["age"] = {"$gte": min_age}
    if max_age is not None:
        if "age" in filter_conditions:
            filter_conditions["age"]["$lte"] = max_age
        else:
            filter_conditions["age"] = {"$lte": max_age}

    if location:
        filter_conditions["location"] = {"$eq": location}

    if min_experience_count is not None:
        filter_conditions["experience_count"] = {"$gte": min_experience_count}

    if skills:
        # 스킬 기반 필터링은 개별 skill_1, skill_2 등을 확인
        skill_filters = []
        for skill in skills:
            for i in range(1, 6):  # skill_1 ~ skill_5
                skill_filters.append({f"skill_{i}": {"$eq": skill}})

        if skill_filters:
            filter_conditions["$or"] = skill_filters

    return filter_conditions


# 샘플 데이터 생성 함수 (ChromaDB 최적화)
def create_sample_portfolio() -> Portfolio:
    """ChromaDB용 샘플 포트폴리오 데이터 생성"""
    education_item = EducationItem(
        institution="서울대학교",
        degree="학사",
        field_of_study="컴퓨터공학",
        start_date="2020-03-01",
        end_date="2024-02-29",
        is_current=False,
        description="컴퓨터과학 및 소프트웨어 엔지니어링 전공",
    )

    portfolio = Portfolio(
        user_id=1,
        user_name="김개발",
        age=25,
        email="kim.dev@example.com",
        location="서울특별시",
        bio="풀스택 개발자를 꿈꾸는 신입 개발자입니다. React와 Node.js를 주로 사용하며, 클라우드 기반 서비스 개발에 관심이 많습니다.",
        skills=["Python", "JavaScript", "React", "Node.js", "Docker", "AWS"],
        education=[education_item],
        experience=[
            {
                "company": "테크 스타트업",
                "position": "인턴 개발자",
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "description": "웹 애플리케이션 프론트엔드 개발",
            }
        ],
        projects=[
            {
                "name": "개인 포트폴리오 웹사이트",
                "description": "React와 Node.js로 구축한 반응형 포트폴리오 사이트",
                "technologies": ["React", "Node.js", "MongoDB", "AWS"],
                "url": "https://github.com/kimdev/portfolio",
            }
        ],
        collection_name="portfolios",
    )

    return portfolio


def create_multiple_sample_portfolios() -> List[Portfolio]:
    """테스트용 다중 포트폴리오 생성"""
    portfolios = []

    # 포트폴리오 1: 프론트엔드 개발자
    portfolio1 = Portfolio(
        user_id=1,
        user_name="김프론트",
        age=25,
        email="frontend@example.com",
        location="서울특별시",
        bio="사용자 경험을 중시하는 프론트엔드 개발자입니다.",
        skills=["JavaScript", "React", "Vue.js", "TypeScript", "CSS"],
        education=[
            EducationItem(
                institution="프론트엔드대학교",
                degree="학사",
                field_of_study="웹개발학과",
            )
        ],
    )

    # 포트폴리오 2: 백엔드 개발자
    portfolio2 = Portfolio(
        user_id=2,
        user_name="이백엔드",
        age=28,
        email="backend@example.com",
        location="부산광역시",
        bio="확장 가능한 서버 아키텍처 설계에 관심이 많습니다.",
        skills=["Python", "Django", "PostgreSQL", "Redis", "Kubernetes"],
        education=[
            EducationItem(
                institution="백엔드대학교", degree="석사", field_of_study="컴퓨터공학"
            )
        ],
    )

    # 포트폴리오 3: 풀스택 개발자
    portfolio3 = Portfolio(
        user_id=3,
        user_name="박풀스택",
        age=30,
        email="fullstack@example.com",
        location="대구광역시",
        bio="프론트엔드부터 백엔드까지 전 영역을 다루는 개발자입니다.",
        skills=["JavaScript", "Python", "React", "Django", "Docker", "AWS"],
        education=[
            EducationItem(
                institution="종합대학교", degree="학사", field_of_study="소프트웨어공학"
            )
        ],
    )

    portfolios.extend([portfolio1, portfolio2, portfolio3])
    return portfolios
