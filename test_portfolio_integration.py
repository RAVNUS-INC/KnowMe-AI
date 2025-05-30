"""
Portfolio ChromaDB 통합 테스트

Portfolio 모델과 ChromaDB의 통합 기능을 테스트합니다.
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.portfolio import (
    Portfolio,
    EducationItem,
    create_sample_portfolio,
    create_multiple_sample_portfolios,
)
from managers.portfolio_manager import PortfolioChromaManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_portfolio_basic_functionality():
    """Portfolio 모델 기본 기능 테스트"""
    print("\n=== Portfolio 모델 기본 기능 테스트 ===")

    # 기본 정보로 포트폴리오 생성
    portfolio = Portfolio(
        user_id=999,
        user_name="테스트유저",
        age=25,
        education=[],
        skills=["Python", "React", "Docker"],
        bio="테스트용 포트폴리오입니다.",
    )

    print(f"✓ 포트폴리오 생성: {portfolio.user_name} (ID: {portfolio.user_id})")
    print(f"✓ 문서 ID: {portfolio.generate_document_id()}")
    print(f"✓ 임베딩 텍스트 길이: {len(portfolio.to_embedding_text())} 문자")
    print(f"✓ ChromaDB 메타데이터 필드 수: {len(portfolio.to_chroma_metadata())} 개")

    # ChromaDB 문서 형태로 변환
    chroma_doc = portfolio.to_chroma_document()
    print(f"✓ ChromaDB 문서 변환 완료")

    return portfolio


def test_portfolio_manager_basic():
    """Portfolio Manager 기본 기능 테스트"""
    print("\n=== Portfolio Manager 기본 기능 테스트 ===")

    try:
        # Portfolio Manager 초기화
        manager = PortfolioChromaManager(
            collection_name="test_portfolios", persist_directory="./test_chroma_db"
        )
        print("✓ Portfolio Manager 초기화 완료")

        # 컬렉션 정보 확인
        info = manager.get_collection_info()
        print(f"✓ 컬렉션 정보: {info}")

        return manager

    except Exception as e:
        print(f"✗ Portfolio Manager 초기화 실패: {str(e)}")
        return None


def test_portfolio_crud_operations(manager: PortfolioChromaManager):
    """Portfolio CRUD 연산 테스트"""
    print("\n=== Portfolio CRUD 연산 테스트 ===")

    if not manager:
        print("✗ Manager가 없어 CRUD 테스트를 건너뜁니다.")
        return

    # 1. 포트폴리오 추가
    sample_portfolio = create_sample_portfolio()
    success = manager.add_portfolio(sample_portfolio)
    print(f"✓ 포트폴리오 추가: {'성공' if success else '실패'}")

    # 2. 포트폴리오 조회
    retrieved = manager.get_portfolio_by_user_id(sample_portfolio.user_id)
    if retrieved:
        print(f"✓ 포트폴리오 조회 성공: {retrieved.user_name}")
    else:
        print("✗ 포트폴리오 조회 실패")

    # 3. 컬렉션 개수 확인
    count = manager.get_collection_count()
    print(f"✓ 현재 포트폴리오 개수: {count}")

    # 4. 유사 포트폴리오 검색
    search_results = manager.search_similar_portfolios("React 개발자", n_results=3)
    print(f"✓ 유사 포트폴리오 검색 결과: {len(search_results)}개")

    for portfolio, score in search_results:
        print(f"  - {portfolio.user_name}: 유사도 {score:.3f}")


def test_batch_operations(manager: PortfolioChromaManager):
    """배치 연산 테스트"""
    print("\n=== 배치 연산 테스트 ===")

    if not manager:
        print("✗ Manager가 없어 배치 테스트를 건너뜁니다.")
        return

    # 여러 포트폴리오 생성
    portfolios = create_multiple_sample_portfolios()

    # 배치 추가
    result = manager.batch_add_portfolios(portfolios)
    print(f"✓ 배치 추가 결과: 성공 {result['success']}개, 실패 {result['failed']}개")

    # 전체 포트폴리오 조회
    all_portfolios = manager.get_all_portfolios()
    print(f"✓ 전체 포트폴리오 개수: {len(all_portfolios)}개")

    # 스킬 기반 검색
    skill_results = manager.search_portfolios_by_skills(["Python", "React"])
    print(f"✓ Python/React 스킬 검색 결과: {len(skill_results)}개")

    # 지역 기반 검색
    location_results = manager.search_portfolios_by_location("서울특별시")
    print(f"✓ 서울 지역 검색 결과: {len(location_results)}개")


def test_collection_stats(manager: PortfolioChromaManager):
    """컬렉션 통계 테스트"""
    print("\n=== 컬렉션 통계 테스트 ===")

    if not manager:
        print("✗ Manager가 없어 통계 테스트를 건너뜁니다.")
        return

    stats = manager.get_collection_stats()
    if stats:
        print(f"✓ 총 포트폴리오: {stats.get('total_portfolios', 0)}개")
        print(f"✓ 상위 스킬: {stats.get('top_skills', [])[:3]}")
        print(f"✓ 지역별 분포: {stats.get('locations', {})}")
        print(f"✓ 연령대별 분포: {stats.get('age_groups', {})}")
    else:
        print("✗ 통계 조회 실패")


def cleanup_test_data(manager: PortfolioChromaManager):
    """테스트 데이터 정리"""
    print("\n=== 테스트 데이터 정리 ===")

    if not manager:
        return

    # 컬렉션 초기화
    success = manager.reset_collection()
    print(f"✓ 테스트 컬렉션 정리: {'성공' if success else '실패'}")


def main():
    """메인 테스트 함수"""
    print("Portfolio ChromaDB 통합 테스트 시작")
    print("=" * 50)

    try:
        # 1. Portfolio 모델 기본 기능 테스트
        test_portfolio = test_portfolio_basic_functionality()

        # 2. Portfolio Manager 초기화 테스트
        manager = test_portfolio_manager_basic()

        # 3. CRUD 연산 테스트
        test_portfolio_crud_operations(manager)

        # 4. 배치 연산 테스트
        test_batch_operations(manager)

        # 5. 통계 테스트
        test_collection_stats(manager)

        # 6. 정리
        cleanup_test_data(manager)

        print("\n" + "=" * 50)
        print("✓ 모든 테스트가 완료되었습니다!")

    except Exception as e:
        print(f"\n✗ 테스트 중 오류 발생: {str(e)}")
        logger.exception("테스트 실행 중 예외 발생")


if __name__ == "__main__":
    main()
