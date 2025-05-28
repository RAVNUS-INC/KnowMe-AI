from __future__ import annotations

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import Optional, Any
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """문서 처리 및 청킹 클래스"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> None:
        """
        문서 처리기 초기화
        
        Args:
            chunk_size: 청크 크기
            chunk_overlap: 청크 간 중복 크기
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ";", ":", " ", ""]
        )
    
    def load_pdf(self, pdf_path: str) -> list[Document]:
        """
        PDF 파일을 로드
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            로드된 문서 페이지 리스트
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            logger.info(f"PDF 로드 완료: {len(documents)}페이지")
            return documents
            
        except Exception as e:
            logger.error(f"PDF 로드 실패: {str(e)}")
            return []
    
    def create_chunks(self, documents: list[Document]) -> list[str]:
        """
        문서를 텍스트 청크로 변환
        
        Args:
            documents: 처리할 문서 리스트
        
        Returns:
            텍스트 청크 리스트
        """
        try:
            # 문서 분할
            chunks = self.text_splitter.split_documents(documents)
            
            # Document 객체에서 텍스트만 추출하고 빈 청크 제거
            text_chunks = [
                chunk.page_content.strip() 
                for chunk in chunks 
                if chunk.page_content.strip()
            ]
            
            logger.info(f"텍스트 청크 생성 완료: {len(text_chunks)}개")
            return text_chunks
            
        except Exception as e:
            logger.error(f"텍스트 청크 생성 실패: {str(e)}")
            return []
