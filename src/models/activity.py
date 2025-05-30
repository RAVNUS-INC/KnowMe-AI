"""
ChromaDB 최적화 Activity 스키마 정의

ChromaDB 벡터 데이터베이스에 최적화된 대외활동 모델입니다.
- 메타데이터: ChromaDB의 메타데이터 제약사항(string, int, float, bool만 지원) 준수
- 임베딩 텍스트: 의미있는 검색을 위한 텍스트 생성
- 문서 구조: ChromaDB의 document, metadata, id 구조에 맞춤

기본 JSON 구조:
{
    "postId": 1001,
    "category": "대외활동",
    "title": "hello",
    "company": "seoul",
    "activityDuration": 3,
    "activityField": "창업"
}
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
import json
import hashlib


class Activity(BaseModel):
    """ChromaDB용 대외활동 메타데이터 모델"""

    # 필수 필드들 (원본 JSON 구조)
    postId: int = Field(..., description="대외활동 게시글 고유 ID")
    category: str = Field(..., min_length=1, max_length=50, description="활동 카테고리")
    title: str = Field(..., min_length=1, max_length=200, description="활동 제목")
    company: str = Field(..., min_length=1, max_length=100, description="주관사/기관명")
    activityDuration: int = Field(..., ge=0, le=365, description="활동 기간 (일)")
    activityField: str = Field(
        ..., min_length=1, max_length=50, description="활동 분야"
    )

    # ChromaDB 최적화를 위한 추가 필드들
    description: Optional[str] = Field(
        None, max_length=5000, description="활동 상세 설명"
    )
    location: Optional[str] = Field(None, max_length=100, description="활동 지역")
    target_audience: Optional[str] = Field(
        None, max_length=100, description="참여 대상"
    )
    application_start_date: Optional[str] = Field(
        None, description="지원 시작일 (YYYY-MM-DD)"
    )
    application_end_date: Optional[str] = Field(
        None, description="지원 마감일 (YYYY-MM-DD)"
    )
    activity_start_date: Optional[str] = Field(
        None, description="활동 시작일 (YYYY-MM-DD)"
    )
    activity_end_date: Optional[str] = Field(
        None, description="활동 종료일 (YYYY-MM-DD)"
    )
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    required_qualifications: List[str] = Field(
        default_factory=list, description="참여 자격 요건"
    )
    benefits: List[str] = Field(default_factory=list, description="활동 혜택")
    skills_gained: List[str] = Field(
        default_factory=list, description="습득 가능한 스킬"
    )
    max_participants: Optional[int] = Field(None, ge=0, description="최대 참여 인원")
    application_fee: Optional[int] = Field(None, ge=0, description="지원비 (원)")
    scholarship_amount: Optional[int] = Field(
        None, ge=0, description="장학금/지원금 (원)"
    )
    contact_email: Optional[str] = Field(None, description="문의 이메일")
    contact_phone: Optional[str] = Field(None, description="문의 전화번호")
    website_url: Optional[str] = Field(None, description="웹사이트 URL")
    difficulty_level: Optional[str] = Field(None, description="난이도 (초급/중급/고급)")
    is_online: bool = Field(default=False, description="온라인 활동 여부")
    is_paid: bool = Field(default=False, description="유료 활동 여부")
    is_certificate_provided: bool = Field(default=False, description="수료증 제공 여부")

    # ChromaDB 메타데이터
    document_id: Optional[str] = Field(None, description="ChromaDB 문서 ID")
    collection_name: str = Field(default="activities", description="ChromaDB 컬렉션명")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="생성일시"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="수정일시"
    )
    version: int = Field(default=1, description="스키마 버전")
    is_active: bool = Field(default=True, description="활성 상태")

    @validator(
        "application_start_date",
        "application_end_date",
        "activity_start_date",
        "activity_end_date",
    )
    def validate_date_format(cls, v):
        """날짜 형식 검증 (YYYY-MM-DD)"""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다")
        return v

    @validator("category")
    def validate_category(cls, v):
        """카테고리 검증"""
        valid_categories = [
            "대외활동",
            "공모전",
            "인턴십",
            "봉사활동",
            "교육프로그램",
            "워크숍",
            "세미나",
            "해커톤",
            "스터디",
            "멘토링",
            "기타",
        ]
        if v not in valid_categories:
            # 검증 실패해도 값을 그대로 반환 (유연성을 위해)
            pass
        return v

    @validator("activityField")
    def validate_activity_field(cls, v):
        """활동 분야 검증"""
        valid_fields = [
            "창업",
            "IT/개발",
            "마케팅",
            "디자인",
            "금융",
            "컨설팅",
            "교육",
            "의료",
            "법률",
            "언론",
            "문화예술",
            "환경",
            "사회공헌",
            "글로벌",
            "기타",
        ]
        if v not in valid_fields:
            # 검증 실패해도 값을 그대로 반환 (유연성을 위해)
            pass
        return v

    class Config:
        """Pydantic 설정"""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "postId": 1001,
                "category": "대외활동",
                "title": "스타트업 인큐베이팅 프로그램",
                "company": "서울창업허브",
                "activityDuration": 90,
                "activityField": "창업",
                "description": "스타트업 창업을 위한 3개월 인큐베이팅 프로그램",
                "location": "서울 강남구",
                "target_audience": "대학생, 청년창업자",
                "tags": ["창업", "스타트업", "인큐베이팅", "멘토링"],
                "benefits": ["창업교육", "멘토링", "네트워킹", "사무공간 제공"],
                "max_participants": 20,
                "scholarship_amount": 1000000,
                "is_certificate_provided": True,
            }
        }

    def add_tag(self, tag: str) -> None:
        """태그 추가"""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """태그 제거"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def add_benefit(self, benefit: str) -> None:
        """혜택 추가"""
        if benefit and benefit not in self.benefits:
            self.benefits.append(benefit)
            self.updated_at = datetime.now()

    def add_skill(self, skill: str) -> None:
        """습득 스킬 추가"""
        if skill and skill not in self.skills_gained:
            self.skills_gained.append(skill)
            self.updated_at = datetime.now()

    def days_until_application_deadline(self) -> Optional[int]:
        """지원 마감일까지 남은 일수"""
        if not self.application_end_date:
            return None

        try:
            deadline = datetime.strptime(self.application_end_date, "%Y-%m-%d").date()
            today = date.today()
            delta = deadline - today
            return delta.days
        except ValueError:
            return None

    def days_until_activity_start(self) -> Optional[int]:
        """활동 시작일까지 남은 일수"""
        if not self.activity_start_date:
            return None

        try:
            start_date = datetime.strptime(self.activity_start_date, "%Y-%m-%d").date()
            today = date.today()
            delta = start_date - today
            return delta.days
        except ValueError:
            return None

    def is_application_deadline_passed(self) -> bool:
        """지원 마감일이 지났는지 확인"""
        days_left = self.days_until_application_deadline()
        return days_left is not None and days_left < 0

    def is_activity_ongoing(self) -> bool:
        """활동이 진행 중인지 확인"""
        if not self.activity_start_date or not self.activity_end_date:
            return False

        try:
            start_date = datetime.strptime(self.activity_start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.activity_end_date, "%Y-%m-%d").date()
            today = date.today()
            return start_date <= today <= end_date
        except ValueError:
            return False

    def get_activity_duration_weeks(self) -> float:
        """활동 기간을 주 단위로 반환"""
        return self.activityDuration / 7.0

    def get_activity_duration_months(self) -> float:
        """활동 기간을 월 단위로 반환"""
        return self.activityDuration / 30.0

    def to_embedding_text(self) -> str:
        """ChromaDB 임베딩을 위한 텍스트 생성"""
        parts = []

        # 기본 정보
        parts.append(f"제목: {self.title}")
        parts.append(f"카테고리: {self.category}")
        parts.append(f"주관사: {self.company}")
        parts.append(f"활동분야: {self.activityField}")
        parts.append(f"활동기간: {self.activityDuration}일")

        # 상세 정보
        if self.description:
            parts.append(f"설명: {self.description}")

        if self.location:
            parts.append(f"지역: {self.location}")

        if self.target_audience:
            parts.append(f"참여대상: {self.target_audience}")

        # 태그
        if self.tags:
            parts.append(f"태그: {', '.join(self.tags)}")

        # 자격 요건
        if self.required_qualifications:
            parts.append(f"자격요건: {', '.join(self.required_qualifications)}")

        # 혜택
        if self.benefits:
            parts.append(f"혜택: {', '.join(self.benefits)}")

        # 습득 스킬
        if self.skills_gained:
            parts.append(f"습득스킬: {', '.join(self.skills_gained)}")

        # 활동 특성
        activity_type = []
        if self.is_online:
            activity_type.append("온라인")
        if self.is_paid:
            activity_type.append("유료")
        if self.is_certificate_provided:
            activity_type.append("수료증제공")

        if activity_type:
            parts.append(f"특성: {', '.join(activity_type)}")

        # 난이도
        if self.difficulty_level:
            parts.append(f"난이도: {self.difficulty_level}")

        # 지원금/장학금
        if self.scholarship_amount and self.scholarship_amount > 0:
            parts.append(f"지원금: {self.scholarship_amount:,}원")

        return " | ".join(parts)

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """ChromaDB 메타데이터 형식으로 변환"""
        metadata = {
            # 기본 필드들 (snake_case로 변환)
            "post_id": self.postId,
            "category": self.category,
            "title": self.title,
            "company": self.company,
            "activity_duration": self.activityDuration,
            "activity_field": self.activityField,
            # 추가 메타데이터
            "collection_name": self.collection_name,
            "version": self.version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # 선택적 필드들 (값이 있는 경우만 추가)
        if self.location:
            metadata["location"] = self.location

        if self.target_audience:
            metadata["target_audience"] = self.target_audience

        if self.application_end_date:
            metadata["application_end_date"] = self.application_end_date

        if self.activity_start_date:
            metadata["activity_start_date"] = self.activity_start_date

        if self.activity_end_date:
            metadata["activity_end_date"] = self.activity_end_date

        if self.max_participants is not None:
            metadata["max_participants"] = self.max_participants

        if self.application_fee is not None:
            metadata["application_fee"] = self.application_fee

        if self.scholarship_amount is not None:
            metadata["scholarship_amount"] = self.scholarship_amount

        if self.difficulty_level:
            metadata["difficulty_level"] = self.difficulty_level

        # 불린 필드들
        metadata["is_online"] = self.is_online
        metadata["is_paid"] = self.is_paid
        metadata["is_certificate_provided"] = self.is_certificate_provided

        # 리스트 필드들을 JSON 문자열로 변환 (ChromaDB 제약사항)
        if self.tags:
            metadata["tags_json"] = json.dumps(self.tags, ensure_ascii=False)

        if self.required_qualifications:
            metadata["required_qualifications_json"] = json.dumps(
                self.required_qualifications, ensure_ascii=False
            )

        if self.benefits:
            metadata["benefits_json"] = json.dumps(self.benefits, ensure_ascii=False)

        if self.skills_gained:
            metadata["skills_gained_json"] = json.dumps(
                self.skills_gained, ensure_ascii=False
            )

        return metadata

    @classmethod
    def from_chroma_result(cls, result: Dict[str, Any]) -> "Activity":
        """ChromaDB 검색 결과에서 Activity 객체 생성"""
        metadata = result.get("metadata", {})

        # JSON 문자열 필드들을 리스트로 복원
        tags = []
        if "tags_json" in metadata:
            try:
                tags = json.loads(metadata["tags_json"])
            except json.JSONDecodeError:
                tags = []

        required_qualifications = []
        if "required_qualifications_json" in metadata:
            try:
                required_qualifications = json.loads(
                    metadata["required_qualifications_json"]
                )
            except json.JSONDecodeError:
                required_qualifications = []

        benefits = []
        if "benefits_json" in metadata:
            try:
                benefits = json.loads(metadata["benefits_json"])
            except json.JSONDecodeError:
                benefits = []

        skills_gained = []
        if "skills_gained_json" in metadata:
            try:
                skills_gained = json.loads(metadata["skills_gained_json"])
            except json.JSONDecodeError:
                skills_gained = []

        # Activity 객체 생성
        activity_data = {
            # camelCase로 변환
            "postId": metadata.get("post_id"),
            "category": metadata.get("category"),
            "title": metadata.get("title"),
            "company": metadata.get("company"),
            "activityDuration": metadata.get("activity_duration"),
            "activityField": metadata.get("activity_field"),
            # 추가 필드들
            "location": metadata.get("location"),
            "target_audience": metadata.get("target_audience"),
            "application_end_date": metadata.get("application_end_date"),
            "activity_start_date": metadata.get("activity_start_date"),
            "activity_end_date": metadata.get("activity_end_date"),
            "max_participants": metadata.get("max_participants"),
            "application_fee": metadata.get("application_fee"),
            "scholarship_amount": metadata.get("scholarship_amount"),
            "difficulty_level": metadata.get("difficulty_level"),
            "is_online": metadata.get("is_online", False),
            "is_paid": metadata.get("is_paid", False),
            "is_certificate_provided": metadata.get("is_certificate_provided", False),
            # 리스트 필드들
            "tags": tags,
            "required_qualifications": required_qualifications,
            "benefits": benefits,
            "skills_gained": skills_gained,
            # 메타데이터
            "collection_name": metadata.get("collection_name", "activities"),
            "version": metadata.get("version", 1),
            "is_active": metadata.get("is_active", True),
            "document_id": result.get("id"),
        }

        # 날짜 필드들 처리
        if "created_at" in metadata:
            try:
                activity_data["created_at"] = datetime.fromisoformat(
                    metadata["created_at"]
                )
            except (ValueError, TypeError):
                activity_data["created_at"] = datetime.now()

        if "updated_at" in metadata:
            try:
                activity_data["updated_at"] = datetime.fromisoformat(
                    metadata["updated_at"]
                )
            except (ValueError, TypeError):
                activity_data["updated_at"] = datetime.now()

        return cls(**activity_data)

    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]) -> "Activity":
        """JSON 딕셔너리에서 Activity 객체 생성"""
        return cls(**data)

    def get_similarity_score(self, distance: float) -> float:
        """ChromaDB 거리를 유사도 점수로 변환 (0-1, 높을수록 유사)"""
        return max(0.0, min(1.0, 1.0 - distance))

    def get_document_hash(self) -> str:
        """문서 해시값 생성 (중복 검사용)"""
        content = f"{self.postId}_{self.title}_{self.company}_{self.activityField}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()


# 유틸리티 함수들
def create_sample_activities(count: int = 10) -> List[Activity]:
    """샘플 대외활동 데이터 생성"""
    from datetime import datetime, timedelta
    import random

    categories = [
        "대외활동",
        "공모전",
        "인턴십",
        "봉사활동",
        "교육프로그램",
        "워크숍",
        "해커톤",
    ]
    fields = [
        "창업",
        "IT/개발",
        "마케팅",
        "디자인",
        "금융",
        "컨설팅",
        "교육",
        "사회공헌",
    ]
    companies = [
        "서울창업허브",
        "네이버",
        "카카오",
        "삼성",
        "LG",
        "현대",
        "SK",
        "한국과학기술원",
    ]
    locations = ["서울", "부산", "대구", "대전", "광주", "인천", "울산", "경기"]

    activities = []
    base_date = datetime.now()

    for i in range(count):
        post_id = 2000 + i
        category = random.choice(categories)
        field = random.choice(fields)
        company = random.choice(companies)
        location = random.choice(locations)

        # 날짜 설정
        app_start = base_date + timedelta(days=random.randint(-30, 30))
        app_end = app_start + timedelta(days=random.randint(7, 60))
        act_start = app_end + timedelta(days=random.randint(1, 30))
        act_end = act_start + timedelta(days=random.randint(30, 180))

        activity_data = {
            "postId": post_id,
            "category": category,
            "title": f"{field} {category} #{i+1}",
            "company": company,
            "activityDuration": random.randint(30, 180),
            "activityField": field,
            "description": f"{company}에서 주관하는 {field} 분야 {category}입니다.",
            "location": location,
            "target_audience": "대학생, 청년",
            "application_start_date": app_start.strftime("%Y-%m-%d"),
            "application_end_date": app_end.strftime("%Y-%m-%d"),
            "activity_start_date": act_start.strftime("%Y-%m-%d"),
            "activity_end_date": act_end.strftime("%Y-%m-%d"),
            "tags": [field.lower(), category.lower(), company.lower()],
            "max_participants": random.randint(10, 100),
            "scholarship_amount": random.choice([0, 500000, 1000000, 2000000]),
            "is_online": random.choice([True, False]),
            "is_paid": random.choice([True, False]),
            "is_certificate_provided": random.choice([True, False]),
            "difficulty_level": random.choice(["초급", "중급", "고급"]),
        }

        activity = Activity(**activity_data)
        activities.append(activity)

    return activities


def create_chroma_query_filter(
    category: Optional[str] = None,
    activity_field: Optional[str] = None,
    company: Optional[str] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    is_online: Optional[bool] = None,
    is_paid: Optional[bool] = None,
    location: Optional[str] = None,
    application_deadline_after: Optional[str] = None,
) -> Dict[str, Any]:
    """ChromaDB 쿼리 필터 생성"""
    filters = {}

    if category:
        filters["category"] = {"$eq": category}

    if activity_field:
        filters["activity_field"] = {"$eq": activity_field}

    if company:
        filters["company"] = {"$eq": company}

    if min_duration is not None:
        filters["activity_duration"] = filters.get("activity_duration", {})
        filters["activity_duration"]["$gte"] = min_duration

    if max_duration is not None:
        filters["activity_duration"] = filters.get("activity_duration", {})
        filters["activity_duration"]["$lte"] = max_duration

    if is_online is not None:
        filters["is_online"] = {"$eq": is_online}

    if is_paid is not None:
        filters["is_paid"] = {"$eq": is_paid}

    if location:
        filters["location"] = {"$eq": location}

    if application_deadline_after:
        filters["application_end_date"] = {"$gte": application_deadline_after}

    return filters


def validate_activity_metadata(metadata: Dict[str, Any]) -> bool:
    """Activity 메타데이터 유효성 검사"""
    required_fields = [
        "post_id",
        "category",
        "title",
        "company",
        "activity_duration",
        "activity_field",
    ]

    # 필수 필드 존재 확인
    for field in required_fields:
        if field not in metadata:
            return False

    # 타입 검사
    if not isinstance(metadata["post_id"], int):
        return False

    if not isinstance(metadata["activity_duration"], int):
        return False

    # 날짜 형식 검사 (선택적 필드)
    date_fields = ["application_end_date", "activity_start_date", "activity_end_date"]
    for field in date_fields:
        if field in metadata and metadata[field]:
            try:
                datetime.strptime(metadata[field], "%Y-%m-%d")
            except (ValueError, TypeError):
                return False

    return True
