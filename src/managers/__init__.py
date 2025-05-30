"""
관리자 모듈 패키지

각종 데이터 관리자들을 포함합니다:
- RecruitmentChromaManager: 채용공고 ChromaDB 관리자
- ActivityChromaManager: 대외활동 ChromaDB 관리자
"""

from .recruitment_manager import (
    RecruitmentChromaManager,
    create_recruitment_manager,
    search_recruitments_by_keywords,
    search_recruitments_by_skills,
    get_similar_recruitments,
)

from .activity_manager import (
    ActivityChromaManager,
    create_activity_manager,
    search_activities_by_keywords,
    search_activities_by_skills,
    get_similar_activities,
    recommend_activities_for_user,
)

__all__ = [
    "RecruitmentChromaManager",
    "create_recruitment_manager",
    "search_recruitments_by_keywords",
    "search_recruitments_by_skills",
    "get_similar_recruitments",
    "ActivityChromaManager",
    "create_activity_manager",
    "search_activities_by_keywords",
    "search_activities_by_skills",
    "get_similar_activities",
    "recommend_activities_for_user",
]
