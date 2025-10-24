from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from fastapi.middleware.cors import CORSMiddleware
import os

# ====================================================================
# 🚨 중요: 여기에 실제 유효한 Google Gemini API 키를 넣어주세요.
# 환경 변수 사용을 권장합니다.
# ====================================================================
GEMINI_API_KEY = "AIzaSyDL48fS85-M0U-uw-bGiBtHaqKtp8HMc8s" 

# 클라이언트 초기화
# API 키가 설정되어 있지 않으면 에러가 발생할 수 있습니다.
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    print("경고: API 키 초기화에 실패했습니다. 유효한 키를 설정해주세요.")
    client = None

app = FastAPI()

# 프론트엔드(HTML)에서 백엔드(FastAPI)로 요청을 보낼 수 있도록 CORS 설정
# 개발 환경에서는 모든 출처(*)를 허용합니다.
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiaryEntry(BaseModel):
    """프론트엔드에서 전송되는 일기 데이터 모델"""
    title: str
    content: str
    tags: list[str]

@app.post("/api/summarize-diary")
def summarize_diary(entry: DiaryEntry):
    """
    일기 내용을 받아 Gemini API를 사용해 요약합니다.
    """
    # 제목과 내용을 합쳐서 요약 프롬프트 생성
    full_text = f"제목: {entry.title}\n\n내용: {entry.content}"
    
    # AI에게 요약 요청을 위한 프롬프트
    prompt = (
        f"다음 일기 내용을 3줄 이내로 핵심만 간결하게 요약해주세요. "
        f"친절한 어투로 한국어로 응답해야 합니다.   \n\n일기:\n---\n{full_text}\n---"
    )
    
    if not client or not GEMINI_API_KEY:
        return {
            "summary": "AI 요약을 실행하려면 `main.py` 파일의 `GEMINI_API_KEY`를 설정해주세요.",
            "status": "warning"
        }
        
    try:
        # Gemini 2.5 Flash 모델 사용
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        return {
            "summary": response.text.strip(),
            "status": "success"
        }
    except Exception as e:
        # 오류 발생 시 상세 로그 출력
        print(f"Gemini API Error: {e}")
        return {
            "summary": "AI 요약 중 API 통신 오류가 발생했습니다. 키 유효성 및 서버 로그를 확인해주세요.",
            "status": "error"
        }

@app.get("/")
def read_root():
    return {"message": "AI Diary Summarization Service is running. Use /api/summarize-diary endpoint."}
