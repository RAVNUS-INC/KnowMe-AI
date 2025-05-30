from __future__ import annotations

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import Optional, Any
import os
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """문서 처리 및 청킹 클래스"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[list[str]] = None
    ) -> None:
        """
        문서 처리기 초기화
        
        Args:
            chunk_size: 청크 크기
            chunk_overlap: 청크 간 중복 크기
            separators: 텍스트 분할에 사용할 구분자
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 한국어와 영어 모두 고려한 구분자 설정
        if separators is None:
            separators = [
                "\n\n",  # 단락 구분
                "\n",    # 줄바꿈
                ".",     # 마침표
                "!",     # 느낌표
                "?",     # 물음표
                ";",     # 세미콜론
                ":",     # 콜론
                " ",     # 공백
                ""       # 빈 문자열 (마지막 대안)
            ]
        
        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=separators,
            is_separator_regex=False
        )
    
    def load_pdf(self, pdf_path: str) -> list[Document]:
        """
        PDF 파일을 동기적으로 로드
        
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
    
    async def load_pdf_async(self, pdf_path: str) -> list[Document]:
        """
        PDF 파일을 비동기로 로드
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            로드된 문서 페이지 리스트
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            
            loader = PyPDFLoader(pdf_path)
            
            # 비동기로 페이지 로드
            pages = []
            async for page in loader.alazy_load():
                pages.append(page)
            
            logger.info(f"PDF 비동기 로드 완료: {len(pages)}페이지")
            return pages
            
        except Exception as e:
            logger.error(f"PDF 비동기 로드 실패: {str(e)}")
            return []
    
    def load_text_file(self, file_path: str, encoding: str = 'utf-8') -> list[Document]:
        """
        텍스트 파일 로드
        
        Args:
            file_path: 텍스트 파일 경로
            encoding: 파일 인코딩
        
        Returns:
            로드된 문서 리스트
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"텍스트 파일을 찾을 수 없습니다: {file_path}")
            
            loader = TextLoader(file_path, encoding=encoding)
            documents = loader.load()
            
            logger.info(f"텍스트 파일 로드 완료: {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"텍스트 파일 로드 실패: {str(e)}")
            return []
    
    def split_documents(self, documents: list[Document]) -> list[Document]:
        """
        문서를 청크로 분할
        
        Args:
            documents: 분할할 문서 리스트
        
        Returns:
            분할된 청크 리스트
        """
        try:
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"문서 분할 완료: {len(documents)}개 문서 → {len(chunks)}개 청크")
            return chunks
            
        except Exception as e:
            logger.error(f"문서 분할 실패: {str(e)}")
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
            chunks = self.split_documents(documents)
            
            # Document 객체에서 텍스트만 추출
            text_chunks = [chunk.page_content for chunk in chunks]
            
            logger.info(f"텍스트 청크 생성 완료: {len(text_chunks)}개")
            return text_chunks
            
        except Exception as e:
            logger.error(f"텍스트 청크 생성 실패: {str(e)}")
            return []
    
    def create_chunks_with_metadata(
        self, 
        documents: list[Document]
    ) -> list[tuple[str, dict[str, Any]]]:
        """
        메타데이터와 함께 텍스트 청크 생성
        
        Args:
            documents: 처리할 문서 리스트
        
        Returns:
            (텍스트, 메타데이터) 튜플 리스트
        """
        try:
            # 문서 분할
            chunks = self.split_documents(documents)
            
            # 텍스트와 메타데이터 쌍으로 변환
            chunks_with_metadata = [
                (chunk.page_content, chunk.metadata) 
                for chunk in chunks
            ]
            
            logger.info(f"메타데이터 포함 청크 생성 완료: {len(chunks_with_metadata)}개")
            return chunks_with_metadata
            
        except Exception as e:
            logger.error(f"메타데이터 포함 청크 생성 실패: {str(e)}")
            return []
    
    def process_file(
        self, 
        file_path: str, 
        metadata: Optional[dict[str, Any]] = None
    ) -> list[str]:
        """
        파일을 처리하여 텍스트 청크 반환
        
        Args:
            file_path: 처리할 파일 경로
            metadata: 추가할 메타데이터
        
        Returns:
            텍스트 청크 리스트
        """
        try:
            # 파일 확장자에 따라 로더 선택
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                documents = self.load_pdf(file_path)
            elif file_extension in ['.txt', '.md', '.py', '.js', '.html', '.css']:
                documents = self.load_text_file(file_path)
            else:
                logger.warning(f"지원하지 않는 파일 형식: {file_extension}")
                return []
            
            if not documents:
                return []
            
            # 메타데이터 추가
            if metadata:
                for doc in documents:
                    doc.metadata.update(metadata)
            
            # 파일 정보를 메타데이터에 추가
            file_info = {
                "source": file_path,
                "filename": Path(file_path).name,
                "file_type": file_extension
            }
            
            for doc in documents:
                doc.metadata.update(file_info)
            
            # 청크 생성
            chunks = self.create_chunks(documents)
            
            logger.info(f"파일 처리 완료: {file_path} → {len(chunks)}개 청크")
            return chunks
            
        except Exception as e:
            logger.error(f"파일 처리 실패 ({file_path}): {str(e)}")
            return []
    
    async def process_file_async(
        self, 
        file_path: str, 
        metadata: Optional[dict[str, Any]] = None
    ) -> list[str]:
        """
        파일을 비동기적으로 처리하여 텍스트 청크 반환
        
        Args:
            file_path: 처리할 파일 경로
            metadata: 추가할 메타데이터
        
        Returns:
            텍스트 청크 리스트
        """
        try:
            # 파일 확장자에 따라 로더 선택
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                documents = await self.load_pdf_async(file_path)
            else:
                # 텍스트 파일은 동기적으로 처리
                documents = self.load_text_file(file_path)
            
            if not documents:
                return []
            
            # 메타데이터 추가
            if metadata:
                for doc in documents:
                    doc.metadata.update(metadata)
            
            # 파일 정보를 메타데이터에 추가
            file_info = {
                "source": file_path,
                "filename": Path(file_path).name,
                "file_type": file_extension
            }
            
            for doc in documents:
                doc.metadata.update(file_info)
            
            # 청크 생성
            chunks = self.create_chunks(documents)
            
            logger.info(f"비동기 파일 처리 완료: {file_path} → {len(chunks)}개 청크")
            return chunks
            
        except Exception as e:
            logger.error(f"비동기 파일 처리 실패 ({file_path}): {str(e)}")
            return []
    
    def get_text_stats(self, text: str) -> dict[str, int]:
        """
        텍스트 통계 정보 반환
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            통계 정보 딕셔너리
        """
        return {
            "character_count": len(text),
            "word_count": len(text.split()),
            "line_count": text.count('\n') + 1,
            "paragraph_count": text.count('\n\n') + 1
        }
    
    def validate_chunk_size(self, documents: list[Document]) -> bool:
        """
        문서들이 청크 크기에 적합한지 검증
        
        Args:
            documents: 검증할 문서 리스트
        
        Returns:
            검증 결과
        """
        try:
            total_length = sum(len(doc.page_content) for doc in documents)
            
            if total_length == 0:
                logger.warning("문서에 내용이 없습니다.")
                return False
            
            estimated_chunks = total_length // self.chunk_size + 1
            
            logger.info(f"문서 검증 완료 - 총 길이: {total_length}, 예상 청크 수: {estimated_chunks}")
            
            return True
            
        except Exception as e:
            logger.error(f"문서 검증 실패: {str(e)}")
            return False
