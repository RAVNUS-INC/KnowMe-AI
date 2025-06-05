"""
AI 기반 개인화 분석 및 추천 서비스

벡터 데이터베이스의 포트폴리오 정보를 바탕으로 다음 기능을 제공:
1. 대외 활동 추천
2. 채용 공고 추천
3. 포트폴리오 강점/약점 분석
"""

import logging
from typing import Dict, Any, List, Optional
import openai
import json
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)


class PersonalizedAIService:
    """개인화 AI 분석 및 추천 서비스"""

    def __init__(self, test_mode: bool = False):
        """서비스 초기화"""
        self.test_mode = test_mode

        if not test_mode:
            # OpenAI 클라이언트 설정
            self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def get_user_profile_context(self, user_id: Optional[str] = None) -> str:
        """
        벡터 데이터베이스에서 사용자 포트폴리오 정보를 가져와 컨텍스트 생성

        Args:
            user_id: 사용자 ID (현재는 기본 포트폴리오 사용)

        Returns:
            포트폴리오 정보를 종합한 컨텍스트 문자열
        """
        try:
            # 포트폴리오 데이터베이스에서 모든 문서 가져오기
            count = self.portfolio_db.get_collection_count()
            if count == 0:
                return "포트폴리오 정보가 없습니다."

            # 전체 포트폴리오 내용 조회
            results = self.portfolio_db.collection.get(
                include=["documents", "metadatas"]
            )

            if not results or not results.get("documents"):
                return "포트폴리오 정보를 가져올 수 없습니다."

            # 청크별로 정리된 포트폴리오 내용을 하나의 컨텍스트로 결합
            documents = results["documents"]
            metadatas = results.get("metadatas", [])

            # 청크 인덱스 순으로 정렬
            sorted_docs = []
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                chunk_index = meta.get("chunk_index", i) if meta else i
                sorted_docs.append((chunk_index, doc))

            sorted_docs.sort(key=lambda x: x[0])

            # 포트폴리오 전체 내용 결합
            full_portfolio = "\n\n".join([doc for _, doc in sorted_docs])

            return full_portfolio

        except Exception as e:
            logger.error(f"포트폴리오 컨텍스트 생성 실패: {str(e)}")
            return "포트폴리오 정보를 가져오는 중 오류가 발생했습니다."

    def recommend_activities(
        self, preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        포트폴리오 기반 대외 활동 추천

        Args:
            preferences: 사용자 선호도 (선택사항)

        Returns:
            AI가 분석한 맞춤형 대외 활동 추천
        """
        try:
            # 포트폴리오 컨텍스트 가져오기
            portfolio_context = self.get_user_profile_context()

            # 선호도 정보 처리
            preference_text = ""
            if preferences:
                preference_text = f"\n\n사용자 선호사항:\n"
                for key, value in preferences.items():
                    preference_text += f"- {key}: {value}\n"

            # AI 프롬프트 구성
            prompt = f"""
다음은 사용자의 포트폴리오 정보입니다:

{portfolio_context}
{preference_text}

위 포트폴리오 정보를 바탕으로, 이 사용자에게 적합한 대외 활동을 추천해주세요.

추천 시 다음 사항을 고려해주세요:
1. 사용자의 기술 스택과 관련된 활동
2. 현재 경력 수준에 맞는 활동
3. 관심 분야와 연관된 활동
4. 커리어 발전에 도움이 될 활동
5. 네트워킹 기회

다음 JSON 형식으로 응답해주세요:
{{
    "recommendations": [
        {{
            "activity_type": "활동 유형",
            "title": "활동명",
            "description": "활동 설명",
            "recommend_reason": "추천 이유",
            "expected_benefits": ["예상 혜택1", "예상 혜택2"],
            "difficulty_level": "난이도 (초급/중급/고급)",
            "time_commitment": "예상 소요 시간"
        }}
    ],
    "overall_strategy": "전체적인 대외 활동 전략 조언",
    "priority_areas": ["우선순위 영역1", "우선순위 영역2"]
}}
"""

            if self.test_mode:
                # 테스트 모드에서는 고정된 응답 반환
                return {
                    "success": True,
                    "recommendations": [
                        {
                            "activity_type": "온라인 코스",
                            "title": "AI 기초",
                            "description": "인공지능의 기초 개념과 활용법을 배우는 온라인 코스",
                            "recommend_reason": "기술 스택과 관련된 기초 지식 강화",
                            "expected_benefits": ["AI 이해도 향상", "기술 스택 확장"],
                            "difficulty_level": "초급",
                            "time_commitment": "5시간",
                        }
                    ],
                    "overall_strategy": "기술 스택 강화를 위한 기초 교육 이수",
                    "priority_areas": ["AI 기초", "기술 스택 확장"],
                }

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 커리어 전문 컨설턴트입니다. 주어진 포트폴리오를 분석하여 맞춤형 대외 활동을 추천해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            # 응답 파싱
            ai_response = response.choices[0].message.content

            try:
                result = json.loads(ai_response)
                result["success"] = True
                result["generated_at"] = datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "AI 응답 파싱 실패",
                    "raw_response": ai_response,
                }

        except Exception as e:
            logger.error(f"대외 활동 추천 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def recommend_jobs(
        self, job_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        포트폴리오 기반 채용 공고 추천

        Args:
            job_preferences: 채용 선호도 (지역, 연봉, 회사 규모 등)

        Returns:
            AI가 분석한 맞춤형 채용 공고 추천
        """
        try:
            # 포트폴리오 컨텍스트 가져오기
            portfolio_context = self.get_user_profile_context()

            # 채용 선호도 정보 처리
            preference_text = ""
            if job_preferences:
                preference_text = f"\n\n채용 선호사항:\n"
                for key, value in job_preferences.items():
                    preference_text += f"- {key}: {value}\n"

            # AI 프롬프트 구성
            prompt = f"""
다음은 구직자의 포트폴리오 정보입니다:

{portfolio_context}
{preference_text}

위 포트폴리오 정보를 바탕으로, 이 구직자에게 적합한 채용 공고 유형과 지원 전략을 추천해주세요.

추천 시 다음 사항을 분석해주세요:
1. 현재 기술 스택으로 지원 가능한 포지션
2. 경력 수준에 맞는 회사 및 역할
3. 강점을 살릴 수 있는 업무 분야
4. 부족한 부분을 보완할 수 있는 기회
5. 커리어 성장 관점에서의 전략적 선택

다음 JSON 형식으로 응답해주세요:
{{
    "job_recommendations": [
        {{
            "position": "추천 포지션",
            "company_type": "적합한 회사 유형",
            "job_description": "업무 내용",
            "match_reason": "적합성 이유",
            "required_skills": ["필요 기술1", "필요 기술2"],
            "advantage_points": ["지원 시 강점1", "지원 시 강점2"],
            "preparation_needed": ["준비 필요 사항1", "준비 필요 사항2"],
            "salary_range": "예상 연봉 범위",
            "career_growth": "커리어 성장 가능성"
        }}
    ],
    "application_strategy": "지원 전략 조언",
    "skill_gap_analysis": "기술 격차 분석",
    "market_insights": "채용 시장 인사이트"
}}
"""

            if self.test_mode:
                # 테스트 모드에서는 고정된 응답 반환
                return {
                    "success": True,
                    "job_recommendations": [
                        {
                            "position": "주니어 AI 엔지니어",
                            "company_type": "스타트업",
                            "job_description": "AI 모델 개발 및 데이터 분석",
                            "match_reason": "기술 스택과 경력 수준에 적합",
                            "required_skills": ["Python", "기계 학습", "데이터 분석"],
                            "advantage_points": [
                                "AI 프로젝트 경험",
                                "데이터 분석 능력",
                            ],
                            "preparation_needed": [
                                "이력서 업데이트",
                                "포트폴리오 정리",
                            ],
                            "salary_range": "3000-4000만원",
                            "career_growth": "높음",
                        }
                    ],
                    "application_strategy": "AI 관련 포지션에 집중하여 지원",
                    "skill_gap_analysis": "기술 스택은 적합하나, 실무 경험 부족",
                    "market_insights": "AI 분야는 성장 중이며, 주니어 포지션에 대한 수요 증가",
                }

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문 채용 컨설턴트입니다. 포트폴리오를 분석하여 맞춤형 채용 정보를 제공해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2500,
            )

            # 응답 파싱
            ai_response = response.choices[0].message.content

            try:
                result = json.loads(ai_response)
                result["success"] = True
                result["generated_at"] = datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "AI 응답 파싱 실패",
                    "raw_response": ai_response,
                }

        except Exception as e:
            logger.error(f"채용 공고 추천 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def analyze_portfolio_strengths_weaknesses(
        self, analysis_focus: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        포트폴리오 강점/약점 분석

        Args:
            analysis_focus: 분석 초점 영역 (예: ["기술", "경험", "프로젝트"])

        Returns:
            AI가 분석한 포트폴리오 강점/약점 및 개선 방안
        """
        try:
            # 포트폴리오 컨텍스트 가져오기
            portfolio_context = self.get_user_profile_context()

            # 분석 초점 설정
            focus_text = ""
            if analysis_focus:
                focus_text = f"\n\n특별히 다음 영역에 중점을 두어 분석해주세요: {', '.join(analysis_focus)}"  # AI 프롬프트 구성
            prompt = f"""
다음은 분석할 포트폴리오 정보입니다:

{portfolio_context}
{focus_text}

위 포트폴리오를 종합적으로 분석하여 강점과 약점을 평가해주세요.

분석 관점:
1. 기술적 역량 (Technical Skills)
2. 프로젝트 경험 (Project Experience) 
3. 업무 경험 (Work Experience)
4. 교육 배경 (Educational Background)
5. 성장 잠재력 (Growth Potential)
6. 차별화 요소 (Differentiation)

다음 JSON 형식으로 응답해주세요:
{{
    "strength": "포트폴리오의 주요 강점을 종합적으로 설명하는 문장",
    "weakness": "포트폴리오의 주요 약점을 종합적으로 설명하는 문장",
    "recommend_position": "이 포트폴리오에 가장 적합한 추천 포지션"
}}

각 필드는 다음과 같이 작성해주세요:
- strength: 여러 강점들을 한 문장으로 통합해서 설명 (약 50-100자)
- weakness: 여러 약점들을 한 문장으로 통합해서 설명 (약 50-100자) 
- recommend_position: 강점과 약점을 종합하여 가장 적합한 직무/포지션 추천 (간단명료하게)
"""

            if self.test_mode:
                # 테스트 모드에서는 고정된 응답 반환
                return {
                    "success": True,
                    "strength": "다양한 실전형 주제로 프론트엔드 역량을 폭넓게 다뤘으며, 창의적 아이디어와 구현력이 뛰어남",
                    "weakness": "협업 도구나 팀 프로젝트 경험이 드러나지 않아 실무 환경 적응력에 대한 우려가 있음",
                    "recommend_position": "프론트엔드 개발자",
                    "generated_at": datetime.now().isoformat(),
                }  # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문 포트폴리오 분석가입니다. 객관적이고 건설적인 피드백을 제공해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=3000,
            )

            # 응답 파싱
            ai_response = response.choices[0].message.content

            try:
                result = json.loads(ai_response)
                result["success"] = True
                result["generated_at"] = datetime.now().isoformat()
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "AI 응답 파싱 실패",
                    "raw_response": ai_response,
                }

        except Exception as e:
            logger.error(f"포트폴리오 분석 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_comprehensive_insights(
        self, preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        종합적인 AI 인사이트 제공 (3가지 분석을 통합)

        Args:
            preferences: 사용자 선호도

        Returns:
            대외활동 추천, 채용 추천, 포트폴리오 분석을 통합한 종합 인사이트
        """
        try:
            # 3가지 분석 실행
            activities = self.recommend_activities(preferences)
            jobs = self.recommend_jobs(preferences)
            analysis = self.analyze_portfolio_strengths_weaknesses()

            return {
                "success": True,
                "generated_at": datetime.now().isoformat(),
                "activity_recommendations": activities,
                "job_recommendations": jobs,
                "portfolio_analysis": analysis,
                "integration_summary": "포트폴리오 분석, 대외활동 추천, 채용 정보 추천을 종합하여 개인화된 커리어 인사이트를 제공합니다.",
            }

        except Exception as e:
            logger.error(f"종합 인사이트 생성 실패: {str(e)}")
            return {"success": False, "error": str(e)}

    def analyze_portfolio_from_data(
        self, analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        작업 큐에서 온 데이터 형식을 기반으로 포트폴리오 분석

        Args:
            analysis_data: {
                "activities": [...],
                "educations": [...],
                "userId": int,
                "analysisId": int
            }

        Returns:
            AI가 분석한 포트폴리오 분석 결과 (요약, 강점, 약점, 추천 직무 포함)
        """
        try:
            # 데이터 추출
            activities = analysis_data.get("activities", [])
            educations = analysis_data.get("educations", [])
            user_id = analysis_data.get("userId")
            analysis_id = analysis_data.get("analysisId")

            # 포트폴리오 텍스트 구성
            portfolio_text = self._build_portfolio_from_data(activities, educations)

            # AI 프롬프트 구성
            prompt = f"""
다음은 분석할 포트폴리오 정보입니다:

{portfolio_text}

위 포트폴리오를 종합적으로 분석하여 요약, 강점, 약점, 추천 직무를 제공해주세요.

분석 관점:
1. 기술적 역량 (Technical Skills)
2. 프로젝트/활동 경험 (Project/Activity Experience) 
3. 교육 배경 (Educational Background)
4. 성장 잠재력 (Growth Potential)
5. 차별화 요소 (Differentiation)

다음 JSON 형식으로 응답해주세요:
{{
    "summary": "포트폴리오 전체를 요약하는 문장 (현재 상황과 역량을 객관적으로 나열)",
    "strength": "포트폴리오의 주요 강점을 종합적으로 설명하는 문장",
    "weakness": "포트폴리오의 주요 약점을 종합적으로 설명하는 문장",
    "recommendPosition": "이 포트폴리오에 가장 적합한 추천 직무"
}}

각 필드는 다음과 같이 작성해주세요:
- summary: 전체적인 상황과 역량을 객관적으로 나열 (약 150-300자)
- strength: 여러 강점들을 열거형으로 나열하여 상세히 설명 (약 300-500자)
- weakness: 여러 약점들을 열거형으로 나열하여 설명 (약 50-100자) 
- recommendPosition: 강점과 약점을 종합하여 가장 적합한 직무/포지션 추천 (간단명료하게)
"""

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문 포트폴리오 분석가입니다. 객관적이고 건설적인 피드백을 제공해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1500,
            )

            # 응답 파싱
            ai_response = response.choices[0].message.content

            try:
                return {
                    "analysisId": analysis_id,
                    "taskType": "ANALYZE",
                    "userId": user_id,
                    "success": True,
                    "result": json.loads(ai_response),
                    "errorMessage": None,
                    "completedAt": datetime.now().isoformat(),
                }
            except json.JSONDecodeError:
                return {
                    "analysisId": analysis_id,
                    "taskType": "ANALYZE",
                    "userId": user_id,
                    "success": False,
                    "result": json.loads(ai_response),
                    "errorMessage": "AI 응답 파싱 실패",
                    "completedAt": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"포트폴리오 분석 실패: {str(e)}")
            return {
                "analysisId": analysis_id,
                "taskType": "ANALYZE",
                "userId": user_id,
                "success": False,
                "result": None,
                "errorMessage": str(e),
                "completedAt": datetime.now().isoformat(),
            }

    def _build_portfolio_from_data(
        self, activities: List[Dict], educations: List[Dict]
    ) -> str:
        """
        활동과 교육 데이터를 포트폴리오 텍스트로 구성

        Args:
            activities: 활동 정보 리스트
            educations: 교육 정보 리스트

        Returns:
            포트폴리오 텍스트
        """
        portfolio_sections = []

        # 교육 배경 섹션
        if educations:
            portfolio_sections.append("=== 교육 배경 ===")
            for edu in educations:
                school = edu.get("school", "학교명 없음")
                major = edu.get("major", "전공 없음")
                grade = edu.get("grade", "성적 없음")
                portfolio_sections.append(f"- {school} {major} (학점: {grade})")

        # 활동/경험 섹션
        if activities:
            portfolio_sections.append("\n=== 활동 및 경험 ===")
            for activity in activities:
                title = activity.get("title", "제목 없음")
                description = activity.get("description", "설명 없음")
                content = activity.get("content", "")
                tags = activity.get("tags", [])

                portfolio_sections.append(f"◆ {title}")
                portfolio_sections.append(f"  설명: {description}")
                if content:
                    portfolio_sections.append(f"  상세: {content}")
                if tags:
                    portfolio_sections.append(f"  태그: {', '.join(tags)}")

        return (
            "\n".join(portfolio_sections)
            if portfolio_sections
            else "포트폴리오 정보가 없습니다."
        )
