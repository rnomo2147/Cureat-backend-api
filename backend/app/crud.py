from sqlalchemy.orm import Session
from backend import db
from . import models, schemas
from passlib.context import CryptContext
from datetime import datetime

# 비밀번호 해싱 설정
# bcrypt 해싱 알고리즘 사용
# deprecated="auto" 옵션은 이전에 사용되던 해싱 알고리즘을 자동으로 감지하여 처리
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

def verify_password(plain_password, hashed_password): # 비밀번호 검증 함수
    return pwd_context.verify(plain_password, hashed_password) # 평문 비밀번호와 해시된 비밀번호 비교

def get_password_hash(password): # 비밀번호 해싱 함수
    return pwd_context.hash(password) # 평문 비밀번호를 해시로 변환

# 유저 관련 CRUD 함수
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    """ID로 사용자를 조회합니다."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    # 이메일로 사용자 조회
    # 1. 입력받은 비밀번호를 안전하게 해싱
    hashed_password = get_password_hash(user.password)
    
    # 2. schemas.py의 birthdate가 date 타입이므로 문자열 변환 필용 없음
    # 3. 데이터베이스 모델(models.py) 객체 생성
    db_user = models.User(
        name=user.name,
        birthdate=user.birthdate,
        gender=user.gender,
        email=user.email,
        phone=user.phone,
        address=user.address,
        interest=user.interests,
        allergies=user.allergies,
        allergies_detail=user.allergies_detail,
        hashed_password=hashed_password,
        is_verified=False, # 이메일 인증 필드 추가 (기본값 False)
    )
    # 4. 생성된 객체를 세션에 추가하고 데이터베이스에 커밋
    db.add(db_user) # 세션에 추가
    db.commit() # 변경사항 커밋
    db.refresh(db_user) # 새로 생성된 사용자 정보 갱신
    return db_user # 생성된 사용자 반환

# 리뷰 & 검색로그 CRUD 함수
def create_review(db: Session, review: schemas.ReviewCreate):
    """새로운 리뷰를 생성합니다."""
    db_review = models.Review(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def create_search_log(db: Session, user_id: int, query: str):
    """새로운 검색 로그를 생성합니다."""
    db_log = models.SearchLog(user_id=user_id, query=query)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log