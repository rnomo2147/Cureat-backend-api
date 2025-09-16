# backend/app/main.py

import os
import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
# .env 로드
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db, Base, engine
from . import models, schemas, crud, service
from starlette.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

from sqlalchemy import text # <-- 이 줄을 추가했습니다.

def ensure_column_exists():
    with engine.connect() as conn:
        # SQLite에서 테이블 구조 확인
        result = conn.execute(text("PRAGMA table_info(restaurants);"))
        columns = [row[1] for row in result.fetchall()]
        if "categories" not in columns:
            conn.execute(text("ALTER TABLE restaurants ADD COLUMN categories TEXT;"))
            print("✅ Added 'categories' column to restaurants table")

ensure_column_exists()

# FastAPI 앱 인스턴스 생성
app = FastAPI()

# CORS 미들웨어 추가 (모든 도메인 허용)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# Naver API 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 외부 API 호출 함수
def verify_place_with_naver(place_name: str):
    """네이버 검색 API로 장소의 실존 여부와 정보 검증"""
    url = "https://openapi.naver.com/v1/search/local.json"
    params = {"query": place_name, "display": 1}
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"네이버 API 호출 중 오류 발생: {e}")
        return None

# ---------- 유저 엔드포인트 ----------

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # 전화번호 중복 확인 로직 추가
    db_user = crud.get_user_by_phone(db, phone=user.phone)
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
        
    return crud.create_user(db=db, user=user)

@app.put("/users/{user_id}/interests", response_model=schemas.User)
def update_user_interests(user_id: int, interests: schemas.UserUpdateInterests, db: Session = Depends(get_db)):
    db_user = crud.update_user_interests(db=db, user_id=user_id, interests=interests.interests)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# ---------- 맛집 관련 엔드포인트 ----------

@app.post("/restaurants/", response_model=schemas.RestaurantDetail, status_code=status.HTTP_201_CREATED)
def create_restaurant(restaurant: schemas.RestaurantCreate, db: Session = Depends(get_db)):
    """새로운 맛집 정보를 생성합니다."""
    return crud.create_restaurant(db, restaurant)

@app.get("/restaurants/search/", response_model=List[schemas.RestaurantDetail])
def search_restaurants(name: str, db: Session = Depends(get_db)):
    """이름으로 맛집을 검색합니다."""
    restaurants = crud.get_restaurants_by_name(db, name)
    if not restaurants:
        raise HTTPException(status_code=404, detail="Restaurants not found")
    return restaurants

@app.get("/restaurants/{restaurant_id}", response_model=schemas.RestaurantDetail)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """특정 ID의 맛집 정보를 조회합니다."""
    restaurant = crud.get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant

# ---------- 추천 기능 엔드포인트 (기능 미구현) ----------

@app.get("/restaurants/recommendations/{user_id}", response_model=schemas.RecommendationResponse)
def get_recommendations_for_user(user_id: int, db: Session = Depends(get_db)):
    """
    NLP 기능이 비활성화되어 벡터를 사용할 수 없습니다.
    따라서 추천 로직을 건너뛰고 임시 응답을 반환합니다.
    """
    answer = "현재 추천 기능이 비활성화되어 맛집 추천을 할 수 없습니다. 개발자에게 문의하세요."
    return schemas.RecommendationResponse(answer=answer, restaurants=[])

# ---------- 리뷰 관련 엔드포인트 ----------
@app.post("/reviews/", response_model=schemas.Review)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    """리뷰를 생성합니다."""
    return crud.create_review(db=db, review=review)

# ---------- 검색 기록 관련 엔드포인트 ----------
@app.post("/users/{user_id}/search_logs")
def create_search_log(user_id: int, query: schemas.SearchLogCreate, db: Session = Depends(get_db)):
    """사용자 검색 기록을 생성합니다."""
    return crud.create_search_log(db=db, user_id=user_id, query=query.query)

# ---------- JSON 저장 엔드포인트 ----------
@app.post("/post_edit_executions/", response_model=schemas.PostEditExecution)
def create_post_edit_execution_api(data: schemas.PostEditExecutionCreate, db: Session = Depends(get_db)):
    """데이터를 JSON 파일로 저장합니다."""
    return crud.create_post_edit_execution(db=db, data=data)