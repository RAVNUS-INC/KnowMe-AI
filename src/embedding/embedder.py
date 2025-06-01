"""
임베딩 로직을 처리하는 모듈입니다.
임베딩 모델 초기화 및 임베딩 생성을 위한 메서드를 포함합니다.
"""

from sentence_transformers import SentenceTransformer
from typing import List

class Embedder:
    """임베딩 생성기 클래스"""
    
    def __init__(self, model_name: str = "jhgan/ko-sbert-nli") -> None:
        """
        Embedder 초기화
        
        Args:
            model_name: 사용할 임베딩 모델 이름
        """
        self.model = SentenceTransformer(model_name)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트를 임베딩으로 변환
        
        Args:
            texts: 임베딩을 생성할 텍스트 리스트
        
        Returns:
            List[List[float]]: 생성된 임베딩 리스트
        """
        return self.model.encode(texts, convert_to_tensor=False).tolist()