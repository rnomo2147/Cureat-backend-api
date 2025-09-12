from pydantic import BaseModel, Field, EmailStr, validator # pydantic의 BaseModel, Field, EmailStr, validator 임포트
from typing import Optional # Optional 임포트
from datetime import date, datetime # date, datetime 임포트
import re # 정규표현식 모듈 임포트
from typing import List # List 임포트

# 유저 스키마

# User 모델 기본 필드
class UserCreate(BaseModel):
    """회원가입 요청 시 받을 데이터 형식"""
    # 이름
    name : str = Field(..., example="홍길동")
    # 생년월일 : YYYYMMDD 형식
    birthdate: date = Field(..., example="1995-10-24")
    # 성별 : 남자, 여자
    gender : str = Field(..., example="남자")
    # 이메일
    email : EmailStr = Field(..., example="user@example.com")
    # 연락처 : 01012345678 형식 (11자리)
    phone : str = Field(..., example="01012345678")
    # 집 주소
    address : str = Field(..., example = "서울시 강남구 테헤란로")
    # 관심사 : 데이트, 회식, 가족모임 등 
    interests : Optional[str] = Field(None, example="데이트, 회식, 가족모임")
    # 알러지 여부
    allergies : bool =Field(False)
    # 알러지 정보
    allergies_detail : Optional[str] = Field(None, example = "땅콩, 새우")
    # 비밀번호 설정
    password : str = Field(..., min_length=8, max_length=20, example= "1q2w3e4r!")
    
# API 응답으로 보낼 사용자 정보 형식 정의 (비밀번호 제외)
class User(BaseModel):
    id : int # 사용자 ID
    name : str # 사용자 이름
    birthdate : date # 사용자 생년월일
    email : EmailStr # 사용자 이메일
    phone : str # 사용자 전화번호
    address : str # 사용자 주소
    interests : Optional[str] # 사용자 관심사
    allergies : bool # 사용자 알레르기
    allergies_detail : Optional[str] # 사용자 알레르기 상세
    is_verified : bool # 사용자 이메일 인증 여부

    class Config : # Config 클래스
        orm_mode=True # ORM 모드 활성화

# 음식점 스키마
class RestaurantDetail(BaseModel): # 가게 기본 필드
    name: str # 가게 이름
    address: str # 가게 주소
    image_url: Optional[str] = None # 가게 이미지 URL
    mapx : Optional[str] = None # 가게 위치 X 좌표
    mapy : Optional[str] = None # 가게 위치 Y 좌표    
    
    is_favorite : Optional[bool] = None # 즐겨찾기 여부
    view_count : int = Field(default=0) # 조회수
    like_count : int = Field(default=0) # 좋아요 수
    dislike_count : int = Field(default=0) # 싫어요 수
    bookmark_count : int = Field(default=0) # 북마크 수
    comment_count : int = Field(default=0) # 댓글 수
    share_count : int = Field(default=0) # 공유 수
    is_favorite_count : int = Field(default=0) # 즐겨찾기 수
    
    # AI 요약 정보
    summary_pros: Optional[List[str]] = Field(None, description="음식점 장점 3가지 요약")
    summary_cons: Optional[List[str]] = Field(None, description="음식점 단점 3가지 요약")
    keywords: Optional[List[str]] = Field(None, description="음식점 키워드 5가지")
    nearby_attractions: Optional[List[str]] = Field(None, description="주변 놀거리 3가지")
    signature_menu: Optional[str] = Field(None, description="대표 메뉴")
    summary_phone: Optional[str] = Field(None, description="전화번호")
    summary_parking: Optional[str] = Field(None, description="주차 정보")
    summary_price: Optional[str] = Field(None, description="가격대")
    summary_opening_hours: Optional[str] = Field(None, description="영업시간")
    
    class Config: # Config 클래스
        orm_mode = True # ORM 모드 활성화

# --- API Schemas ---

class ChatRequest(BaseModel):
    """맛집 추천 요청 시 받을 데이터 형식"""
    user_id: int
    prompt: str

class RecommendationResponse(BaseModel):
    """맛집 추천 API의 최종 응답 형식"""
    answer: str # AI 응답 메시지
    restaurants: List[RestaurantDetail]

class CourseRequest(BaseModel):
    """코스 추천 요청 시 받을 데이터 형식"""
    user_id: int
    location: str = Field(..., example="서울 강남역")
    start_time: str = Field(..., example="14:00")
    end_time: str = Field(..., example="20:00")
    theme: str

class CourseDetail(BaseModel):
    """하나의 데이트 코스를 나타내는 스키마"""
    title: str # 예: "코스 1: 성수동 감성 카페와 예술 산책"
    steps: List[RestaurantDetail] # 코스에 포함된 각 장소의 상세 정보 리스트

class CourseResponse(BaseModel):
    """코스 추천 API의 최종 응답 형식"""
    courses: List[CourseDetail]


# 리뷰 스키마

class ReviewCreate(BaseModel):
    """리뷰 생성 시 받을 데이터 형식"""
    user_id: int
    restaurant_id: int
    content: str
    rating: str = Field(..., ge=1, le=5) # 1~5점 사이의 평점

class Review(ReviewCreate):
    """API 응답으로 보낼 리뷰 정보 형식"""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
