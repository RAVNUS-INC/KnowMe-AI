"""
ChromaDB Portfolio 관리자

Portfolio 모델과 ChromaDB 벡터 데이터베이스 간의 상호작용을 관리하는 클래스입니다.
vector_database.py를 참고하여 개선된 버전입니다.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
import uuid

from src.models.portfolio import Portfolio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioChromaManager:
    """Portfolio 데이터를 ChromaDB에서 관리하는 클래스 - vector_database.py 참고하여 개선됨"""

    def __init__(
        self,
        collection_name: str = "portfolios",
        persist_directory: str = "./chroma_portfolio_db",
        embedding_model: str = "jhgan/ko-sbert-nli",
    ):
        """
        ChromaDB Portfolio 관리자 초기화

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

        # SentenceTransformer로 임베딩 모델 초기화 (한국어 특화)
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info(f"임베딩 모델 '{embedding_model}' 로드 완료")

        # ChromaDB 클라이언트 초기화 (PersistentClient 사용)
        self.client = chromadb.PersistentClient(path=persist_directory)
        logger.info(f"ChromaDB 클라이언트 초기화 완료: {persist_directory}")

        # 컬렉션 초기화
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """컬렉션 초기화 또는 기존 컬렉션 로드"""
        try:
            # 기존 컬렉션이 있으면 로드, 없으면 생성
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "사용자 포트폴리오 벡터 저장소"}
            )
            logger.info(f"컬렉션 '{self.collection_name}' 초기화 완료")
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

    def add_portfolio(self, portfolio: Portfolio) -> bool:
        """포트폴리오를 ChromaDB에 추가"""
        try:
            # 문서 ID 생성
            document_id = portfolio.generate_document_id()

            # 임베딩 텍스트 생성
            embedding_text = portfolio.to_embedding_text()

            # 임베딩 벡터 생성
            embeddings = self.generate_embeddings([embedding_text])

            # ChromaDB 메타데이터 생성
            metadata = portfolio.to_chroma_metadata()

            # 컬렉션에 추가
            self.collection.add(
                embeddings=embeddings,
                documents=[embedding_text],
                metadatas=[metadata],
                ids=[document_id]
            )

            logger.info(f"포트폴리오 추가 완료: {document_id}")
            return True

        except Exception as e:
            logger.error(f"포트폴리오 추가 실패: {str(e)}")
            return False
            embedding = self.generate_embeddings([embedding_text])[0]

            # ChromaDB 메타데이터 생성
            metadata = portfolio.to_chroma_metadata()

            # ChromaDB에 추가
            self.collection.add(
                ids=[document_id],
                documents=[embedding_text],
                embeddings=[embedding],
                metadatas=[metadata],
            )

            logger.info(f"포트폴리오 추가 완료: {document_id}")
            return True

        except Exception as e:
            logger.error(f"포트폴리오 추가 실패: {str(e)}")
            return False

    def update_portfolio(self, portfolio: Portfolio) -> bool:
        """포트폴리오 업데이트"""
        try:
            # 기존 포트폴리오 삭제
            self.delete_portfolio(portfolio.user_id)

            # 새 포트폴리오 추가
            return self.add_portfolio(portfolio)

        except Exception as e:
            logger.error(f"포트폴리오 업데이트 실패: {str(e)}")
            return False

    def get_portfolio_by_user_id(self, user_id: int) -> Optional[Portfolio]:
        """사용자 ID로 포트폴리오 조회"""
        try:
            results = self.collection.query(
                where={"user_id": {"$eq": user_id}}, n_results=1
            )

            if results["ids"] and len(results["ids"][0]) > 0:
                chroma_result = {
                    "id": results["ids"][0][0],
                    "metadata": results["metadatas"][0][0],
                    "document": results["documents"][0][0],
                }
                return Portfolio.from_chroma_result(chroma_result)

            return None

        except Exception as e:
            logger.error(f"포트폴리오 조회 실패: {str(e)}")
            return None

    def delete_portfolio(self, user_id: int) -> bool:
        """포트폴리오 삭제"""
        try:
            # 사용자 ID로 문서 찾기
            results = self.collection.query(
                where={"user_id": {"$eq": user_id}}, n_results=1
            )

            if results["ids"] and len(results["ids"][0]) > 0:
                document_id = results["ids"][0][0]
                self.collection.delete(ids=[document_id])
                logger.info(f"포트폴리오 삭제 완료: user_id {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"포트폴리오 삭제 실패: {str(e)}")
            return False

    def search_similar_portfolios(
        self,
        query_text: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Portfolio, float]]:
        """유사한 포트폴리오 검색"""
        try:
            # 쿼리 텍스트를 임베딩으로 변환
            query_embedding = self.generate_embeddings([query_text])[0]

            # ChromaDB에서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results, where=filters
            )

            # 결과를 Portfolio 객체로 변환
            portfolios_with_scores = []

            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }

                    portfolio = Portfolio.from_chroma_result(chroma_result)
                    # 거리를 유사도로 변환 (거리가 작을수록 유사도가 높음)
                    similarity_score = 1.0 - results["distances"][0][i]

                    portfolios_with_scores.append((portfolio, similarity_score))

            logger.info(
                f"유사 포트폴리오 검색 완료: {len(portfolios_with_scores)}개 결과"
            )
            return portfolios_with_scores

        except Exception as e:
            logger.error(f"포트폴리오 검색 실패: {str(e)}")
            return []

    def search_portfolios_by_skills(
        self, skills: List[str], n_results: int = 10
    ) -> List[Tuple[Portfolio, float]]:
        """스킬 기반 포트폴리오 검색"""
        query_text = f"기술 스킬: {', '.join(skills)}"
        return self.search_similar_portfolios(query_text, n_results)

    def search_portfolios_by_location(
        self, location: str, n_results: int = 10
    ) -> List[Portfolio]:
        """지역 기반 포트폴리오 검색"""
        try:
            results = self.collection.query(
                where={"location": {"$eq": location}}, n_results=n_results
            )

            portfolios = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chroma_result = {
                        "id": results["ids"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i],
                    }
                    portfolios.append(Portfolio.from_chroma_result(chroma_result))

            return portfolios

        except Exception as e:
            logger.error(f"지역별 포트폴리오 검색 실패: {str(e)}")
            return []

    def get_all_portfolios(self, limit: int = 100) -> List[Portfolio]:
        """모든 포트폴리오 조회"""
        try:
            # peek을 사용하여 모든 데이터 조회
            results = self.collection.peek(limit=limit)

            portfolios = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"])):
                    chroma_result = {
                        "id": results["ids"][i],
                        "metadata": results["metadatas"][i],
                        "document": results["documents"][i],
                    }
                    portfolios.append(Portfolio.from_chroma_result(chroma_result))

            return portfolios

        except Exception as e:
            logger.error(f"전체 포트폴리오 조회 실패: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보 조회"""
        try:
            count = self.collection.count()

            # 스킬별 통계
            all_portfolios = self.get_all_portfolios()
            skill_counts = {}
            location_counts = {}
            age_groups = {"20대": 0, "30대": 0, "40대+": 0}

            for portfolio in all_portfolios:
                # 스킬 통계
                for skill in portfolio.skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

                # 지역 통계
                if portfolio.location:
                    location_counts[portfolio.location] = (
                        location_counts.get(portfolio.location, 0) + 1
                    )

                # 연령대 통계
                if 20 <= portfolio.age < 30:
                    age_groups["20대"] += 1
                elif 30 <= portfolio.age < 40:
                    age_groups["30대"] += 1
                else:
                    age_groups["40대+"] += 1

            return {
                "total_portfolios": count,
                "top_skills": sorted(
                    skill_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "locations": location_counts,
                "age_groups": age_groups,
            }

        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {}

    def get_collection_count(self) -> int:
        """컬렉션의 포트폴리오 개수 반환"""
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
                "portfolio_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model_name,
            }
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {str(e)}")
            return {}

    def list_collections(self) -> List[str]:
        """사용 가능한 컬렉션 목록 반환"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"컬렉션 목록 조회 실패: {str(e)}")
            return []

    def delete_collection(self) -> bool:
        """현재 컬렉션 삭제"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"컬렉션 '{self.collection_name}' 삭제 완료")
            return True
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {str(e)}")
            return False

    def update_portfolio_metadata(
        self, document_id: str, new_metadata: Dict[str, Any]
    ) -> bool:
        """포트폴리오 메타데이터만 업데이트"""
        try:
            self.collection.update(ids=[document_id], metadatas=[new_metadata])

            logger.info(f"메타데이터 업데이트 완료: {document_id}")
            return True
        except Exception as e:
            logger.error(f"메타데이터 업데이트 실패: {str(e)}")
            return False

    def batch_add_portfolios(self, portfolios: List[Portfolio]) -> Dict[str, Any]:
        """여러 포트폴리오를 한 번에 추가"""
        try:
            if not portfolios:
                return {"success": 0, "failed": 0, "errors": []}

            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for portfolio in portfolios:
                try:
                    ids.append(portfolio.generate_document_id())
                    documents.append(portfolio.to_embedding_text())
                    metadatas.append(portfolio.to_chroma_metadata())
                except Exception as e:
                    logger.warning(
                        f"포트폴리오 처리 실패 (user_id: {portfolio.user_id}): {str(e)}"
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

                logger.info(f"배치 포트폴리오 추가 완료: {len(documents)}개")
                return {
                    "success": len(documents),
                    "failed": len(portfolios) - len(documents),
                    "errors": [],
                }

            return {
                "success": 0,
                "failed": len(portfolios),
                "errors": ["모든 포트폴리오 처리 실패"],
            }

        except Exception as e:
            logger.error(f"배치 포트폴리오 추가 실패: {str(e)}")
            return {"success": 0, "failed": len(portfolios), "errors": [str(e)]}

    def __enter__(self) -> "PortfolioChromaManager":
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        # 필요시 정리 작업 수행
        pass

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
