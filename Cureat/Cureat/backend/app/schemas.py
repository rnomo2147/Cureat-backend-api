from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import re
from pydantic import ConfigDict

# 유저 스키마
class UserCreate(BaseModel):
    name : str = Field(..., example="홍길동")
    birthdate: date = Field(..., example="1995-10-24")
    gender : str = Field(..., example="남자")
    email : EmailStr = Field(..., example="user@example.com")
    phone : str = Field(..., example="01012345678")
    address : str = Field(..., example = "서울시 강남구 테헤란로")
    interests : Optional[str] = Field(None, example="데이트, 회식, 가족모임")
    allergies : bool =Field(False)
    allergies_detail : Optional[str] = Field(None, example = "땅콩, 새우")
    password: str = Field(..., min_length=8)

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    is_verified: bool
    
    # Pydantic v2 호환
    model_config = ConfigDict(from_attributes=True)

# 새로운 사용자 관심사 업데이트 스키마 추가
class UserUpdateInterests(BaseModel):
    interests: Optional[str] = Field(None, example="데이트, 회식, 가족모임")

# 맛집 스키마
class RestaurantDetail(BaseModel):
    id: Optional[int] = None
    name: str
    address: Optional[str] = None
    image_url: Optional[str] = None
    categories: Optional[str] = None
    
    # Pydantic v2 호환
    model_config = ConfigDict(from_attributes=True)

# API 스키마
class ChatRequest(BaseModel):
    user_id: int
    prompt: str

class RecommendationResponse(BaseModel):
    answer: str
    restaurants: List[RestaurantDetail]

class CourseRequest(BaseModel):
    user_id: int
    location: str = Field(..., example="서울 강남역")
    start_time: str = Field(..., example="14:00")
    end_time: str = Field(..., example="20:00")
    theme: str

class CourseDetail(BaseModel):
    title: str
    steps: List[RestaurantDetail]
    description: Optional[str] = None

class CourseResponse(BaseModel):
    answer: str
    courses: List[CourseDetail]

# 리뷰 스키마
class ReviewCreate(BaseModel):
    user_id: int
    restaurant_id: int
    content: str
    rating: int

class Review(ReviewCreate):
    id: int
    created_at: datetime
    
    # Pydantic v2 호환
    model_config = ConfigDict(from_attributes=True)

class PostEditExecutionCreate(BaseModel):
    post_id: int
    edit_value: str
    payload: Optional[Dict[str, Any]] = None

class PostEditExecution(PostEditExecutionCreate):
    id: int
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 기타 스키마
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
# 맛집 스키마
class RestaurantCreate(BaseModel):
    name: str
    address: Optional[str] = None
    image_url: Optional[str] = None

# 검색 기록 스키마
class SearchLogCreate(BaseModel):
    query: str