"""
AI 기반 추천 서비스

메타데이터를 이용한 벡터 검색과 OpenAI API를 활용한 개인화 추천 기능을 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional
import openai
import json
from datetime import datetime

from database.vector_database import ChromaVectorDB
from config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationService:
    """AI 기반 추천 서비스"""

    def __init__(self):
        """추천 서비스 초기화"""
        # OpenAI API 설정
        openai.api_key = settings.openai_api_key

        # 벡터 데이터베이스 인스턴스
        self.activity_db = ChromaVectorDB(collection_name="activities")
        self.recruitment_db = ChromaVectorDB(collection_name="recruitments")

    def recommend_activities_with_metadata(
        self,
        user_profile: Dict[str, Any],
        metadata_filters: Optional[Dict[str, Any]] = None,
        n_results: int = 10,
    ) -> Dict[str, Any]:
        """
        메타데이터 필터와 AI 분석을 통한 대외활동 추천

        Args:
            user_profile: 사용자 프로필 정보
            metadata_filters: 메타데이터 기반 필터링 조건
            n_results: 반환할 결과 수

        Returns:
            추천 결과와 AI 분석
        """
        try:
            # 1. 사용자 프로필을 쿼리 텍스트로 변환
            query_text = self._build_activity_query(user_profile)

            # 2. 벡터 검색 + 메타데이터 필터링
            vector_results = self._search_activities_with_metadata(
                query_text, metadata_filters, n_results
            )

            # 3. AI 기반 개인화 추천 생성
            ai_recommendations = self._generate_activity_recommendations(
                user_profile, vector_results
            )

            return {
                "success": True,
                "user_query": query_text,
                "vector_results": vector_results,
                "ai_analysis": ai_recommendations,
                "recommendation_count": len(vector_results),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"대외활동 추천 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def recommend_jobs_with_metadata(
        self,
        user_profile: Dict[str, Any],
        metadata_filters: Optional[Dict[str, Any]] = None,
        n_results: int = 10,
    ) -> Dict[str, Any]:
        """
        메타데이터 필터와 AI 분석을 통한 채용공고 추천

        Args:
            user_profile: 사용자 프로필 정보
            metadata_filters: 메타데이터 기반 필터링 조건
            n_results: 반환할 결과 수

        Returns:
            추천 결과와 AI 분석
        """
        try:
            # 1. 사용자 프로필을 쿼리 텍스트로 변환
            query_text = self._build_job_query(user_profile)

            # 2. 벡터 검색 + 메타데이터 필터링
            vector_results = self._search_jobs_with_metadata(
                query_text, metadata_filters, n_results
            )

            # 3. AI 기반 개인화 추천 생성
            ai_recommendations = self._generate_job_recommendations(
                user_profile, vector_results
            )

            return {
                "success": True,
                "user_query": query_text,
                "vector_results": vector_results,
                "ai_analysis": ai_recommendations,
                "recommendation_count": len(vector_results),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"채용공고 추천 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _search_activities_with_metadata(
        self,
        query_text: str,
        metadata_filters: Optional[Dict[str, Any]],
        n_results: int,
    ) -> List[Dict[str, Any]]:
        """메타데이터 필터를 적용한 대외활동 벡터 검색"""
        try:
            # ChromaDB where 절 구성
            where_clause = None
            if metadata_filters:
                where_clause = self._build_where_clause(metadata_filters)

            # 벡터 검색 실행
            results = self.activity_db.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            # 결과 포맷팅
            formatted_results = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append(
                        {
                            "document": doc,
                            "metadata": (
                                results["metadatas"][0][i]
                                if results["metadatas"]
                                else {}
                            ),
                            "similarity_score": (
                                1 - results["distances"][0][i]
                                if results["distances"]
                                else 0
                            ),
                            "rank": i + 1,
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"대외활동 벡터 검색 실패: {str(e)}")
            return []

    def _search_jobs_with_metadata(
        self,
        query_text: str,
        metadata_filters: Optional[Dict[str, Any]],
        n_results: int,
    ) -> List[Dict[str, Any]]:
        """메타데이터 필터를 적용한 채용공고 벡터 검색"""
        try:
            # ChromaDB where 절 구성
            where_clause = None
            if metadata_filters:
                where_clause = self._build_where_clause(metadata_filters)

            # 벡터 검색 실행
            results = self.recruitment_db.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            # 결과 포맷팅
            formatted_results = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append(
                        {
                            "document": doc,
                            "metadata": (
                                results["metadatas"][0][i]
                                if results["metadatas"]
                                else {}
                            ),
                            "similarity_score": (
                                1 - results["distances"][0][i]
                                if results["distances"]
                                else 0
                            ),
                            "rank": i + 1,
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"채용공고 벡터 검색 실패: {str(e)}")
            return []

    def _build_where_clause(self, metadata_filters: Dict[str, Any]) -> Dict[str, Any]:
        """ChromaDB where 절 구성"""
        where_clause = {}

        for key, value in metadata_filters.items():
            if isinstance(value, dict):
                # 범위 조건 처리 (예: {"min": 1, "max": 5})
                if "min" in value and "max" in value:
                    where_clause[key] = {"$gte": value["min"], "$lte": value["max"]}
                elif "min" in value:
                    where_clause[key] = {"$gte": value["min"]}
                elif "max" in value:
                    where_clause[key] = {"$lte": value["max"]}
            elif isinstance(value, list):
                # IN 조건 처리
                where_clause[key] = {"$in": value}
            else:
                # 정확한 일치
                where_clause[key] = value

        return where_clause

    def _build_activity_query(self, user_profile: Dict[str, Any]) -> str:
        """사용자 프로필을 대외활동 검색 쿼리로 변환"""
        query_parts = []

        # 관심분야
        if "interests" in user_profile and user_profile["interests"]:
            interests = ", ".join(user_profile["interests"])
            query_parts.append(f"관심분야: {interests}")

        # 전공
        if "major" in user_profile and user_profile["major"]:
            query_parts.append(f"전공: {user_profile['major']}")

        # 스킬
        if "skills" in user_profile and user_profile["skills"]:
            skills = ", ".join(user_profile["skills"])
            query_parts.append(f"보유 스킬: {skills}")

        # 경험 레벨
        if "experience_level" in user_profile:
            query_parts.append(f"경험 수준: {user_profile['experience_level']}")

        # 선호 지역
        if "preferred_location" in user_profile:
            query_parts.append(f"선호 지역: {user_profile['preferred_location']}")

        return " ".join(query_parts) if query_parts else "대외활동 추천"

    def _build_job_query(self, user_profile: Dict[str, Any]) -> str:
        """사용자 프로필을 채용공고 검색 쿼리로 변환"""
        query_parts = []

        # 희망 직무
        if "desired_role" in user_profile and user_profile["desired_role"]:
            query_parts.append(f"희망 직무: {user_profile['desired_role']}")

        # 전공
        if "major" in user_profile and user_profile["major"]:
            query_parts.append(f"전공: {user_profile['major']}")

        # 스킬
        if "skills" in user_profile and user_profile["skills"]:
            skills = ", ".join(user_profile["skills"])
            query_parts.append(f"보유 기술: {skills}")

        # 경력
        if "experience_years" in user_profile:
            query_parts.append(f"경력: {user_profile['experience_years']}년")

        # 선호 회사 규모
        if "company_size_preference" in user_profile:
            query_parts.append(
                f"선호 회사 규모: {user_profile['company_size_preference']}"
            )

        return " ".join(query_parts) if query_parts else "채용공고 추천"

    def _generate_activity_recommendations(
        self, user_profile: Dict[str, Any], vector_results: List[Dict[str, Any]]
    ) -> str:
        """AI를 이용한 대외활동 개인화 추천 생성"""
        try:
            # 프롬프트 구성
            prompt = self._build_activity_recommendation_prompt(
                user_profile, vector_results
            )            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 대학생을 위한 대외활동 추천 전문가입니다. 사용자의 프로필과 관심사를 바탕으로 적합한 대외활동을 추천하고 구체적인 이유를 제시해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"AI 대외활동 추천 생성 실패: {str(e)}")
            return "AI 추천 생성 중 오류가 발생했습니다."

    def _generate_job_recommendations(
        self, user_profile: Dict[str, Any], vector_results: List[Dict[str, Any]]
    ) -> str:
        """AI를 이용한 채용공고 개인화 추천 생성"""
        try:            # 프롬프트 구성
            prompt = self._build_job_recommendation_prompt(user_profile, vector_results)

            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 취업 상담 전문가입니다. 사용자의 배경과 역량을 바탕으로 적합한 채용공고를 추천하고 지원 전략을 제시해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"AI 채용공고 추천 생성 실패: {str(e)}")
            return "AI 추천 생성 중 오류가 발생했습니다."

    def _build_activity_recommendation_prompt(
        self, user_profile: Dict[str, Any], vector_results: List[Dict[str, Any]]
    ) -> str:
        """대외활동 추천을 위한 프롬프트 구성"""
        prompt = f"""
사용자 프로필:
{json.dumps(user_profile, ensure_ascii=False, indent=2)}

벡터 검색으로 찾은 유사한 대외활동들:
"""
        for i, result in enumerate(vector_results[:5], 1):
            prompt += f"""
{i}. 제목: {result['metadata'].get('title', 'N/A')}
   주관사: {result['metadata'].get('company', 'N/A')}
   분야: {result['metadata'].get('activityField', 'N/A')}
   기간: {result['metadata'].get('activityDuration', 'N/A')}일
   유사도: {result['similarity_score']:.2f}
   설명: {result['document'][:200]}...
"""

        prompt += """
위 정보를 바탕으로:
1. 사용자에게 가장 적합한 대외활동 3개를 선별하여 추천해주세요
2. 각 추천의 구체적인 이유를 설명해주세요
3. 사용자의 성장에 어떤 도움이 될지 분석해주세요
4. 지원 시 어필할 수 있는 포인트를 제시해주세요
"""

        return prompt

    def _build_job_recommendation_prompt(
        self, user_profile: Dict[str, Any], vector_results: List[Dict[str, Any]]
    ) -> str:
        """채용공고 추천을 위한 프롬프트 구성"""
        prompt = f"""
사용자 프로필:
{json.dumps(user_profile, ensure_ascii=False, indent=2)}

벡터 검색으로 찾은 유사한 채용공고들:
"""
        for i, result in enumerate(vector_results[:5], 1):
            prompt += f"""
{i}. 제목: {result['metadata'].get('title', 'N/A')}
   회사: {result['metadata'].get('company', 'N/A')}
   요구경력: {result['metadata'].get('requiredExperience', 'N/A')}년
   마감일: {result['metadata'].get('applicationDeadline', 'N/A')}
   유사도: {result['similarity_score']:.2f}
   설명: {result['document'][:200]}...
"""

        prompt += """
위 정보를 바탕으로:
1. 사용자에게 가장 적합한 채용공고 3개를 선별하여 추천해주세요
2. 각 추천의 구체적인 이유를 설명해주세요
3. 사용자의 강점과 부족한 부분을 분석해주세요
4. 지원 시 강조할 수 있는 경험과 역량을 제시해주세요
5. 면접 준비 팁을 제공해주세요
"""

        return prompt
