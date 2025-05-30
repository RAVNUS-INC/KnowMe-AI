"""
Portfolio 모델 테스트

Portfolio 스키마의 유효성 검사, 생성, 조작 기능을 테스트합니다.
"""

import pytest
from datetime import datetime
from src.models.portfolio import Portfolio, EducationItem, create_portfolio_from_basic_info, validate_portfolio_metadata


class TestEducationItem:
    """EducationItem 모델 테스트"""
    
    def test_create_education_item(self):
        """교육 이력 항목 생성 테스트"""
        education = EducationItem(
            institution="테스트 대학교",
            degree="학사",
            field_of_study="컴퓨터공학"
        )
        
        assert education.institution == "테스트 대학교"
        assert education.degree == "학사"
        assert education.field_of_study == "컴퓨터공학"
        assert education.is_current == False
    
    def test_education_item_with_dates(self):
        """날짜가 포함된 교육 이력 테스트"""
        education = EducationItem(
            institution="테스트 대학교",
            start_date="2020-03-01",
            end_date="2024-02-29",
            is_current=True
        )
        
        assert education.start_date == "2020-03-01"
        assert education.end_date == "2024-02-29"
        assert education.is_current == True


class TestPortfolio:
    """Portfolio 모델 테스트"""
    
    def test_create_basic_portfolio(self):
        """기본 포트폴리오 생성 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25
        )
        
        assert portfolio.user_id == 1
        assert portfolio.user_name == "테스트유저"
        assert portfolio.age == 25
        assert portfolio.education == []
        assert portfolio.skills == []
    
    def test_create_portfolio_with_required_json_structure(self):
        """요청된 JSON 구조로 포트폴리오 생성 테스트"""
        json_data = {
            "user_id": 1,
            "user_name": "asdf",
            "age": 23,
            "education": []
        }
        
        portfolio = Portfolio(**json_data)
        
        assert portfolio.user_id == 1
        assert portfolio.user_name == "asdf"
        assert portfolio.age == 23
        assert portfolio.education == []
    
    def test_portfolio_with_education(self):
        """교육 이력이 포함된 포트폴리오 테스트"""
        education = EducationItem(
            institution="테스트 대학교",
            degree="학사"
        )
        
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25,
            education=[education]
        )
        
        assert len(portfolio.education) == 1
        assert portfolio.education[0].institution == "테스트 대학교"
    
    def test_add_education(self):
        """교육 이력 추가 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25
        )
        
        education = EducationItem(institution="새 대학교")
        portfolio.add_education(education)
        
        assert len(portfolio.education) == 1
        assert portfolio.education[0].institution == "새 대학교"
    
    def test_add_skill(self):
        """스킬 추가 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25
        )
        
        portfolio.add_skill("Python")
        portfolio.add_skill("JavaScript")
        portfolio.add_skill("Python")  # 중복 추가
        
        assert len(portfolio.skills) == 2
        assert "Python" in portfolio.skills
        assert "JavaScript" in portfolio.skills
    
    def test_remove_skill(self):
        """스킬 제거 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25,
            skills=["Python", "JavaScript", "React"]
        )
        
        portfolio.remove_skill("JavaScript")
        
        assert len(portfolio.skills) == 2
        assert "JavaScript" not in portfolio.skills
        assert "Python" in portfolio.skills
    
    def test_update_bio(self):
        """자기소개 업데이트 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25
        )
        
        new_bio = "새로운 자기소개입니다."
        portfolio.update_bio(new_bio)
        
        assert portfolio.bio == new_bio
    
    def test_to_metadata_dict(self):
        """메타데이터 딕셔너리 변환 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트유저",
            age=25,
            email="test@example.com",
            skills=["Python", "JavaScript"]
        )
        
        metadata = portfolio.to_metadata_dict()
        
        assert metadata["user_id"] == 1
        assert metadata["user_name"] == "테스트유저"
        assert metadata["age"] == 25
        assert metadata["email"] == "test@example.com"
        assert metadata["skills_count"] == 2
        assert metadata["education_count"] == 0
    
    def test_from_json_metadata(self):
        """JSON 메타데이터에서 포트폴리오 생성 테스트"""
        json_data = {
            "user_id": 1,
            "user_name": "JSON유저",
            "age": 30,
            "email": "json@example.com",
            "skills": ["Python", "Django"]
        }
        
        portfolio = Portfolio.from_json_metadata(json_data)
        
        assert portfolio.user_id == 1
        assert portfolio.user_name == "JSON유저"
        assert portfolio.age == 30
        assert portfolio.email == "json@example.com"
        assert len(portfolio.skills) == 2


class TestPortfolioValidation:
    """Portfolio 유효성 검사 테스트"""
    
    def test_valid_age(self):
        """유효한 나이 범위 테스트"""
        # 유효한 나이
        portfolio = Portfolio(user_id=1, user_name="테스트", age=25)
        assert portfolio.age == 25
        
        # 경계값 테스트
        portfolio_min = Portfolio(user_id=1, user_name="테스트", age=0)
        assert portfolio_min.age == 0
        
        portfolio_max = Portfolio(user_id=1, user_name="테스트", age=150)
        assert portfolio_max.age == 150
    
    def test_invalid_age(self):
        """유효하지 않은 나이 테스트"""
        with pytest.raises(ValueError):
            Portfolio(user_id=1, user_name="테스트", age=-1)
        
        with pytest.raises(ValueError):
            Portfolio(user_id=1, user_name="테스트", age=151)
    
    def test_valid_email(self):
        """유효한 이메일 테스트"""
        portfolio = Portfolio(
            user_id=1,
            user_name="테스트",
            age=25,
            email="test@example.com"
        )
        assert portfolio.email == "test@example.com"
    
    def test_invalid_email(self):
        """유효하지 않은 이메일 테스트"""
        with pytest.raises(ValueError):
            Portfolio(
                user_id=1,
                user_name="테스트",
                age=25,
                email="invalid-email"
            )
    
    def test_user_name_validation(self):
        """사용자 이름 유효성 검사 테스트"""
        # 유효한 이름
        portfolio = Portfolio(user_id=1, user_name="유효한이름", age=25)
        assert portfolio.user_name == "유효한이름"
        
        # 공백 제거 테스트
        portfolio_with_spaces = Portfolio(user_id=1, user_name="  이름  ", age=25)
        assert portfolio_with_spaces.user_name == "이름"
        
        # 빈 이름 테스트
        with pytest.raises(ValueError):
            Portfolio(user_id=1, user_name="", age=25)
        
        with pytest.raises(ValueError):
            Portfolio(user_id=1, user_name="   ", age=25)


class TestUtilityFunctions:
    """유틸리티 함수 테스트"""
    
    def test_create_portfolio_from_basic_info(self):
        """기본 정보로 포트폴리오 생성 함수 테스트"""
        portfolio = create_portfolio_from_basic_info(
            user_id=1,
            user_name="기본유저",
            age=25
        )
        
        assert portfolio.user_id == 1
        assert portfolio.user_name == "기본유저"
        assert portfolio.age == 25
        assert portfolio.education == []
    
    def test_validate_portfolio_metadata(self):
        """포트폴리오 메타데이터 유효성 검사 함수 테스트"""
        # 유효한 메타데이터
        valid_metadata = {
            "user_id": 1,
            "user_name": "테스트",
            "age": 25
        }
        assert validate_portfolio_metadata(valid_metadata) == True
        
        # 유효하지 않은 메타데이터
        invalid_metadata = {
            "user_id": 1,
            "user_name": "",  # 빈 이름
            "age": 25
        }
        assert validate_portfolio_metadata(invalid_metadata) == False


if __name__ == "__main__":
    # pytest를 사용해서 테스트 실행
    pytest.main([__file__, "-v"])
