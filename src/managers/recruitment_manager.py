"""
ChromaDB Recruitment 관리자

Recruitment 모델과 ChromaDB 벡터 데이터베이스 간의 상호작용을 관리하는 클래스입니다.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

from models.recruitment import Recruitment

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecruitmentChromaManager:
    """Recruitment 데이터를 ChromaDB에서 관리하는 클래스"""

    def __init__(
        self,
        collection_name: str = "recruitments",
        persist_directory: str = "./chroma_recruitment_db",
        embedding_model: str = "jhgan/ko-sbert-nli",
    ):
        """
        ChromaDB Recruitment 관리자 초기화

        Args:
            collection_name: 사용할 컬렉션 이름
            persist_directory: 데이터 저장 디렉토리
            embedding_model: 임베딩 모델명 (한국어 특화)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model

        # 디렉토리 생성
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        try:
            # SentenceTransformer로 임베딩 모델 초기화 (한국어 특화)
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"임베딩 모델 '{embedding_model}' 로드 완료")
        except Exception as e:
            logger.warning(f"한국어 모델 로드 실패, 기본 모델 사용: {str(e)}")
            self.embedding_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )

        # ChromaDB 클라이언트 초기화 (로컬 PersistentClient 사용)
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
            logger.info(f"ChromaDB 클라이언트 초기화 완료: {persist_directory}")
        except Exception as e:
            logger.error(f"ChromaDB 클라이언트 초기화 실패: {str(e)}")
            raise

        # 컬렉션 생성 또는 가져오기
        self.collection = self._get_or_create_collection()

        logger.info(f"RecruitmentChromaManager 초기화 완료")

    def _get_or_create_collection(self):
        """채용공고 컬렉션 생성 또는 가져오기"""
        try:
            # 기존 컬렉션이 있으면 로드, 없으면 생성
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Job recruitments for similarity search"},
            )
            logger.info(f"컬렉션 '{self.collection_name}' 초기화 완료")
            return collection
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {str(e)}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise

    def add_recruitment(self, recruitment: Recruitment) -> bool:
        """채용공고를 ChromaDB에 추가"""
        try:
            # 문서 ID 생성
            document_id = recruitment.generate_document_id()

            # 임베딩 텍스트 생성
            embedding_text = recruitment.to_embedding_text()

            # 임베딩 벡터 생성
            embedding = self.generate_embeddings([embedding_text])[0]

            # ChromaDB 메타데이터 생성
            metadata = recruitment.to_chroma_metadata()

            # ChromaDB에 추가
            self.collection.add(
                ids=[document_id],
                documents=[embedding_text],
                embeddings=[embedding],
                metadatas=[metadata],
            )

            logger.info(f"채용공고 추가 완료: {document_id}")
            return True

        except Exception as e:
            logger.error(f"채용공고 추가 실패: {str(e)}")
            return False

    def update_recruitment(self, recruitment: Recruitment) -> bool:
        """채용공고 업데이트"""
        try:
            # 기존 채용공고 삭제
            self.delete_recruitment(recruitment.id)

            # 새 채용공고 추가
            return self.add_recruitment(recruitment)

        except Exception as e:
            logger.error(f"채용공고 업데이트 실패: {str(e)}")
            return False

    def get_recruitment_by_id(self, recruitment_id: int) -> Optional[Recruitment]:
        """채용공고 ID로 조회"""
        try:
            results = self.collection.query(
                where={"recruitment_id": {"$eq": recruitment_id}}, n_results=1
            )

            if results["ids"] and len(results["ids"][0]) > 0:
                chroma_result = {
                    "id": results["ids"][0][0],
                    "metadata": results["metadatas"][0][0],
                    "document": results["documents"][0][0],
                }
                return Recruitment.from_chroma_result(chroma_result)

            return None

        except Exception as e:
            logger.error(f"채용공고 조회 실패: {str(e)}")
            return None

    def delete_recruitment(self, recruitment_id: int) -> bool:
        """채용공고 삭제"""
        try:
            # 채용공고 ID로 문서 찾기
            results = self.collection.query(
                where={"recruitment_id": {"$eq": recruitment_id}}, n_results=1
            )

            if results["ids"] and len(results["ids"][0]) > 0:
                document_id = results["ids"][0][0]
                self.collection.delete(ids=[document_id])
                logger.info(f"채용공고 삭제 완료: recruitment_id {recruitment_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"채용공고 삭제 실패: {str(e)}")
            return False

    def search_similar_recruitments(
        self,
        query_text: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Recruitment, float]]:
        """유사한 채용공고 검색"""
        try:
            # 쿼리 텍스트를 임베딩으로 변환
            query_embedding = self.generate_embeddings([query_text])[0]

            # ChromaDB에서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results, where=filters
            )

            # 결과를 Recruitment 객체로 변환
            recruitments_with_scores = []

            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }

                    recruitment = Recruitment.from_chroma_result(chroma_result)
                    # 거리를 유사도로 변환 (거리가 작을수록 유사도가 높음)
                    similarity_score = 1.0 - results["distances"][0][i]

                    recruitments_with_scores.append((recruitment, similarity_score))

            logger.info(
                f"유사 채용공고 검색 완료: {len(recruitments_with_scores)}개 결과"
            )
            return recruitments_with_scores

        except Exception as e:
            logger.error(f"채용공고 검색 실패: {str(e)}")
            return []

    def search_recruitments_by_skills(
        self, skills: List[str], n_results: int = 10
    ) -> List[Tuple[Recruitment, float]]:
        """스킬 기반 채용공고 검색"""
        query_text = f"필요 기술 스킬: {', '.join(skills)}"
        return self.search_similar_recruitments(query_text, n_results)

    def search_recruitments_by_company(
        self, company: str, n_results: int = 10
    ) -> List[Recruitment]:
        """회사별 채용공고 검색"""
        try:
            results = self.collection.query(
                where={"company": {"$eq": company}}, n_results=n_results
            )

            recruitments = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }
                    recruitments.append(Recruitment.from_chroma_result(chroma_result))

            return recruitments

        except Exception as e:
            logger.error(f"회사별 채용공고 검색 실패: {str(e)}")
            return []

    def search_recruitments_by_location(
        self, location: str, n_results: int = 10
    ) -> List[Recruitment]:
        """지역별 채용공고 검색"""
        try:
            results = self.collection.query(
                where={"location": {"$eq": location}}, n_results=n_results
            )

            recruitments = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }
                    recruitments.append(Recruitment.from_chroma_result(chroma_result))

            return recruitments

        except Exception as e:
            logger.error(f"지역별 채용공고 검색 실패: {str(e)}")
            return []

    def search_active_recruitments(self, n_results: int = 20) -> List[Recruitment]:
        """활성화된 채용공고만 검색"""
        try:
            results = self.collection.query(
                where={"is_active": {"$eq": True}}, n_results=n_results
            )

            recruitments = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }
                    recruitments.append(Recruitment.from_chroma_result(chroma_result))

            return recruitments

        except Exception as e:
            logger.error(f"활성 채용공고 검색 실패: {str(e)}")
            return []

    def search_recruitments_by_experience(
        self, min_experience: int = 0, max_experience: int = 20, n_results: int = 10
    ) -> List[Recruitment]:
        """경력별 채용공고 검색"""
        try:
            filter_conditions = {
                "required_experience": {"$gte": min_experience, "$lte": max_experience}
            }

            results = self.collection.query(
                where=filter_conditions, n_results=n_results
            )

            recruitments = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }
                    recruitments.append(Recruitment.from_chroma_result(chroma_result))

            return recruitments

        except Exception as e:
            logger.error(f"경력별 채용공고 검색 실패: {str(e)}")
            return []

    def get_all_recruitments(self, limit: int = 100) -> List[Recruitment]:
        """모든 채용공고 조회"""
        try:
            # peek을 사용하여 모든 데이터 조회
            results = self.collection.peek(limit=limit)

            recruitments = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"])):
                    chroma_result = {
                        "id": results["ids"][i],
                        "metadata": results["metadatas"][i],
                        "document": results["documents"][i],
                    }
                    recruitments.append(Recruitment.from_chroma_result(chroma_result))

            return recruitments

        except Exception as e:
            logger.error(f"전체 채용공고 조회 실패: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보 조회"""
        try:
            count = self.collection.count()

            # 채용공고별 통계
            all_recruitments = self.get_all_recruitments()
            company_counts = {}
            location_counts = {}
            skill_counts = {}
            experience_groups = {"신입": 0, "주니어(1-3년)": 0, "시니어(4년+)": 0}
            active_count = 0

            for recruitment in all_recruitments:
                # 회사별 통계
                company_counts[recruitment.company] = (
                    company_counts.get(recruitment.company, 0) + 1
                )

                # 지역별 통계
                if recruitment.location:
                    location_counts[recruitment.location] = (
                        location_counts.get(recruitment.location, 0) + 1
                    )

                # 스킬별 통계
                for skill in recruitment.skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

                # 경력별 통계
                if recruitment.requiredExperience == 0:
                    experience_groups["신입"] += 1
                elif 1 <= recruitment.requiredExperience <= 3:
                    experience_groups["주니어(1-3년)"] += 1
                else:
                    experience_groups["시니어(4년+)"] += 1

                # 활성 채용공고 수
                if recruitment.is_active:
                    active_count += 1

            return {
                "total_recruitments": count,
                "active_recruitments": active_count,
                "top_companies": sorted(
                    company_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "top_skills": sorted(
                    skill_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "locations": location_counts,
                "experience_groups": experience_groups,
            }

        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {}

    def get_collection_count(self) -> int:
        """컬렉션의 채용공고 개수 반환"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"컬렉션 개수 조회 실패: {str(e)}")
            return 0

    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 정보 반환"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "recruitment_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model_name,
            }
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {str(e)}")
            return {}

    def batch_add_recruitments(self, recruitments: List[Recruitment]) -> Dict[str, Any]:
        """여러 채용공고를 한 번에 추가"""
        try:
            if not recruitments:
                return {"success": 0, "failed": 0, "errors": []}

            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for recruitment in recruitments:
                try:
                    ids.append(recruitment.generate_document_id())
                    documents.append(recruitment.to_embedding_text())
                    metadatas.append(recruitment.to_chroma_metadata())
                except Exception as e:
                    logger.warning(
                        f"채용공고 처리 실패 (id: {recruitment.id}): {str(e)}"
                    )
                    continue

            if documents:
                # 배치로 임베딩 생성
                batch_embeddings = self.generate_embeddings(documents)

                # ChromaDB에 배치 추가
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=batch_embeddings,
                    metadatas=metadatas,
                )

                logger.info(f"배치 채용공고 추가 완료: {len(documents)}개")
                return {
                    "success": len(documents),
                    "failed": len(recruitments) - len(documents),
                    "errors": [],
                }

            return {
                "success": 0,
                "failed": len(recruitments),
                "errors": ["모든 채용공고 처리 실패"],
            }

        except Exception as e:
            logger.error(f"배치 채용공고 추가 실패: {str(e)}")
            return {"success": 0, "failed": len(recruitments), "errors": [str(e)]}

    def reset_collection(self) -> bool:
        """컬렉션 초기화 (모든 데이터 삭제)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.info(f"컬렉션 '{self.collection_name}' 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {str(e)}")
            return False

    def __enter__(self) -> "RecruitmentChromaManager":
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        # 필요시 정리 작업 수행
        pass
