"""
개인화 AI 서비스 CLI 도구

명령줄에서 쉽게 AI 분석 및 추천 기능을 사용할 수 있는 도구
"""

import sys
import json
import argparse
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.services.personalized_ai_service import PersonalizedAIService


def print_json_pretty(data, title="결과"):
    """JSON 데이터를 예쁘게 출력"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print("=" * 60)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("=" * 60)


def recommend_activities_cmd(args):
    """대외 활동 추천 명령"""
    service = PersonalizedAIService(test_mode=args.test_mode)

    # 선호도 파싱
    preferences = {}
    if args.preferences:
        try:
            preferences = json.loads(args.preferences)
        except json.JSONDecodeError:
            print("❌ 선호도는 유효한 JSON 형식이어야 합니다.")
            return

    print("🔍 포트폴리오 기반 대외 활동 추천을 시작합니다...")
    result = service.recommend_activities(preferences)

    if result.get("success"):
        print("✅ 대외 활동 추천 완료!")

        # 추천 결과를 보기 좋게 출력
        recommendations = result.get("recommendations", [])
        for i, rec in enumerate(recommendations, 1):
            print(f"\n📋 추천 {i}: {rec.get('title', 'N/A')}")
            print(f"   유형: {rec.get('activity_type', 'N/A')}")
            print(f"   설명: {rec.get('description', 'N/A')}")
            print(f"   추천 이유: {rec.get('relevance_reason', 'N/A')}")
            print(f"   난이도: {rec.get('difficulty_level', 'N/A')}")
            print(f"   예상 소요 시간: {rec.get('time_commitment', 'N/A')}")
            print(f"   예상 혜택: {', '.join(rec.get('expected_benefits', []))}")

        print(f"\n💡 전체 전략: {result.get('overall_strategy', 'N/A')}")
        print(f"🎯 우선순위 영역: {', '.join(result.get('priority_areas', []))}")

        if args.json:
            print_json_pretty(result, "대외 활동 추천 (상세 JSON)")
    else:
        print(f"❌ 추천 실패: {result.get('error', '알 수 없는 오류')}")


def recommend_jobs_cmd(args):
    """채용 공고 추천 명령"""
    service = PersonalizedAIService(test_mode=args.test_mode)

    # 채용 선호도 파싱
    preferences = {}
    if args.preferences:
        try:
            preferences = json.loads(args.preferences)
        except json.JSONDecodeError:
            print("❌ 선호도는 유효한 JSON 형식이어야 합니다.")
            return

    print("🔍 포트폴리오 기반 채용 공고 추천을 시작합니다...")
    result = service.recommend_jobs(preferences)

    if result.get("success"):
        print("✅ 채용 공고 추천 완료!")

        # 추천 결과를 보기 좋게 출력
        recommendations = result.get("job_recommendations", [])
        for i, rec in enumerate(recommendations, 1):
            print(f"\n💼 추천 {i}: {rec.get('position', 'N/A')}")
            print(f"   회사 유형: {rec.get('company_type', 'N/A')}")
            print(f"   업무 내용: {rec.get('job_description', 'N/A')}")
            print(f"   적합성 이유: {rec.get('match_reason', 'N/A')}")
            print(f"   필요 기술: {', '.join(rec.get('required_skills', []))}")
            print(f"   지원 강점: {', '.join(rec.get('advantage_points', []))}")
            print(f"   예상 연봉: {rec.get('salary_range', 'N/A')}")
            print(f"   커리어 성장: {rec.get('career_growth', 'N/A')}")

        print(f"\n📋 지원 전략: {result.get('application_strategy', 'N/A')}")
        print(f"📊 기술 격차 분석: {result.get('skill_gap_analysis', 'N/A')}")
        print(f"💡 시장 인사이트: {result.get('market_insights', 'N/A')}")

        if args.json:
            print_json_pretty(result, "채용 공고 추천 (상세 JSON)")
    else:
        print(f"❌ 추천 실패: {result.get('error', '알 수 없는 오류')}")


def analyze_portfolio_cmd(args):
    """포트폴리오 분석 명령"""
    service = PersonalizedAIService(test_mode=args.test_mode)
    # 분석 초점 파싱
    focus_areas = []
    if args.focus:
        focus_areas = [area.strip() for area in args.focus.split(",")]

    print("🔍 포트폴리오 강점/약점 분석을 시작합니다...")
    result = service.analyze_portfolio_strengths_weaknesses(focus_areas)

    if result.get("success"):
        print("✅ 포트폴리오 분석 완료!")

        # 새로운 간단한 형식 출력
        print(f"\n💪 강점:")
        print(f"   {result.get('strength', 'N/A')}")

        print(f"\n⚠️ 약점:")
        print(f"   {result.get('weakness', 'N/A')}")

        print(f"\n🎯 추천 포지션:")
        print(f"   {result.get('recommend_position', 'N/A')}")

        print(f"\n⏰ 분석 시간: {result.get('generated_at', 'N/A')}")

        if args.json:
            print_json_pretty(result, "포트폴리오 분석 (JSON 형식)")
    else:
        print(f"❌ 분석 실패: {result.get('error', '알 수 없는 오류')}")


def comprehensive_analysis_cmd(args):
    """종합 분석 명령"""
    service = PersonalizedAIService(test_mode=args.test_mode)

    # 선호도 파싱
    preferences = {}
    if args.preferences:
        try:
            preferences = json.loads(args.preferences)
        except json.JSONDecodeError:
            print("❌ 선호도는 유효한 JSON 형식이어야 합니다.")
            return

    print("🔍 종합적인 AI 인사이트 분석을 시작합니다...")
    print("   (대외활동 추천 + 채용 추천 + 포트폴리오 분석)")

    result = service.get_comprehensive_insights(preferences)

    if result.get("success"):
        print("✅ 종합 분석 완료!")

        # 각 분석 결과 요약
        activity_result = result.get("activity_recommendations", {})
        job_result = result.get("job_recommendations", {})
        portfolio_result = result.get("portfolio_analysis", {})

        print(f"\n📊 분석 요약:")
        print(f"   대외활동 추천: {len(activity_result.get('recommendations', []))}개")
        print(f"   채용 공고 추천: {len(job_result.get('job_recommendations', []))}개")
        print(f"   포트폴리오 강점: {len(portfolio_result.get('strengths', []))}개")
        print(f"   포트폴리오 약점: {len(portfolio_result.get('weaknesses', []))}개")

        if args.json:
            print_json_pretty(result, "종합 AI 인사이트 (상세 JSON)")
        else:
            print("\n💡 상세 내용을 보려면 --json 옵션을 사용하세요.")
    else:
        print(f"❌ 종합 분석 실패: {result.get('error', '알 수 없는 오류')}")


def main():
    """메인 CLI 함수"""
    parser = argparse.ArgumentParser(
        description="AI 기반 개인화 분석 및 추천 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 대외 활동 추천
  python ai_cli.py activities

  # 선호도를 포함한 대외 활동 추천  
  python ai_cli.py activities --preferences '{"관심분야": "AI", "지역": "서울"}'

  # 채용 공고 추천
  python ai_cli.py jobs

  # 포트폴리오 분석 (특정 영역 집중)
  python ai_cli.py portfolio --focus "기술,경험"

  # 종합 분석
  python ai_cli.py comprehensive --json

  # 테스트 모드 (OpenAI API 호출 없이 모의 응답)
  python ai_cli.py portfolio --test
        """,
    )

    # 전역 옵션 추가
    parser.add_argument(
        "--test",
        action="store_true",
        dest="test_mode",
        help="테스트 모드 (OpenAI API 호출 없이 모의 응답 사용)",
    )

    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령")
    # 대외 활동 추천
    activities_parser = subparsers.add_parser("activities", help="대외 활동 추천")
    activities_parser.add_argument("--preferences", help="선호도 (JSON 형식)")
    activities_parser.add_argument(
        "--json", action="store_true", help="JSON 형식으로 전체 결과 출력"
    )
    activities_parser.add_argument(
        "--test", action="store_true", dest="test_mode", help="테스트 모드"
    )
    activities_parser.set_defaults(func=recommend_activities_cmd)

    # 채용 공고 추천
    jobs_parser = subparsers.add_parser("jobs", help="채용 공고 추천")
    jobs_parser.add_argument("--preferences", help="채용 선호도 (JSON 형식)")
    jobs_parser.add_argument(
        "--json", action="store_true", help="JSON 형식으로 전체 결과 출력"
    )
    jobs_parser.add_argument(
        "--test", action="store_true", dest="test_mode", help="테스트 모드"
    )
    jobs_parser.set_defaults(func=recommend_jobs_cmd)

    # 포트폴리오 분석
    portfolio_parser = subparsers.add_parser(
        "portfolio", help="포트폴리오 강점/약점 분석"
    )
    portfolio_parser.add_argument("--focus", help="분석 초점 영역 (쉼표로 구분)")
    portfolio_parser.add_argument(
        "--json", action="store_true", help="JSON 형식으로 전체 결과 출력"
    )
    portfolio_parser.add_argument(
        "--test", action="store_true", dest="test_mode", help="테스트 모드"
    )
    portfolio_parser.set_defaults(func=analyze_portfolio_cmd)

    # 종합 분석
    comprehensive_parser = subparsers.add_parser(
        "comprehensive", help="종합 AI 인사이트"
    )
    comprehensive_parser.add_argument("--preferences", help="전체 선호도 (JSON 형식)")
    comprehensive_parser.add_argument(
        "--json", action="store_true", help="JSON 형식으로 전체 결과 출력"
    )
    comprehensive_parser.add_argument(
        "--test", action="store_true", dest="test_mode", help="테스트 모드"
    )
    comprehensive_parser.set_defaults(func=comprehensive_analysis_cmd)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # 설정 확인
        from src.config.settings import settings

        if not hasattr(settings, "openai_api_key") or not settings.openai_api_key:
            print("❌ OpenAI API 키가 설정되지 않았습니다.")
            print("   환경변수 OPENAI_API_KEY를 설정하거나 settings.py를 확인해주세요.")
            return

        # 명령 실행
        args.func(args)

    except ImportError as e:
        print(f"❌ 모듈 임포트 실패: {e}")
        print("   필요한 의존성이 설치되어 있는지 확인해주세요.")
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
