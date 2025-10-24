
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. 환경 변수 로드
load_dotenv()

# 2. FastAPI 앱 및 Gemini 클라이언트 초기화
app = FastAPI()

# 클라이언트 초기화 시 API 키를 자동으로 환경 변수에서 로드합니다.
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 임시 데이터베이스 역할 (실제 DB로 대체 필요)
# {user_id: [GrowthCard_data]}
GROWTH_CARD_DB = {}

# ===================================================
# 3. Pydantic 모델: 요청 본문 정의
# ===================================================

class DiarySubmitRequest(BaseModel):
    """일기 제출 API의 요청 본문 구조를 정의합니다."""
    user_id: int
    diary_text: str

# ===================================================
# 4. Gemini API 호출 함수 (비동기 처리)
# ===================================================

# FastAPI는 비동기를 선호하지만, 동기 라이브러리(google-genai)를 사용할 경우,
# 그대로 두거나, FastAPI가 백그라운드에서 동기 함수를 실행하도록 합니다.
# 여기서는 코드를 단순화하기 위해 동기 함수 그대로 유지합니다.

def generate_daily_card(diary_text):
    """일기 내용을 요약하여 DailyCard JSON을 생성합니다."""
    # ... (함수 내용은 Gemini API를 사용한 이전 코드와 동일) ...
    prompt = f"""
    사용자가 오늘 작성한 일기입니다. 다음 3가지 항목에 맞춰 요약하고 결과는 JSON 형식으로만 응답해 주세요:
    1. 제목 (5단어 이내)
    2. 요약 (50자 이내)
    3. 핵심 키워드 (3~5개, 쉼표로 구분)
    
    일기: {diary_text}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "제목": {"type": "string"},
                        "요약": {"type": "string"},
                        "핵심 키워드": {"type": "string"}
                    },
                    "required": ["제목", "요약", "핵심 키워드"]
                }
            )
        )
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Daily Card 생성 오류: {e}")
        return None


def evolve_growth_card(user_id, new_daily_card, historical_data):
    """새 DailyCard와 과거 데이터를 비교하여 Growth Card를 진화시킵니다."""
    # ... (함수 내용은 Gemini API를 사용한 이전 코드와 동일) ...
    past_growth_info = json.dumps(historical_data.get(user_id, "N/A"), ensure_ascii=False)
    
    prompt = f"""
    오늘의 요약 카드와 과거 성장 분석 데이터를 비교하여, 사용자의 성장, 변화, 또는 일관된 주제를 찾아내고,
    새로운 Growth Card 내용을 다음 JSON 형식으로 생성해 주세요.
    # ... (프롬프트 내용 생략) ...
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "Growth_Card_제목": {"type": "string"},
                        "분석_요약": {"type": "string"},
                        "다음_성장_목표_제안": {"type": "string"}
                    },
                    "required": ["Growth_Card_제목", "분석_요약", "다음_성장_목표_제안"]
                }
            )
        )
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Growth Card 진화 오류: {e}")
        return None

# ===================================================
# 5. FastAPI 엔드포인트
# ===================================================

@app.post('/api/diary/submit')
async def submit_diary(request_data: DiarySubmitRequest):
    """
    사용자의 일기를 받아 Daily Card를 생성하고 Growth Card를 진화시키는 엔드포인트.
    """
    user_id = request_data.user_id
    diary_text = request_data.diary_text

    # 1. 일일 요약 카드 생성 (Gemini 호출)
    daily_card_data = generate_daily_card(diary_text)
    
    if not daily_card_data:
        raise HTTPException(status_code=500, detail="일일 카드 생성에 실패했습니다.")
    
    # TODO: 2. 생성된 daily_card_data를 DailyCard 테이블에 저장

    # 3. 성장 카드 진화 (Gemini 호출)
    historical_data = GROWTH_CARD_DB 
    
    growth_card_data = evolve_growth_card(user_id, daily_card_data, historical_data)

    if not growth_card_data:
        raise HTTPException(status_code=500, detail="성장 카드 진화에 실패했습니다.")

    # 4. 성장 카드 데이터 업데이트/저장
    GROWTH_CARD_DB[user_id] = growth_card_data 
    # TODO: growth_card_data를 GrowthCard 테이블에 저장/업데이트

    return {
        "message": "일기 처리 및 성장 카드 진화 완료",
        "daily_card": daily_card_data,
        "new_growth_card": growth_card_data
    }