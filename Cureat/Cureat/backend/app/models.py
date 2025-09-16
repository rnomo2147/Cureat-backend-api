# backend/app/models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    birthdate = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    interests = Column(String, nullable=True)
    allergies = Column(Boolean, default=True)
    allergies_detail = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    search_logs = relationship("SearchLog", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    
# UserVector 및 RestaurantVector 모델 삭제
# SQLite 환경에서는 pgvector를 사용할 수 없으므로 제거

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    reviews = relationship("Review", back_populates="restaurant")
    categories = Column(String, nullable=True)

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_ad = Column(Boolean, default=False)
    user = relationship("User", back_populates="reviews")
    restaurant = relationship("Restaurant", back_populates="reviews")

class SearchLog(Base):
    __tablename__ = "search_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String, nullable=False)
    search_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="search_logs")

class PostEditExecution(Base):
    __tablename__ = "post_edit_executions"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, nullable=False)
    edit_value = Column(String, nullable=False)
    payload = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())