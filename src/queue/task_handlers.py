"""
태스크 핸들러들

다양한 종류의 비동기 태스크를 처리하는 핸들러 함수들
"""

import asyncio
import logging
from typing import Dict, Any
import aiofiles
import os
from src.models.portfolio import Portfolio, validate_portfolio_metadata
from src.models.activity import Activity, validate_activity_metadata
from src.managers.activity_manager import ActivityChromaManager, create_activity_manager

logger = logging.getLogger(__name__)


async def document_processing_task(data: Dict[str, Any]):
    """문서 처리 태스크"""
    try:
        file_path = data.get("file_path")
        document_id = data.get("document_id")

        if not file_path or not document_id:
            raise ValueError("file_path와 document_id가 필요합니다")

        logger.info(f"문서 처리 시작: {document_id}")

        # 파일 읽기 (비동기)
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()

        # 문서 처리 시뮬레이션 (실제로는 텍스트 분할, 전처리 등)
        await asyncio.sleep(2)  # 처리 시간 시뮬레이션

        logger.info(f"문서 처리 완료: {document_id}, 길이: {len(content)}")

        # 결과를 다른 큐로 전송하거나 데이터베이스에 저장
        return {
            "status": "success",
            "document_id": document_id,
            "content_length": len(content),
        }

    except Exception as e:
        logger.error(f"문서 처리 오류: {str(e)}")
        raise


async def embedding_generation_task(data: Dict[str, Any]):
    """임베딩 생성 태스크"""
    try:
        text = data.get("text")
        document_id = data.get("document_id")

        if not text or not document_id:
            raise ValueError("text와 document_id가 필요합니다")

        logger.info(f"임베딩 생성 시작: {document_id}")

        # 임베딩 생성 시뮬레이션
        await asyncio.sleep(3)  # 임베딩 생성 시간 시뮬레이션

        logger.info(f"임베딩 생성 완료: {document_id}")

        return {"status": "success", "document_id": document_id, "embedding_size": 384}

    except Exception as e:
        logger.error(f"임베딩 생성 오류: {str(e)}")
        raise


async def file_upload_task(data: Dict[str, Any]):
    """파일 업로드 태스크"""
    try:
        local_path = data.get("local_path")
        bucket_name = data.get("bucket_name")
        object_name = data.get("object_name")

        if not all([local_path, bucket_name, object_name]):
            raise ValueError("local_path, bucket_name, object_name이 모두 필요합니다")

        logger.info(f"파일 업로드 시작: {local_path} -> {bucket_name}/{object_name}")

        # MinIO 업로드 시뮬레이션
        await asyncio.sleep(1)  # 업로드 시간 시뮬레이션

        # 실제로는 MinIO 클라이언트 사용
        # from src.storage.minio_client import MinioClient
        # minio_client = MinioClient(...)
        # success = minio_client.upload_file(bucket_name, object_name, local_path)

        logger.info(f"파일 업로드 완료: {object_name}")

        return {"status": "success", "object_name": object_name}

    except Exception as e:
        logger.error(f"파일 업로드 오류: {str(e)}")
        raise


async def vector_database_insert_task(data: Dict[str, Any]):
    """벡터 데이터베이스 삽입 태스크"""
    try:
        document_id = data.get("document_id")
        embedding = data.get("embedding")
        metadata = data.get("metadata", {})

        if not document_id or not embedding:
            raise ValueError("document_id와 embedding이 필요합니다")

        logger.info(f"벡터 DB 삽입 시작: {document_id}")

        # 벡터 데이터베이스 삽입 시뮬레이션
        await asyncio.sleep(1)  # 삽입 시간 시뮬레이션

        # 실제로는 벡터 데이터베이스 클라이언트 사용
        # from src.database.vector_database import VectorDatabase
        # vector_db = VectorDatabase()
        # vector_db.add_document(document_id, embedding, metadata)

        logger.info(f"벡터 DB 삽입 완료: {document_id}")

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"벡터 DB 삽입 오류: {str(e)}")
        raise


async def notification_task(data: Dict[str, Any]):
    """알림 전송 태스크"""
    try:
        message = data.get("message")
        recipient = data.get("recipient")
        notification_type = data.get("type", "info")

        if not message or not recipient:
            raise ValueError("message와 recipient이 필요합니다")

        logger.info(f"알림 전송 시작: {recipient}")

        # 알림 전송 시뮬레이션
        await asyncio.sleep(0.5)

        logger.info(f"알림 전송 완료: {recipient} - {message}")

        return {"status": "success", "recipient": recipient}

    except Exception as e:
        logger.error(f"알림 전송 오류: {str(e)}")
        raise


async def portfolio_processing_task(data: Dict[str, Any]):
    """포트폴리오 메타데이터 처리 태스크"""
    try:
        portfolio_data = data.get("portfolio_data")
        user_id = data.get("user_id")

        if not portfolio_data or not user_id:
            raise ValueError("portfolio_data와 user_id가 필요합니다")

        logger.info(f"포트폴리오 처리 시작: user_id {user_id}")

        # 포트폴리오 데이터 유효성 검사
        if not validate_portfolio_metadata(portfolio_data):
            raise ValueError("유효하지 않은 포트폴리오 데이터입니다")

        # Portfolio 객체 생성
        portfolio = Portfolio.from_json_metadata(portfolio_data)

        # 포트폴리오 처리 시뮬레이션
        await asyncio.sleep(1)

        # 벡터 데이터베이스용 메타데이터 생성
        metadata = portfolio.to_metadata_dict()

        logger.info(f"포트폴리오 처리 완료: user_id {user_id}")

        return {
            "status": "success",
            "user_id": user_id,
            "portfolio_id": portfolio.user_id,
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"포트폴리오 처리 오류: {str(e)}")
        raise


async def portfolio_search_task(data: Dict[str, Any]):
    """포트폴리오 검색 태스크"""
    try:
        search_criteria = data.get("search_criteria", {})
        limit = data.get("limit", 10)

        logger.info(f"포트폴리오 검색 시작: {search_criteria}")

        # 검색 시뮬레이션
        await asyncio.sleep(1)

        # 실제로는 벡터 데이터베이스에서 검색
        # 예: age, skills, education 등을 기준으로 유사한 포트폴리오 찾기

        # 더미 검색 결과
        search_results = [
            {
                "user_id": 1,
                "user_name": "김개발",
                "similarity_score": 0.95,
                "matching_skills": ["Python", "JavaScript"],
            },
            {
                "user_id": 2,
                "user_name": "이백엔드",
                "similarity_score": 0.87,
                "matching_skills": ["Python", "Django"],
            },
        ]

        logger.info(f"포트폴리오 검색 완료: {len(search_results)}개 결과")

        return {
            "status": "success",
            "results": search_results[:limit],
            "total_count": len(search_results),
        }

    except Exception as e:
        logger.error(f"포트폴리오 검색 오류: {str(e)}")
        raise


async def recommend_activity_task(data: Dict[str, Any]):
    """대외활동 추천 태스크"""
    try:
        user_interests = data.get("user_interests", [])
        user_skills = data.get("user_skills", [])
        preferred_duration = data.get("preferred_duration_days")
        preferred_location = data.get("preferred_location")
        is_online_preferred = data.get("is_online_preferred")
        limit = data.get("limit", 10)

        logger.info(f"대외활동 추천 시작: 관심사={user_interests}, 스킬={user_skills}")

        # ActivityChromaManager 초기화
        try:
            manager = create_activity_manager()
        except Exception as e:
            logger.warning(f"ActivityChromaManager 초기화 실패, 더미 데이터 사용: {e}")
            # 더미 추천 결과
            dummy_results = [
                {
                    "postId": 2001,
                    "title": "스타트업 인큐베이팅 프로그램",
                    "company": "서울창업허브",
                    "category": "대외활동",
                    "activityField": "창업",
                    "similarity_score": 0.92,
                },
                {
                    "postId": 2002,
                    "title": "IT 해커톤 대회",
                    "company": "네이버",
                    "category": "공모전",
                    "activityField": "IT/개발",
                    "similarity_score": 0.85,
                },
            ]

            return {
                "status": "success",
                "recommendations": dummy_results[:limit],
                "total_count": len(dummy_results),
                "is_dummy": True,
            }

        # 실제 추천 시스템 호출
        await asyncio.sleep(1)  # 처리 시간 시뮬레이션

        # 사용자 맞춤 추천 수행
        from src.managers.activity_manager import recommend_activities_for_user

        recommendations = recommend_activities_for_user(
            manager=manager,
            user_interests=user_interests,
            user_skills=user_skills,
            preferred_duration_days=preferred_duration,
            preferred_location=preferred_location,
            is_online_preferred=is_online_preferred,
            n_results=limit,
        )

        # 결과 포맷팅
        formatted_results = []
        for rec in recommendations:
            if "activity" in rec:
                activity = rec["activity"]
                formatted_results.append(
                    {
                        "postId": activity.postId,
                        "title": activity.title,
                        "company": activity.company,
                        "category": activity.category,
                        "activityField": activity.activityField,
                        "activityDuration": activity.activityDuration,
                        "location": activity.location,
                        "tags": activity.tags,
                        "similarity_score": rec.get("similarity_score", 0.0),
                        "application_end_date": activity.application_end_date,
                        "is_certificate_provided": activity.is_certificate_provided,
                        "scholarship_amount": activity.scholarship_amount,
                    }
                )

        logger.info(f"대외활동 추천 완료: {len(formatted_results)}개 결과")

        return {
            "status": "success",
            "recommendations": formatted_results,
            "total_count": len(formatted_results),
            "search_criteria": {
                "user_interests": user_interests,
                "user_skills": user_skills,
                "preferred_duration_days": preferred_duration,
                "preferred_location": preferred_location,
                "is_online_preferred": is_online_preferred,
            },
        }

    except Exception as e:
        logger.error(f"대외활동 추천 오류: {str(e)}")
        raise


async def activity_search_task(data: Dict[str, Any]):
    """대외활동 검색 태스크"""
    try:
        query = data.get("query", "")
        category = data.get("category")
        activity_field = data.get("activity_field")
        company = data.get("company")
        location = data.get("location")
        min_duration = data.get("min_duration")
        max_duration = data.get("max_duration")
        is_online = data.get("is_online")
        is_paid = data.get("is_paid")
        limit = data.get("limit", 10)

        logger.info(f"대외활동 검색 시작: 쿼리='{query}', 카테고리={category}")

        # ActivityChromaManager 초기화
        try:
            manager = create_activity_manager()
        except Exception as e:
            logger.warning(f"ActivityChromaManager 초기화 실패, 더미 데이터 사용: {e}")
            # 더미 검색 결과
            dummy_results = [
                {
                    "postId": 3001,
                    "title": "창업 아이디어 공모전",
                    "company": "중소벤처기업부",
                    "category": "공모전",
                    "activityField": "창업",
                    "similarity_score": 0.88,
                }
            ]

            return {
                "status": "success",
                "results": dummy_results[:limit],
                "total_count": len(dummy_results),
                "is_dummy": True,
            }

        # 검색 필터 생성
        from src.models.activity import create_chroma_query_filter

        filters = create_chroma_query_filter(
            category=category,
            activity_field=activity_field,
            company=company,
            min_duration=min_duration,
            max_duration=max_duration,
            is_online=is_online,
            is_paid=is_paid,
            location=location,
        )

        await asyncio.sleep(0.5)  # 검색 시간 시뮬레이션

        # 실제 검색 수행
        search_results = manager.search_activities(
            query=query, n_results=limit, filters=filters if filters else None
        )

        # 결과 포맷팅
        formatted_results = []
        for result in search_results:
            if "activity" in result:
                activity = result["activity"]
                formatted_results.append(
                    {
                        "postId": activity.postId,
                        "title": activity.title,
                        "company": activity.company,
                        "category": activity.category,
                        "activityField": activity.activityField,
                        "activityDuration": activity.activityDuration,
                        "location": activity.location,
                        "tags": activity.tags,
                        "similarity_score": result.get("similarity_score", 0.0),
                        "application_end_date": activity.application_end_date,
                        "is_online": activity.is_online,
                        "is_certificate_provided": activity.is_certificate_provided,
                        "scholarship_amount": activity.scholarship_amount,
                        "benefits": activity.benefits,
                    }
                )

        logger.info(f"대외활동 검색 완료: {len(formatted_results)}개 결과")

        return {
            "status": "success",
            "results": formatted_results,
            "total_count": len(formatted_results),
            "search_query": query,
            "filters_applied": filters,
        }

    except Exception as e:
        logger.error(f"대외활동 검색 오류: {str(e)}")
        raise


async def activity_add_task(data: Dict[str, Any]):
    """대외활동 추가 태스크"""
    try:
        activity_data = data.get("activity_data")

        if not activity_data:
            raise ValueError("activity_data가 필요합니다")

        logger.info(f"대외활동 추가 시작: ID={activity_data.get('postId')}")

        # Activity 객체 생성 및 검증
        activity = Activity(**activity_data)

        # 메타데이터 유효성 검사
        metadata = activity.to_chroma_metadata()
        if not validate_activity_metadata(metadata):
            raise ValueError("대외활동 메타데이터 유효성 검사 실패")

        # ActivityChromaManager를 통해 저장
        manager = create_activity_manager()

        await asyncio.sleep(0.3)  # 저장 시간 시뮬레이션

        success = manager.add_activity(activity)

        if success:
            logger.info(f"대외활동 추가 완료: {activity.title}")
            return {
                "status": "success",
                "postId": activity.postId,
                "title": activity.title,
                "company": activity.company,
                "message": "대외활동이 성공적으로 추가되었습니다",
            }
        else:
            raise Exception("대외활동 저장에 실패했습니다")

    except Exception as e:
        logger.error(f"대외활동 추가 오류: {str(e)}")
        raise


async def activity_update_task(data: Dict[str, Any]):
    """대외활동 업데이트 태스크"""
    try:
        post_id = data.get("post_id")
        update_data = data.get("update_data")

        if not post_id or not update_data:
            raise ValueError("post_id와 update_data가 필요합니다")

        logger.info(f"대외활동 업데이트 시작: ID={post_id}")

        # ActivityChromaManager 초기화
        manager = create_activity_manager()

        # 기존 대외활동 조회
        existing_activity = manager.get_activity_by_id(post_id)
        if not existing_activity:
            raise ValueError(f"ID {post_id}에 해당하는 대외활동을 찾을 수 없습니다")

        # 업데이트 데이터 적용
        existing_data = existing_activity.dict()
        existing_data.update(update_data)
        existing_data["updated_at"] = data.get("updated_at")  # 업데이트 시간 갱신

        # 새 Activity 객체 생성
        updated_activity = Activity(**existing_data)

        await asyncio.sleep(0.3)  # 업데이트 시간 시뮬레이션

        # 업데이트 수행
        success = manager.update_activity(updated_activity)

        if success:
            logger.info(f"대외활동 업데이트 완료: {updated_activity.title}")
            return {
                "status": "success",
                "postId": updated_activity.postId,
                "title": updated_activity.title,
                "message": "대외활동이 성공적으로 업데이트되었습니다",
            }
        else:
            raise Exception("대외활동 업데이트에 실패했습니다")

    except Exception as e:
        logger.error(f"대외활동 업데이트 오류: {str(e)}")
        raise


async def activity_delete_task(data: Dict[str, Any]):
    """대외활동 삭제 태스크"""
    try:
        post_id = data.get("post_id")

        if not post_id:
            raise ValueError("post_id가 필요합니다")

        logger.info(f"대외활동 삭제 시작: ID={post_id}")

        # ActivityChromaManager 초기화
        manager = create_activity_manager()

        await asyncio.sleep(0.2)  # 삭제 시간 시뮬레이션

        # 삭제 수행
        success = manager.delete_activity(post_id)

        if success:
            logger.info(f"대외활동 삭제 완료: ID={post_id}")
            return {
                "status": "success",
                "postId": post_id,
                "message": "대외활동이 성공적으로 삭제되었습니다",
            }
        else:
            raise Exception("대외활동 삭제에 실패했습니다")

    except Exception as e:
        logger.error(f"대외활동 삭제 오류: {str(e)}")
        raise
