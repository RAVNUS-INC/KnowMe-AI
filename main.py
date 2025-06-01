import asyncio
import os
import logging

from vector_database import ChromaVectorDB
from document_processor import DocumentProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """메인 실행 함수"""
    try:
        # PDF 파일 경로 설정
        pdf_path = "C:\\Users\\blues\\OneDrive\\바탕 화면\\portfolio.pdf"
        persist_directory = "./chroma_db"
        collection_name = "portfolio_documents"
        
        # PDF 파일 존재 확인
        if not os.path.exists(pdf_path):
            logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            return
        logger.info("문서 처리 시작...")
        # 문서 처리기 초기화
        doc_processor = DocumentProcessor()
        
        # PDF 문서 로드 및 청킹
        documents = doc_processor.load_pdf(pdf_path)
        chunks = doc_processor.create_chunks(documents)
        
        logger.info(f"총 {len(chunks)}개의 텍스트 청크가 생성되었습니다.")
        print("-" * 50)
        
        # 벡터 데이터베이스 초기화
        logger.info("벡터 데이터베이스 초기화...")
        vector_db = ChromaVectorDB(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        
        # 문서를 벡터 데이터베이스에 추가
        logger.info("벡터 임베딩 및 저장 중...")
        
        # 각 청크에 대한 메타데이터 생성
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "source": pdf_path,
                "chunk_index": i,
                "filename": "portfolio.pdf",
                "file_type": ".pdf"
            }
            metadatas.append(metadata)
        
        # 문서 추가 (메타데이터와 함께)
        success = vector_db.add_documents(chunks, metadatas=metadatas)
        
        if success:
            logger.info("벡터 저장소 저장 완료!")
        else:
            logger.error("벡터 저장소 저장 실패!")
            return
        
        # 검색 테스트
        query = "프로젝트"
        logger.info(f"검색 테스트: '{query}'")
        results = vector_db.search(query, k=3)
        
        print(f"\n'{query}' 검색 결과 (상위 {len(results)}개):")
        print("=" * 60)
        
        for i, (content, metadata, score) in enumerate(results):
            print(f"결과 {i+1} (유사도: {score:.4f}):")
            print(f"내용: {content[:200]}...")
            if metadata:
                print(f"메타데이터: {metadata}")
            print("-" * 40)
        
        # 추가 검색 테스트
        test_queries = ["기술", "경험", "개발"]
        for test_query in test_queries:
            print(f"\n'{test_query}' 검색 결과:")
            print("-" * 30)
            test_results = vector_db.search(test_query, k=2)
            for j, (content, metadata, score) in enumerate(test_results):
                print(f"  {j+1}. (유사도: {score:.4f}) {content[:100]}...")
        
        # 벡터 DB 통계 정보
        collection_count = vector_db.get_collection_count()
        logger.info(f"컬렉션에 저장된 문서 수: {collection_count}")
        
        print("\n" + "=" * 60)
        print("처리 완료!")
        
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())