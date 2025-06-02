from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer
from typing import Any, Optional
import uuid
import logging


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaVectorDB:
    """ChromaDB 벡터 데이터베이스 관리 클래스"""

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "jhgan/ko-sbert-nli",
    ) -> None:
        """
        ChromaDB 클라이언트 초기화

        Args:
            collection_name: 컬렉션 이름
            persist_directory: 데이터 저장 디렉토리
            embedding_model: 임베딩 모델명
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # SentenceTransformer로 임베딩 모델 초기화
        self.embedding_model = SentenceTransformer(embedding_model)

        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 컬렉션 초기화
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """컬렉션 초기화 또는 기존 컬렉션 로드"""
        try:
            # 기존 컬렉션이 있으면 로드, 없으면 생성
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "문서 벡터 저장소", "hnsw:space": "cosine"},
            )
            logger.info(f"컬렉션 '{self.collection_name}' 초기화 완료")
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {str(e)}")
            raise

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """텍스트 리스트를 임베딩으로 변환"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise

    def add_documents(
        self,
        documents: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> bool:
        """
        문서를 벡터 데이터베이스에 추가

        Args:
            documents: 문서 텍스트 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트 (없으면 자동 생성)

        Returns:
            bool: 성공 여부
        """
        try:
            # ID가 없으면 UUID로 자동 생성
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]

            # 메타데이터가 없으면 기본 메타데이터로 초기화
            if metadatas is None:
                metadatas = [{"document_index": i} for i in range(len(documents))]

            # 임베딩 생성
            embeddings = self.generate_embeddings(documents)

            # 컬렉션에 추가
            self.collection.add(
                embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids
            )

            logger.info(f"{len(documents)}개 문서가 추가되었습니다.")
            return True

        except Exception as e:
            logger.error(f"문서 추가 실패: {str(e)}")
            return False

    def similarity_search(
        self, query: str, n_results: int = 5, where: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        유사도 검색 수행

        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 개수
            where: 메타데이터 필터링 조건

        Returns:
            dict: 검색 결과
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.generate_embeddings([query])[0]

            # 검색 수행
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=n_results, where=where
            )

            return results

        except Exception as e:
            logger.error(f"검색 실패: {str(e)}")
            return {}

    def search(self, query: str, k: int = 5) -> list[tuple[str, dict[str, Any], float]]:
        """
        간단한 검색 인터페이스

        Args:
            query: 검색 쿼리
            k: 반환할 결과 개수

        Returns:
            list: (문서, 메타데이터, 유사도 점수) 튜플 리스트
        """
        results = self.similarity_search(query, n_results=k)

        if not results or "documents" not in results:
            return []

        search_results = []
        documents = results["documents"][0]
        metadatas = results.get("metadatas", [[{}] * len(documents)])[0]
        distances = results.get("distances", [[1.0] * len(documents)])[0]

        for doc, metadata, distance in zip(documents, metadatas, distances):
            # ChromaDB가 코사인 거리를 사용할 때: distance = 1 - cosine_similarity
            # 따라서 similarity = 1 - distance
            # 하지만 실제로는 제곱 유클리드 거리를 사용할 수도 있으므로
            # 거리 범위에 따라 적절히 변환
            if distance <= 2.0:  # 코사인 거리 범위 (0-2)
                similarity_score = max(0.0, 1.0 - distance)
            else:  # 유클리드 거리인 경우 정규화
                # 큰 거리 값을 0-1 사이의 유사도로 변환
                similarity_score = 1.0 / (1.0 + distance / 100.0)
            search_results.append((doc, metadata, similarity_score))

        return search_results

    def get_collection_count(self) -> int:
        """컬렉션의 문서 개수 반환"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"컬렉션 개수 조회 실패: {str(e)}")
            return 0

    def delete_documents(self, document_ids: list[str]) -> bool:
        """
        문서 삭제

        Args:
            document_ids: 삭제할 문서 ID 리스트

        Returns:
            bool: 성공 여부
        """
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"{len(document_ids)}개 문서가 삭제되었습니다.")
            return True
        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            return False

    def update_document(
        self, document_id: str, document: str, metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        문서 업데이트

        Args:
            document_id: 업데이트할 문서 ID
            document: 새로운 문서 텍스트
            metadata: 새로운 메타데이터

        Returns:
            bool: 성공 여부
        """
        try:
            # 새로운 임베딩 생성
            embedding = self.generate_embeddings([document])[0]

            # 문서 업데이트
            self.collection.update(
                ids=[document_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata] if metadata else None,
            )

            logger.info(f"문서 ID '{document_id}' 업데이트 완료")
            return True
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {str(e)}")
            return False

    def get_collection_info(self) -> dict[str, Any]:
        """컬렉션 정보 반환"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {str(e)}")
            return {}

    def list_collections(self) -> list[str]:
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

    def __enter__(self) -> ChromaVectorDB:
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료"""
        # 필요시 정리 작업 수행
        pass
