import os
import re
import requests
import json
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from . import models, schemas, nlpService
import xml.etree.ElementTree as ET

# .env 파일에서 환경변수 로드
load_dotenv()

# API Key 및 모델 설정
# Gemini API 설정
genai.configure(api_key=os.getenv("GENAI_API_KEY"))
# Naver API 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 사용할 Gemini 모델 객체 생성
gemini_model = genai.Model.get("gemini-1.5-flash")

# 외부 API 호출 헬퍼 함수
def _call_naver_api(url: str, params: dict = None, headers: dict = None):
    try:
        response = requests.get(url,params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"네이버 API 호출 중 오류 발생: {url}, {e}")
        return None

# 네이버 장소 검증 함수
def verify_place_with_naver(place_name: str):
    """네이버 검색으로 장소를 검증하고 기본 정보와 이미지 URL을 반환합니다."""
    place_info = _call_naver_api(
        "https://openapi.naver.com/v1/search/local.json",
        params={"query": place_name, "display": 1},
        headers={"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    )
    if not (place_info and place_info.get("items")): return None
    
    # HTML 태그 제거
    verified_place = place_info.get("items")[0]

# 이미지 정보 조회
    image_info = _call_naver_api(
        "https://openapi.naver.com/v1/search/image",
        params={"query": f"{place_name} 음식", "display": 1, "sort": "sim"},
        headers={"X-Naver-Client-Id": NAVER_CLIENT_ID, "X-Naver-Client-Secret": NAVER_CLIENT_SECRET}
    )
    if image_info and image_info.get("items"):
        verified_place['image_url'] = image_info["items"][0].get('link')
    return verified_place

def crawl_reviews_for_summary(place_name: str) -> List[str]:
    """
    특정 장소에 대한 리뷰 30~50개를 웹 크롤링합니다.
    (주의: 실제 구현 시에는 특정 사이트의 구조에 맞춰 정교하게 만들어야 합니다)
    """
    print(f"'{place_name}'에 대한 리뷰 크롤링 시뮬레이션...")
    # 예시: 네이버 'VIEW' 검색 결과에서 블로그 본문 일부를 가져온다고 가정
    # 실제로는 beautifulsoup4를 사용해 HTML을 파싱해야 합니다.
    return [
        f"{place_name} 정말 맛있어요! 인생 맛집 등극!",
        "분위기는 좋은데 가격이 좀 비싸요. 그래도 데이트하기엔 최고.",
        "이 글은 업체로부터 소정의 원고료를 받아 작성되었습니다.", # 광고 예시
        "정말... 할많하않... 다신 안 갈듯.",
        "뷰가 미쳤어요! 음식 맛은 평범한데 사진 찍으러 가기엔 좋아요."
    ] * 6 # 30개 리뷰 예시

def filter_ad_reviews(reviews: List[str]) -> List[str]:
    """규칙과 AI를 사용해 광고성/바이럴 리뷰를 필터링합니다."""
    clean_reviews = []
    ad_keywords = ["소정의 원고료", "제공받아", "체험단", "광고 포함"]
    
    for review in reviews:
        # 1. 명시적인 광고 키워드가 있으면 1차로 필터링
        if any(keyword in review for keyword in ad_keywords):
            continue
        
        # 2. (선택적) Gemini를 이용한 2차 필터링
        # prompt = f"다음 리뷰가 광고성/바이럴 마케팅인지 '예' 또는 '아니오'로만 답해줘: \"{review}\""
        # response = model.generate_content(prompt)
        # if '예' in response.text:
        #     continue
        
        clean_reviews.append(review)
    print(f"광고 필터링 후 {len(clean_reviews)}개의 유효한 리뷰 확보.")
    return clean_reviews



# 맛집 추천 로직
def get_restaurant_summary_and_vectorize(place_name: str):
    """
    웹 크롤링, 필터링, AI 요약을 거쳐 식당의 상세 정보와 벡터를 생성합니다.
    """
    # 1. 웹에서 리뷰 30~50개를 크롤링합니다.
    crawled_reviews = crawl_reviews_for_summary(place_name)
    
    # 2. 광고성 리뷰를 필터링합니다.
    filtered_reviews = filter_ad_reviews(crawled_reviews)
    
    if not filtered_reviews:
        return None, None # 요약할 리뷰가 없으면 종료

    # 3. 깨끗한 리뷰들을 Gemini에 보내 상세 정보 요약을 요청합니다.
    reviews_text = "\n".join(filtered_reviews)
    
    # 1. Gemini에게 맛집 3곳의 '이름'과 상세 요약 정보'를 모두 요청하는 프롬프트
    prompt = f"""
    [지시]
    너는 맛집 정보를 누구보다 잘 아는 전문가야.
    웹 검색을 통해서 아래 사용자 정보와 프롬프트 요청에 가장 적절한 
    각 맛집에 대한 상세 정보도 함께 찾아서 아래 [답변 형식]에 맞춰 완벽한 JSON 배열로만 답변해줘.
    광고성 리뷰, 바이럴 마케팅 리뷰가 들어가면 안 돼.

    
    [사용자 정보]
    - 관심사 : {user_interests}
    - 알러지 : {user.allergies_details if user.allergies else '없음'}
    - 성별 : {gender}
    - 나이 : {birthdate}
     
    [사용자 요청]
    "{prompt}"   
    
    [답변 형식]
    [
     {{
        "name": "추천 맛집 이름 1",
        "address": "맛집 주소",
        "summary_pros": ["장점1", "장점2", "장점3"],
        "summary_cons": ["단점1", "단점2", "단점3"],
        "keywords": ["키워드1", "키워드2", "키워드3"],
        "signature_menu": ["시그니처 메뉴1", "시그니처 메뉴2", "시그니처 메뉴3"],
        "price_range": "가격대"(예: 1~2만원대),
        "opening_hours": "영업시간"(예: 매일 11:00~22:00, 브레이크타임 15:00~17:00, 월요일 휴무),
        "parking": "주차 가능 여부"(예: 가능, 불가능, 유료),
        "phone": "전화번호",
        "nearby_attractions": ["주변 놀거리1", "주변 놀거리2", "주변 놀거리3"],
     }},
     {{
         "place_name": "추천 맛집 이름 2",
         ... (위와 동일한 형식) ...
     }},
     {{
         "place_name": "추천 맛집 이름 3",
         ... (위와 동일한 형식) ...
     }}
        [주의사항]
        - 실제 존재하는 맛집이 맞는지 반드시 확인해야 해.
        - JSON 배열 형식을 반드시 지켜야 해.
        - 사용자의 관심사와 알러지 정보를 반드시 반영해야 해.
    ]
    """
    
    try:
        gemini_response = model.generate_content(prompt)
        recommended_places_names = re.findall(r'\[(.*?)\]', gemini_response.text)
        
        verified_restaurants = []
        for name in recommended_places_names[:3]:
            # 1. 네이버 API로 기본 정보 검증
            place_basic_info = verify_place_with_naver(name)
            if place_basic_info:
                # 2. 상세 정보 생성 (크롤링 -> 필터링 -> 요약 -> 벡터화)
                summary_info, vector = get_restaurant_summary_and_vectorize(name)
                
                # (향후 작업) 여기서 summary_info와 vector를 DB에 저장/업데이트 하는 crud 함수를 호출합니다.
                # 예: crud.update_restaurant_summary(db, restaurant_id, summary_info, vector)
                
                # 3. 프론트엔드에 전달할 최종 데이터 조합
                final_data = {
                    "name": place_basic_info.get('title', '').replace('<b>', '').replace('</b>', ''),
                    "address": place_basic_info.get('roadAddress'),
                    "mapx": place_basic_info.get('mapx'),
                    "mapy": place_basic_info.get('mapy'),
                    "image_url": place_basic_info.get('image_url'),
                    **summary_info # 요약된 상세 정보를 여기에 추가
                }
                verified_restaurants.append(final_data)
        
        if verified_restaurants:
            return {"answer": "맛집을 찾았어요! 사진을 터치해 상세 정보를 확인해보세요.", "restaurants": verified_restaurants}
        else:
            return {"answer": "맛집을 찾을 수 없었어요.", "restaurants": []}
            
    except Exception as e:
        print(f"Recommendation error: {e}")
        return {"answer": "추천 생성 중 문제가 발생했습니다.", "restaurants": []}


def create_date_course(request: schemas.CourseRequest, user: models.User):
    """사용자 정보와 제약 조건을 바탕으로 3가지 데이트 코스를 생성합니다."""
    prompt = f"""
    [지시]
    당신은 최고의 데이트 코스 플래너입니다.
    아래 사용자 정보와 제약 조건을 모두 고려하여, 최적의 데이트 코스 3가지를 추천해주세요.
    각 장소의 예상 소요 시간, 영업 시간, 날씨(현재 서울 날씨) 등을 종합적으로 고려해야 합니다.

    [사용자 정보]
    - 관심사: {user.interest}
    
    [제약 조건]
    - 지역: {request.location}
    - 일정: {request.start_time} 부터 {request.end_time} 까지
    - 테마/목적: {request.theme}

    [답변 형식]
    각 코스는 "코스 1: [장소1] -> [장소2] -> [장소3]..." 형식으로 추천해줘.
    """
    try:
        response = model.generate_content(prompt)
        # Gemini 답변을 파싱하여 3가지 코스로 분리하는 로직
        courses = [line.strip() for line in response.text.split('\n') if line.strip().startswith("코스")]
        return {"courses": courses if courses else ["요청에 맞는 코스를 생성하지 못했습니다."]}
    except Exception as e:
        print(f"Course generation error: {e}")
        return {"courses": ["죄송합니다. 코스 생성 중 문제가 발생했습니다."]}