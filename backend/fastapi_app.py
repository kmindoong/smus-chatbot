import uvicorn
from fastapi import FastAPI, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time
from pathlib import Path

# ★ 1. StaticFiles 임포트
from fastapi.staticfiles import StaticFiles

# 2. FastAPI 앱 인스턴스 생성
app = FastAPI()

# ★ 3. 프론트엔드 파일 경로 설정
# (fastapi_app.py 기준, 상위 폴더로 나간 뒤 frontend 폴더)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# 4. CORS 설정
origins = [
    "http://localhost",
    "http://localhost:8000",
    "null", 
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. 요청/응답 모델
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# 6. /chat API 엔드포인트 (기존과 동일)
@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    user_prompt = request.message
    time.sleep(0.5) 
    
    if user_prompt == "담당자 정보 알려줘":
        bot_response = "담당자 정보입니다: 챗봇 운영 (김OO 매니저), 데이터 분석 (이XX 매니저)"
    elif user_prompt == "데이터를 활용하고 싶은데 신청 방법은?":
        bot_response = "데이터 활용 신청은 '통합데이터분석환경' 포털을 통해 가능합니다. 상단 바로가기 버튼을 클릭해 주세요."
    elif user_prompt == "안전보건 데이터를 확인하고 싶어, 어떤 테이블을 확인해야 해?":
        bot_response = "안전보건 데이터는 'HSE_DAILY_REPORT' 테이블과 'SAFETY_ACCIDENT_LOG' 테이블을 확인해 보시는 것을 권장합니다."
    else:
        bot_response = f"'{user_prompt}'(이)라는 메시지를 받았습니다. 하지만 이 질문에 대한 답변은 아직 준비되지 않았어요."

    return ChatResponse(response=bot_response)

# ★ 7. (신규) 정적 파일 서빙 ★
# frontend 폴더 전체를 / 경로에 마운트합니다.
# html=True는 / 요청 시 index.html을 자동으로 서빙하게 합니다.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

# (기존 / , /chatbot.html, /style.css, /images/* 라우트는 모두 삭제합니다)

# 8. (로컬 테스트용) 서버 실행
if __name__ == "__main__":
    # 터미널에서 실행: uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
    pass