"""
Activity 스키마와 ActivityChromaManager 통합 테스트

이 스크립트는 다음을 테스트합니다:
1. Activity 스키마 기본 기능
2. ChromaDB 연동 기능
3. ActivityChromaManager CRUD 작업
4. 검색 및 필터링 기능
5. 배치 처리 기능
6. 추천 시스템 기능
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
    from models.activity import (
        Activity,
        create_sample_activities,
        create_chroma_query_filter,
        validate_activity_metadata,
    )
    from managers.activity_manager import (
        ActivityChromaManager,
        create_activity_manager,
        search_activities_by_keywords,
        search_activities_by_skills,
        recommend_activities_for_user,
    )

    print("✓ 모든 모듈 import 성공")
except ImportError as e:
    print(f"❌ Import 실패: {e}")
    traceback.print_exc()
    sys.exit(1)


def test_activity_schema():
    """Activity 스키마 기본 기능 테스트"""
    print("\n=== Activity 스키마 테스트 ===")

    # 1. 기본 대외활동 생성
    activity_data = {
        "postId": 1001,
        "category": "대외활동",
        "title": "스타트업 인큐베이팅 프로그램",
        "company": "서울창업허브",
        "activityDuration": 90,
        "activityField": "창업",
        "description": "3개월간 진행되는 스타트업 인큐베이팅 프로그램입니다.",
        "location": "서울 강남구",
        "target_audience": "대학생, 청년창업자",
        "application_end_date": "2025-06-30",
        "activity_start_date": "2025-07-01",
        "activity_end_date": "2025-09-30",
        "tags": ["창업", "스타트업", "인큐베이팅"],
        "benefits": ["창업교육", "멘토링", "네트워킹", "사무공간"],
        "max_participants": 20,
        "scholarship_amount": 1000000,
        "is_certificate_provided": True,
        "difficulty_level": "중급",
    }

    try:
        activity = Activity(**activity_data)
        print(f"✓ 대외활동 생성 성공: {activity.title}")

        # 2. ChromaDB 메타데이터 변환 테스트
        metadata = activity.to_chroma_metadata()
        print(f"✓ ChromaDB 메타데이터 변환 성공: {len(metadata)} 필드")

        # 3. 임베딩 텍스트 생성 테스트
        embedding_text = activity.to_embedding_text()
        print(f"✓ 임베딩 텍스트 생성 성공: {len(embedding_text)} 글자")

        # 4. 메타데이터 유효성 검사
        is_valid = validate_activity_metadata(metadata)
        print(f"✓ 메타데이터 유효성 검사: {'통과' if is_valid else '실패'}")

        # 5. 날짜 관련 메서드 테스트
        days_left = activity.days_until_application_deadline()
        is_ongoing = activity.is_activity_ongoing()
        duration_weeks = activity.get_activity_duration_weeks()
        print(
            f"✓ 지원마감까지 {days_left}일, 진행중: {is_ongoing}, 기간: {duration_weeks:.1f}주"
        )

        return activity

    except Exception as e:
        print(f"❌ 스키마 테스트 실패: {e}")
        traceback.print_exc()
        return None


def test_sample_data_generation():
    """샘플 데이터 생성 테스트"""
    print("\n=== 샘플 데이터 생성 테스트 ===")

    try:
        sample_activities = create_sample_activities(count=5)
        print(f"✓ {len(sample_activities)}개 샘플 대외활동 생성 성공")

        for i, activity in enumerate(sample_activities[:2]):
            print(f"  {i+1}. {activity.company} - {activity.title}")
            print(f"     카테고리: {activity.category}, 분야: {activity.activityField}")

        return sample_activities

    except Exception as e:
        print(f"❌ 샘플 데이터 생성 실패: {e}")
        traceback.print_exc()
        return []


def test_chroma_manager_basic():
    """ActivityChromaManager 기본 기능 테스트"""
    print("\n=== ChromaDB 관리자 기본 테스트 ===")

    try:
        # ChromaDB 관리자 생성
        manager = create_activity_manager(
            collection_name="test_activities", persist_directory="./test_chroma_db"
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


def test_crud_operations(manager, sample_activities):
    """CRUD 작업 테스트"""
    print("\n=== CRUD 작업 테스트 ===")

    if not manager or not sample_activities:
        print("❌ 관리자나 샘플 데이터가 없어 테스트를 건너뜁니다")
        return False

    try:
        # 1. 단일 대외활동 추가
        first_activity = sample_activities[0]
        success = manager.add_activity(first_activity)
        print(f"✓ 단일 대외활동 추가: {'성공' if success else '실패'}")

        # 2. 배치 대외활동 추가
        remaining_activities = sample_activities[1:3]
        success = manager.add_activities(remaining_activities)
        print(f"✓ 배치 대외활동 추가: {'성공' if success else '실패'}")

        # 3. ID로 조회
        retrieved = manager.get_activity_by_id(first_activity.postId)
        print(f"✓ ID 조회: {'성공' if retrieved else '실패'}")
        if retrieved:
            print(f"  조회된 대외활동: {retrieved.company} - {retrieved.title}")

        # 4. 업데이트
        if retrieved:
            retrieved.title = "업데이트된 " + retrieved.title
            success = manager.update_activity(retrieved)
            print(f"✓ 대외활동 업데이트: {'성공' if success else '실패'}")

        # 5. 통계 확인
        stats = manager.get_collection_stats()
        print(f"✓ 현재 컬렉션에 {stats.get('total_activities', 0)}개 대외활동 저장됨")

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
        results = manager.search_activities("창업 스타트업", n_results=5)
        print(f"✓ 텍스트 검색: {len(results)}개 결과")

        # 2. 카테고리로 검색
        results = manager.search_by_category("대외활동", n_results=3)
        print(f"✓ 카테고리 검색: {len(results)}개 결과")

        # 3. 활동 분야로 검색
        results = manager.search_by_field("창업", n_results=3)
        print(f"✓ 활동 분야 검색: {len(results)}개 결과")

        # 4. 주관사로 검색
        results = manager.search_by_company("서울창업허브", n_results=3)
        print(f"✓ 주관사 검색: {len(results)}개 결과")

        # 5. 활동 기간으로 검색
        results = manager.search_by_duration(30, 120, n_results=3)
        print(f"✓ 활동 기간 검색: {len(results)}개 결과")

        # 6. 온라인 활동 검색
        results = manager.search_online_activities(n_results=3)
        print(f"✓ 온라인 활동 검색: {len(results)}개 결과")

        # 7. 수료증 제공 활동 검색
        results = manager.search_certificate_activities(n_results=3)
        print(f"✓ 수료증 제공 활동 검색: {len(results)}개 결과")

        # 8. 키워드 검색
        results = search_activities_by_keywords(
            manager, ["창업", "멘토링"], n_results=3
        )
        print(f"✓ 키워드 검색: {len(results)}개 결과")

        # 9. 스킬 기반 검색
        results = search_activities_by_skills(manager, ["창업", "마케팅"], n_results=3)
        print(f"✓ 스킬 기반 검색: {len(results)}개 결과")

        # 검색 결과 상세 출력 (첫 번째 결과만)
        if results:
            first_result = results[0]
            print(f"  첫 번째 결과:")
            print(f"    - ID: {first_result['id']}")
            print(f"    - 유사도: {first_result.get('similarity_score', 'N/A')}")
            if "activity" in first_result:
                activity = first_result["activity"]
                print(f"    - 제목: {activity.title}")
                print(f"    - 주관사: {activity.company}")
                print(f"    - 카테고리: {activity.category}")

    except Exception as e:
        print(f"❌ 검색 작업 테스트 실패: {e}")
        traceback.print_exc()


def test_recommendation_system(manager):
    """추천 시스템 테스트"""
    print("\n=== 추천 시스템 테스트 ===")

    if not manager:
        print("❌ 관리자가 없어 테스트를 건너뜁니다")
        return

    try:
        # 1. 사용자 관심사 기반 추천
        user_interests = ["창업", "IT", "마케팅"]
        user_skills = ["Python", "기획", "발표"]

        recommendations = recommend_activities_for_user(
            manager=manager,
            user_interests=user_interests,
            user_skills=user_skills,
            preferred_duration_days=90,
            is_online_preferred=False,
            n_results=5,
        )
        print(f"✓ 사용자 맞춤 추천: {len(recommendations)}개 결과")

        # 2. 통계 정보 확인
        category_stats = manager.get_category_stats()
        field_stats = manager.get_field_stats()
        print(f"✓ 카테고리 통계: {category_stats}")
        print(f"✓ 분야 통계: {field_stats}")

        # 추천 결과 상세 출력
        for i, rec in enumerate(recommendations[:2]):
            if "activity" in rec:
                activity = rec["activity"]
                print(f"  추천 {i+1}: {activity.title}")
                print(f"    - 주관사: {activity.company}")
                print(f"    - 분야: {activity.activityField}")
                print(f"    - 유사도: {rec.get('similarity_score', 'N/A')}")

    except Exception as e:
        print(f"❌ 추천 시스템 테스트 실패: {e}")
        traceback.print_exc()


def test_filter_operations(manager):
    """필터 작업 테스트"""
    print("\n=== 필터 작업 테스트 ===")

    if not manager:
        print("❌ 관리자가 없어 테스트를 건너뜁니다")
        return

    try:
        # 1. 복합 필터 생성 및 적용
        filters = create_chroma_query_filter(
            category="대외활동",
            activity_field="창업",
            min_duration=30,
            max_duration=120,
            is_online=False,
        )

        results = manager.search_activities(
            query="창업 프로그램", n_results=5, filters=filters
        )
        print(f"✓ 복합 필터 검색: {len(results)}개 결과")

        # 2. 장학금/지원금 있는 활동 검색
        results = manager.search_with_scholarship(min_amount=500000, n_results=3)
        print(f"✓ 장학금 지원 활동 검색: {len(results)}개 결과")

        # 3. 현재 지원 가능한 활동 검색
        results = manager.search_active_applications(n_results=5)
        print(f"✓ 현재 지원 가능한 활동: {len(results)}개 결과")

    except Exception as e:
        print(f"❌ 필터 작업 테스트 실패: {e}")
        traceback.print_exc()


def test_context_manager(manager, sample_activities):
    """컨텍스트 매니저 테스트"""
    print("\n=== 컨텍스트 매니저 테스트 ===")

    if not manager or not sample_activities:
        print("❌ 관리자나 샘플 데이터가 없어 테스트를 건너뜁니다")
        return

    try:
        # 배치 작업 컨텍스트 매니저 테스트
        with manager.batch_operation() as batch_manager:
            # 여러 작업을 배치로 수행
            new_activities = sample_activities[3:5]
            success = batch_manager.add_activities(new_activities)
            print(
                f"✓ 배치 작업으로 {len(new_activities)}개 대외활동 추가: {'성공' if success else '실패'}"
            )

        print("✓ 컨텍스트 매니저 테스트 완료")

    except Exception as e:
        print(f"❌ 컨텍스트 매니저 테스트 실패: {e}")
        traceback.print_exc()


def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")

    try:
        # 1. 잘못된 데이터로 Activity 생성 시도
        try:
            invalid_data = {
                "postId": "invalid_id",  # 숫자여야 함
                "category": "",  # 빈 문자열
                "title": "",  # 빈 문자열
                "company": "test",
                "activityDuration": -1,  # 음수
                "activityField": "",
                "application_end_date": "invalid-date",  # 잘못된 날짜 형식
            }
            activity = Activity(**invalid_data)
            print("❌ 잘못된 데이터 검증 실패")
        except Exception:
            print("✓ 잘못된 데이터 검증 성공 (예상된 에러)")

        # 2. 존재하지 않는 ID 조회
        manager = create_activity_manager(collection_name="test_activities_error")
        result = manager.get_activity_by_id(99999)
        print(
            f"✓ 존재하지 않는 ID 조회: {'None 반환' if result is None else '예상치 못한 결과'}"
        )

        # 3. 빈 검색
        results = manager.search_activities("", n_results=5)
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
    print("=== Activity 통합 테스트 시작 ===")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 스키마 테스트
    activity = test_activity_schema()

    # 2. 샘플 데이터 생성
    sample_activities = test_sample_data_generation()

    # 3. ChromaDB 관리자 테스트
    manager = test_chroma_manager_basic()

    # 4. CRUD 작업 테스트
    crud_success = test_crud_operations(manager, sample_activities)

    # 5. 검색 작업 테스트
    if crud_success:
        test_search_operations(manager)

    # 6. 추천 시스템 테스트
    if crud_success:
        test_recommendation_system(manager)

    # 7. 필터 작업 테스트
    if crud_success:
        test_filter_operations(manager)

    # 8. 컨텍스트 매니저 테스트
    test_context_manager(manager, sample_activities)

    # 9. 에러 처리 테스트
    test_error_handling()

    # 10. 최종 통계
    if manager:
        final_stats = manager.get_collection_stats()
        category_stats = manager.get_category_stats()
        field_stats = manager.get_field_stats()

        print(f"\n=== 최종 통계 ===")
        print(f"컬렉션: {final_stats.get('collection_name', 'N/A')}")
        print(f"총 대외활동 수: {final_stats.get('total_activities', 0)}")
        print(f"저장 경로: {final_stats.get('persist_directory', 'N/A')}")
        print(f"카테고리별 분포: {category_stats}")
        print(f"분야별 분포: {field_stats}")

    # 11. 정리 (선택적)
    response = input("\n테스트 데이터를 삭제하시겠습니까? (y/N): ")
    if response.lower() in ["y", "yes"]:
        cleanup_test_data()

    print("\n=== Activity 통합 테스트 완료 ===")


if __name__ == "__main__":
    main()
