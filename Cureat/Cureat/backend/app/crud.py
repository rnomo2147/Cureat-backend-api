from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas
from passlib.context import CryptContext
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import os

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ---------- JSON 저장 유틸 ----------

def _json_base_dir() -> Path:
    """JSON 파일을 저장할 기본 디렉토리 경로 반환"""
    return Path(__file__).resolve().parents[2] / "db" / "json_files"

def _model_to_dict(model_instance) -> Dict[str, Any]:
    """SQLAlchemy 모델 인스턴스를 직렬화 가능한 딕셔너리로 변환"""
    data = model_instance.__dict__.copy()
    data.pop('_sa_instance_state', None)
    for key, value in data.items():
        if isinstance(value, (datetime, date)):
            data[key] = value.isoformat()
    return data

def _dump_json(table_name: str, record_id: int, data: Dict[str, Any]) -> None:
    """테이블 이름으로 폴더를 생성하고 JSON 데이터를 저장합니다."""
    base_dir = _json_base_dir() / table_name
    
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = base_dir / f"{record_id}.json"
    
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- 유저 관련 CRUD ----------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.phone == phone).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        birthdate=user.birthdate,
        gender=user.gender,
        email=user.email,
        phone=user.phone,
        address=user.address,
        hashed_password=hashed_password,
        interests=user.interests,
        allergies=user.allergies,
        allergies_detail=user.allergies_detail,
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user_data = _model_to_dict(db_user)
        _dump_json("users", db_user.id, user_data)
        return db_user
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: users.phone" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )
        elif "UNIQUE constraint failed: users.email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )

def update_user_interests(db: Session, user_id: int, interests: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.interests = interests
        db.commit()
        db.refresh(user)
        user_data = _model_to_dict(user)
        _dump_json("users", user.id, user_data)
    return user

# ---------- 맛집 관련 CRUD ----------
def get_restaurant_by_id(db: Session, restaurant_id: int):
    return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

def get_restaurants_by_name(db: Session, name: str):
    return db.query(models.Restaurant).filter(models.Restaurant.name.ilike(f'%{name}%')).all()

def create_restaurant(db: Session, restaurant: schemas.RestaurantCreate):
    db_restaurant = models.Restaurant(
        name=restaurant.name,
        address=restaurant.address,
        image_url=restaurant.image_url
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    # SQLAlchemy 객체를 딕셔너리로 변환하여 전달
    restaurant_data = _model_to_dict(db_restaurant)
    _dump_json("restaurants", db_restaurant.id, restaurant_data)
    return db_restaurant

def get_all_restaurants(db: Session):
    return db.query(models.Restaurant).all()

# ---------- 리뷰 관련 CRUD ----------
def create_review(db: Session, review: schemas.ReviewCreate) -> models.Review:
    db_review = models.Review(
        user_id=review.user_id,
        restaurant_id=review.restaurant_id,
        content=review.content,
        rating=review.rating
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    review_data = _model_to_dict(db_review)
    _dump_json("reviews", db_review.id, review_data)
    return db_review

def get_restaurant_reviews(db: Session, restaurant_id: int) -> List[models.Review]:
    return db.query(models.Review).filter(models.Review.restaurant_id == restaurant_id).all()

def get_user_reviews(db: Session, user_id: int, limit: int = 10) -> List[models.Review]:
    return db.query(models.Review).filter(models.Review.user_id == user_id).order_by(models.Review.created_at.desc()).limit(limit).all()

# ---------- 검색 기록 관련 CRUD ----------
def create_search_log(db: Session, user_id: int, query: str):
    db_search_log = models.SearchLog(user_id=user_id, query=query)
    db.add(db_search_log)
    db.commit()
    db.refresh(db_search_log)
    search_log_data = _model_to_dict(db_search_log)
    _dump_json("search_logs", db_search_log.id, search_log_data)
    return db_search_log

def get_user_search_logs(db: Session, user_id: int, limit: int = 10) -> List[models.SearchLog]:
    return db.query(models.SearchLog).filter(models.SearchLog.user_id == user_id).order_by(models.SearchLog.search_at.desc()).limit(limit).all()
    
# ---------- PostEditExecution ----------
def create_post_edit_execution(db: Session, data: schemas.PostEditExecutionCreate) -> models.PostEditExecution:
    payload_text = json.dumps(data.payload, ensure_ascii=False) if data.payload is not None else None
    record = models.PostEditExecution(post_id=data.post_id, edit_value=data.edit_value, payload=payload_text)
    db.add(record)
    db.commit()
    db.refresh(record)
    _dump_json(
        "post_edit_executions",
        record.id,
        {
            "id": record.id,
            "post_id": record.post_id,
            "edit_value": record.edit_value,
            "payload": data.payload,
            "executed_at": record.executed_at.isoformat() if hasattr(record, 'executed_at') and record.executed_at else None
        }
    )
    return record