"""
Recruitment 스키마와 RecruitmentChromaManager 통합 테스트

이 스크립트는 다음을 테스트합니다:
1. Recruitment 스키마 기본 기능
2. ChromaDB 연동 기능
3. RecruitmentChromaManager CRUD 작업
4. 검색 및 필터링 기능
5. 배치 처리 기능
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import traceback

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from models.recruitment import (
        Recruitment,
        create_sample_recruitments,
        create_chroma_query_filter,
        validate_recruitment_metadata,
    )
    from managers.recruitment_manager import (
        RecruitmentChromaManager,
        create_recruitment_manager,
        search_recruitments_by_keywords,
        search_recruitments_by_skills,
    )

    print("✓ 모든 모듈 import 성공")
except ImportError as e:
    print(f"❌ Import 실패: {e}")
    traceback.print_exc()
    sys.exit(1)


def test_recruitment_schema():
    """Recruitment 스키마 기본 기능 테스트"""
    print("\n=== Recruitment 스키마 테스트 ===")

    # 1. 기본 채용공고 생성
    recruitment_data = {
        "id": 1001,
        "title": "백엔드 개발자",
        "company": "google",
        "applicationDeadline": "2025-02-22",
        "tags": ["backend", "python", "django"],
        "requiredExperience": 3,
        "description": "구글에서 백엔드 개발자를 모집합니다.",
        "location": "서울 강남구",
        "employment_type": "정규직",
        "salary_min": 4000,
        "salary_max": 6000,
        "required_skills": ["Python", "Django", "PostgreSQL"],
        "preferred_skills": ["AWS", "Docker", "Kubernetes"],
    }

    try:
        recruitment = Recruitment(**recruitment_data)
        print(f"✓ 채용공고 생성 성공: {recruitment.title}")

        # 2. ChromaDB 메타데이터 변환 테스트
        metadata = recruitment.to_chroma_metadata()
        print(f"✓ ChromaDB 메타데이터 변환 성공: {len(metadata)} 필드")

        # 3. 임베딩 텍스트 생성 테스트
        embedding_text = recruitment.to_embedding_text()
        print(f"✓ 임베딩 텍스트 생성 성공: {len(embedding_text)} 글자")

        # 4. 메타데이터 유효성 검사
        is_valid = validate_recruitment_metadata(metadata)
        print(f"✓ 메타데이터 유효성 검사: {'통과' if is_valid else '실패'}")

        # 5. 날짜 관련 메서드 테스트
        days_left = recruitment.days_until_deadline()
        is_active = recruitment.is_deadline_passed()
        print(f"✓ 마감일까지 {days_left}일, 활성상태: {not is_active}")

        return recruitment

    except Exception as e:
        print(f"❌ 스키마 테스트 실패: {e}")
        traceback.print_exc()
        return None


def test_sample_data_generation():
    """샘플 데이터 생성 테스트"""
    print("\n=== 샘플 데이터 생성 테스트 ===")

    try:
        sample_recruitments = create_sample_recruitments(count=5)
        print(f"✓ {len(sample_recruitments)}개 샘플 채용공고 생성 성공")

        for i, recruitment in enumerate(sample_recruitments[:2]):
            print(f"  {i+1}. {recruitment.company} - {recruitment.title}")

        return sample_recruitments

    except Exception as e:
        print(f"❌ 샘플 데이터 생성 실패: {e}")
        traceback.print_exc()
        return []


def test_chroma_manager_basic():
    """RecruitmentChromaManager 기본 기능 테스트"""
    print("\n=== ChromaDB 관리자 기본 테스트 ===")

    try:
        # ChromaDB 관리자 생성
        manager = create_recruitment_manager(
            collection_name="test_recruitments", persist_directory="./test_chroma_db"
        )
        print("✓ ChromaDB 관리자 생성 성공")

        # 컬렉션 통계 확인
        stats = manager.get_collection_stats()
        print(f"✓ 컬렉션 통계: {stats}")

        return manager

    except Exception as e:
        print(f"❌ ChromaDB 관리자 테스트 실패: {e}")
        traceback.print_exc()
        return None


def test_crud_operations(manager, sample_recruitments):
    """CRUD 작업 테스트"""
    print("\n=== CRUD 작업 테스트 ===")

    if not manager or not sample_recruitments:
        print("❌ 관리자나 샘플 데이터가 없어 테스트를 건너뜁니다")
        return False

    try:
        # 1. 단일 채용공고 추가
        first_recruitment = sample_recruitments[0]
        success = manager.add_recruitment(first_recruitment)
        print(f"✓ 단일 채용공고 추가: {'성공' if success else '실패'}")

        # 2. 배치 채용공고 추가
        remaining_recruitments = sample_recruitments[1:3]
        success = manager.add_recruitments(remaining_recruitments)
        print(f"✓ 배치 채용공고 추가: {'성공' if success else '실패'}")

        # 3. ID로 조회
        retrieved = manager.get_recruitment_by_id(first_recruitment.id)
        print(f"✓ ID 조회: {'성공' if retrieved else '실패'}")
        if retrieved:
            print(f"  조회된 채용공고: {retrieved.company} - {retrieved.title}")

        # 4. 업데이트
        if retrieved:
            retrieved.title = "업데이트된 " + retrieved.title
            success = manager.update_recruitment(retrieved)
            print(f"✓ 채용공고 업데이트: {'성공' if success else '실패'}")

        # 5. 통계 확인
        stats = manager.get_collection_stats()
        print(f"✓ 현재 컬렉션에 {stats.get('total_recruitments', 0)}개 채용공고 저장됨")

        return True

    except Exception as e:
        print(f"❌ CRUD 작업 테스트 실패: {e}")
        traceback.print_exc()
        return False


def test_search_operations(manager):
    """검색 작업 테스트"""
    print("\n=== 검색 작업 테스트 ===")

    if not manager:
        print("❌ 관리자가 없어 테스트를 건너뜁니다")
        return

    try:
        # 1. 기본 텍스트 검색
        results = manager.search_recruitments("백엔드 개발자", n_results=5)
        print(f"✓ 텍스트 검색: {len(results)}개 결과")

        # 2. 회사명으로 검색
        results = manager.search_by_company("google", n_results=3)
        print(f"✓ 회사명 검색: {len(results)}개 결과")

        # 3. 경력으로 검색
        results = manager.search_by_experience(1, 5, n_results=3)
        print(f"✓ 경력 검색: {len(results)}개 결과")

        # 4. 활성 채용공고 검색
        results = manager.search_active_recruitments(n_results=5)
        print(f"✓ 활성 채용공고 검색: {len(results)}개 결과")

        # 5. 키워드 검색
        results = search_recruitments_by_keywords(
            manager, ["Python", "Django"], n_results=3
        )
        print(f"✓ 키워드 검색: {len(results)}개 결과")

        # 6. 스킬 기반 검색
        results = search_recruitments_by_skills(manager, ["Python", "AWS"], n_results=3)
        print(f"✓ 스킬 기반 검색: {len(results)}개 결과")

        # 검색 결과 상세 출력 (첫 번째 결과만)
        if results:
            first_result = results[0]
            print(f"  첫 번째 결과:")
            print(f"    - ID: {first_result['id']}")
            print(f"    - 유사도: {first_result.get('similarity_score', 'N/A')}")
            if "recruitment" in first_result:
                recruitment = first_result["recruitment"]
                print(f"    - 제목: {recruitment.title}")
                print(f"    - 회사: {recruitment.company}")

    except Exception as e:
        print(f"❌ 검색 작업 테스트 실패: {e}")
        traceback.print_exc()


def test_context_manager(manager, sample_recruitments):
    """컨텍스트 매니저 테스트"""
    print("\n=== 컨텍스트 매니저 테스트 ===")

    if not manager or not sample_recruitments:
        print("❌ 관리자나 샘플 데이터가 없어 테스트를 건너뜁니다")
        return

    try:
        # 배치 작업 컨텍스트 매니저 테스트
        with manager.batch_operation() as batch_manager:
            # 여러 작업을 배치로 수행
            new_recruitments = sample_recruitments[3:5]
            success = batch_manager.add_recruitments(new_recruitments)
            print(
                f"✓ 배치 작업으로 {len(new_recruitments)}개 채용공고 추가: {'성공' if success else '실패'}"
            )

        print("✓ 컨텍스트 매니저 테스트 완료")

    except Exception as e:
        print(f"❌ 컨텍스트 매니저 테스트 실패: {e}")
        traceback.print_exc()


def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")

    try:
        # 1. 잘못된 데이터로 Recruitment 생성 시도
        try:
            invalid_data = {
                "id": "invalid_id",  # 숫자여야 함
                "title": "",  # 빈 문자열
                "company": "test",
                "applicationDeadline": "invalid-date",  # 잘못된 날짜 형식
                "requiredExperience": -1,  # 음수
            }
            recruitment = Recruitment(**invalid_data)
            print("❌ 잘못된 데이터 검증 실패")
        except Exception:
            print("✓ 잘못된 데이터 검증 성공 (예상된 에러)")

        # 2. 존재하지 않는 ID 조회
        manager = create_recruitment_manager(collection_name="test_recruitments_error")
        result = manager.get_recruitment_by_id(99999)
        print(
            f"✓ 존재하지 않는 ID 조회: {'None 반환' if result is None else '예상치 못한 결과'}"
        )

        # 3. 빈 검색
        results = manager.search_recruitments("", n_results=5)
        print(f"✓ 빈 쿼리 검색: {len(results)}개 결과 (정상)")

    except Exception as e:
        print(f"❌ 에러 처리 테스트 실패: {e}")
        traceback.print_exc()


def cleanup_test_data():
    """테스트 데이터 정리"""
    print("\n=== 테스트 데이터 정리 ===")

    try:
        import shutil

        test_dir = Path("./test_chroma_db")
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("✓ 테스트 ChromaDB 디렉토리 삭제 완료")
        else:
            print("✓ 정리할 테스트 데이터가 없습니다")
    except Exception as e:
        print(f"❌ 테스트 데이터 정리 실패: {e}")


def main():
    """메인 테스트 함수"""
    print("=== Recruitment 통합 테스트 시작 ===")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 스키마 테스트
    recruitment = test_recruitment_schema()

    # 2. 샘플 데이터 생성
    sample_recruitments = test_sample_data_generation()

    # 3. ChromaDB 관리자 테스트
    manager = test_chroma_manager_basic()

    # 4. CRUD 작업 테스트
    crud_success = test_crud_operations(manager, sample_recruitments)

    # 5. 검색 작업 테스트
    if crud_success:
        test_search_operations(manager)

    # 6. 컨텍스트 매니저 테스트
    test_context_manager(manager, sample_recruitments)

    # 7. 에러 처리 테스트
    test_error_handling()

    # 8. 최종 통계
    if manager:
        final_stats = manager.get_collection_stats()
        print(f"\n=== 최종 통계 ===")
        print(f"컬렉션: {final_stats.get('collection_name', 'N/A')}")
        print(f"총 채용공고 수: {final_stats.get('total_recruitments', 0)}")
        print(f"저장 경로: {final_stats.get('persist_directory', 'N/A')}")

    # 9. 정리 (선택적)
    response = input("\n테스트 데이터를 삭제하시겠습니까? (y/N): ")
    if response.lower() in ["y", "yes"]:
        cleanup_test_data()

    print("\n=== Recruitment 통합 테스트 완료 ===")


if __name__ == "__main__":
    main()
