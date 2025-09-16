import os
import requests
import json
import numpy as np
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from . import models, schemas, crud
from sqlalchemy.orm import Session
from fastapi import HTTPException

# .env 파일에서 환경변수 로드
load_dotenv()

# API Key 및 모델 설정
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

# 사용할 Gemini 모델 객체 생성
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# 벡터 유사도 계산 함수 (더 이상 사용하지 않음)
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    return 0.0

# --- 맛집 추천 기능 ---
async def get_recommendation_for_user(user: models.User, prompt: str, db: Session) -> schemas.RecommendationResponse:
    # NLP 기능이 비활성화되어 벡터를 사용할 수 없습니다.
    # 따라서 추천 로직을 건너뛰고 임시 응답을 반환합니다.
    return schemas.RecommendationResponse(
        answer="현재 NLP 기능이 비활성화되어 맛집 추천을 할 수 없습니다. 개발자에게 문의하세요.",
        restaurants=[]
    )