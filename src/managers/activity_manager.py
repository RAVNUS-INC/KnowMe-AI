"""
대외활동 전용 ChromaDB 관리자

Activity 스키마를 기반으로 한 ChromaDB 전용 관리자입니다.
- 대외활동 추가/수정/삭제/검색
- 한국어 임베딩 최적화
- 배치 처리 지원
- 컨텍스트 매니저 지원
"""

from typing import List, Optional, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
import logging
from contextlib import contextmanager
from datetime import datetime
import sys
import os

# 상위 디렉토리의 models 패키지를 import하기 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models.activity import Activity

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActivityChromaManager:
    """대외활동 전용 ChromaDB 관리자"""

    def __init__(
        self,
        collection_name: str = "activities",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "jhgan/ko-sbert-nli",
    ) -> None:
        """
        대외활동 ChromaDB 관리자 초기화

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
                metadata={"description": "대외활동 벡터 저장소"},
            )
            logger.info(f"대외활동 컬렉션 '{self.collection_name}' 초기화 완료")
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {str(e)}")
            raise

    def add_activity(self, activity: Activity) -> bool:
        """단일 대외활동 추가"""
        try:
            return self.add_activities([activity])
        except Exception as e:
            logger.error(f"대외활동 추가 실패 (ID: {activity.postId}): {str(e)}")
            return False

    def add_activities(self, activities: List[Activity]) -> bool:
        """배치로 대외활동들 추가"""
        try:
            if not activities:
                logger.warning("추가할 대외활동이 없습니다")
                return True

            # 임베딩용 텍스트 생성
            documents = [a.to_embedding_text() for a in activities]

            # ChromaDB 메타데이터 변환
            metadatas = [a.to_chroma_metadata() for a in activities]

            # ID 생성 (기존 postId 기반)
            ids = [f"activity_{a.postId}" for a in activities]

            # 임베딩 생성
            embeddings = self._generate_embeddings(documents)

            # 컬렉션에 추가
            self.collection.add(
                embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids
            )

            logger.info(f"{len(activities)}개 대외활동 추가 완료")
            return True

        except Exception as e:
            logger.error(f"배치 대외활동 추가 실패: {str(e)}")
            return False

    def search_activities(
        self, query: str, n_results: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """대외활동 검색"""
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

                    # Activity 객체로 복원
                    try:
                        activity = Activity.from_chroma_result(result_data)
                        result_data["activity"] = activity
                    except Exception as e:
                        logger.warning(f"대외활동 객체 복원 실패: {e}")

                    formatted_results.append(result_data)

            logger.info(f"대외활동 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results

        except Exception as e:
            logger.error(f"대외활동 검색 실패: {str(e)}")
            return []

    def get_activity_by_id(self, post_id: int) -> Optional[Activity]:
        """ID로 대외활동 조회"""
        try:
            chroma_id = f"activity_{post_id}"
            results = self.collection.get(ids=[chroma_id])

            if results["ids"]:
                result_data = {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0],
                }
                return Activity.from_chroma_result(result_data)

            return None

        except Exception as e:
            logger.error(f"대외활동 조회 실패 (ID: {post_id}): {str(e)}")
            return None

    def update_activity(self, activity: Activity) -> bool:
        """대외활동 업데이트"""
        try:
            chroma_id = f"activity_{activity.postId}"

            # 기존 데이터 확인
            existing = self.collection.get(ids=[chroma_id])
            if not existing["ids"]:
                logger.warning(
                    f"업데이트할 대외활동을 찾을 수 없습니다 (ID: {activity.postId})"
                )
                return False

            # 새 데이터로 업데이트
            document = activity.to_embedding_text()
            metadata = activity.to_chroma_metadata()
            embedding = self._generate_embeddings([document])[0]

            self.collection.update(
                ids=[chroma_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )

            logger.info(f"대외활동 업데이트 완료 (ID: {activity.postId})")
            return True

        except Exception as e:
            logger.error(f"대외활동 업데이트 실패 (ID: {activity.postId}): {str(e)}")
            return False

    def delete_activity(self, post_id: int) -> bool:
        """대외활동 삭제"""
        try:
            chroma_id = f"activity_{post_id}"
            self.collection.delete(ids=[chroma_id])

            logger.info(f"대외활동 삭제 완료 (ID: {post_id})")
            return True

        except Exception as e:
            logger.error(f"대외활동 삭제 실패 (ID: {post_id}): {str(e)}")
            return False

    def search_by_category(
        self, category: str, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """카테고리로 대외활동 검색"""
        filters = {"category": {"$eq": category}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_by_field(self, field: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """활동 분야로 대외활동 검색"""
        filters = {"activity_field": {"$eq": field}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_by_company(
        self, company: str, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """주관사로 대외활동 검색"""
        filters = {"company": {"$eq": company}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_by_duration(
        self, min_days: int, max_days: int, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """활동 기간으로 대외활동 검색"""
        filters = {"activity_duration": {"$gte": min_days, "$lte": max_days}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_by_location(
        self, location: str, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """지역으로 대외활동 검색"""
        filters = {"location": {"$eq": location}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_online_activities(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """온라인 대외활동 검색"""
        filters = {"is_online": {"$eq": True}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_paid_activities(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """유료 대외활동 검색"""
        filters = {"is_paid": {"$eq": True}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_with_scholarship(
        self, min_amount: int = 0, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """장학금/지원금이 있는 대외활동 검색"""
        filters = {"scholarship_amount": {"$gte": min_amount}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_certificate_activities(
        self, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """수료증 제공 대외활동 검색"""
        filters = {"is_certificate_provided": {"$eq": True}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def search_active_applications(self, n_results: int = 10) -> List[Dict[str, Any]]:
        """현재 지원 가능한 대외활동 검색 (지원 마감일이 지나지 않은 것들)"""
        today = datetime.now().strftime("%Y-%m-%d")
        filters = {"application_end_date": {"$gte": today}}
        return self.search_activities("", n_results=n_results, filters=filters)

    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_activities": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {str(e)}")
            return {}

    def get_category_stats(self) -> Dict[str, int]:
        """카테고리별 통계"""
        try:
            # 모든 활동을 가져와서 카테고리별로 집계
            results = self.collection.get()
            category_counts = {}

            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    category = metadata.get("category", "기타")
                    category_counts[category] = category_counts.get(category, 0) + 1

            return category_counts
        except Exception as e:
            logger.error(f"카테고리 통계 조회 실패: {str(e)}")
            return {}

    def get_field_stats(self) -> Dict[str, int]:
        """활동 분야별 통계"""
        try:
            # 모든 활동을 가져와서 분야별로 집계
            results = self.collection.get()
            field_counts = {}

            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    field = metadata.get("activity_field", "기타")
                    field_counts[field] = field_counts.get(field, 0) + 1

            return field_counts
        except Exception as e:
            logger.error(f"분야 통계 조회 실패: {str(e)}")
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
def create_activity_manager(
    collection_name: str = "activities", persist_directory: str = "./chroma_db"
) -> ActivityChromaManager:
    """대외활동 관리자 생성 편의 함수"""
    return ActivityChromaManager(
        collection_name=collection_name, persist_directory=persist_directory
    )


def search_activities_by_keywords(
    manager: ActivityChromaManager, keywords: List[str], n_results: int = 10
) -> List[Dict[str, Any]]:
    """키워드 리스트로 대외활동 검색"""
    query = " ".join(keywords)
    return manager.search_activities(query, n_results=n_results)


def search_activities_by_skills(
    manager: ActivityChromaManager, skills: List[str], n_results: int = 10
) -> List[Dict[str, Any]]:
    """습득 스킬 기반 대외활동 검색"""
    query = f"습득스킬 배울수있는기술 {' '.join(skills)}"
    return manager.search_activities(query, n_results=n_results)


def get_similar_activities(
    manager: ActivityChromaManager, reference_activity: Activity, n_results: int = 5
) -> List[Dict[str, Any]]:
    """유사한 대외활동 찾기"""
    query = reference_activity.to_embedding_text()
    # 자기 자신은 제외
    filters = {"post_id": {"$ne": reference_activity.postId}}
    return manager.search_activities(query, n_results=n_results, filters=filters)


def recommend_activities_for_user(
    manager: ActivityChromaManager,
    user_interests: List[str],
    user_skills: List[str],
    preferred_duration_days: Optional[int] = None,
    preferred_location: Optional[str] = None,
    is_online_preferred: Optional[bool] = None,
    n_results: int = 10,
) -> List[Dict[str, Any]]:
    """사용자 관심사와 스킬을 기반으로 대외활동 추천"""
    # 쿼리 구성
    query_parts = []
    if user_interests:
        query_parts.append(f"관심분야: {' '.join(user_interests)}")
    if user_skills:
        query_parts.append(f"활용가능스킬: {' '.join(user_skills)}")

    query = " | ".join(query_parts) if query_parts else ""

    # 필터 구성
    filters = {}
    if preferred_duration_days:
        filters["activity_duration"] = {"$lte": preferred_duration_days}
    if preferred_location:
        filters["location"] = {"$eq": preferred_location}
    if is_online_preferred is not None:
        filters["is_online"] = {"$eq": is_online_preferred}

    return manager.search_activities(query, n_results=n_results, filters=filters)
