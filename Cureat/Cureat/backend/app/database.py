# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite 연결 URL로 변경
# db.sqlite3 파일을 프로젝트 루트에 생성합니다.
DATABASE_URL = "sqlite:///./db.sqlite3"

# connect_args는 SQLite 사용 시 필요
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()