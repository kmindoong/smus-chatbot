import uvicorn
from fastapi import FastAPI, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time
from fastapi.responses import FileResponse # ★ 1. FileResponse 임포트
from pathlib import Path # ★ 2. Path 임포트

# 1. FastAPI 앱 인스턴스 생성
app = FastAPI()

# ★ 3. 프론트엔드 파일 경로 설정
# (fastapi_app.py 기준, 상위 폴더로 나간 뒤 frontend 폴더)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# 2. CORS (Cross-Origin Resource Sharing) 설정
# (기존과 동일)
origins = [
    "http://localhost",
    "http://localhost:8080",
    "null", 
    "*"     # (배포 후에는 EB URL로 변경)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 요청(Request) 바디 모델 정의
class ChatRequest(BaseModel):
    message: str

# 4. 응답(Response) 바디 모델 정의
class ChatResponse(BaseModel):
    response: str

# 5. /chat API 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    # (기존과 동일 - 가짜 답변 로직)
    user_prompt = request.message
    time.sleep(0.5) 
    
    if user_prompt == "담당자 정보 알려줘":
        bot_response = "담당자 정보입니다: 챗봇 운영 (김OO 매니저), 데이터 분석 (이XX 매니저)"
    elif user_prompt == "데이터를 활용하고 싶은데 신청 방법은?":
        bot_response = "데이터 활용 신청은 '통합데이터분석환경' 포털을 통해 가능합니다. 하단 링크를 클릭해 주세요."
    elif user_prompt == "안전보건 데이터를 확인하고 싶어, 어떤 테이블을 확인해야해?":
        bot_response = "안전보건 데이터는 'HSE_DAILY_REPORT' 테이블과 'SAFETY_ACCIDENT_LOG' 테이블을 확인해 보시는 것을 권장합니다."
    else:
        bot_response = f"'{user_prompt}'에 대해 답변을 생성 중입니다. (아직 구현되지 않은 기능)"

    return ChatResponse(response=bot_response)

# ★ 6. (신규) HTML 서빙 엔드포인트 ★

@app.get("/chatbot.html")
async def get_chatbot_html():
    """chatbot.html 파일을 서빙합니다."""
    return FileResponse(FRONTEND_DIR / "chatbot.html")

@app.get("/")
async def get_index_html():
    """루트 URL(/) 요청 시 index.html 파일을 서빙합니다."""
    return FileResponse(FRONTEND_DIR / "index.html")

# 7. (로컬 테스트용) 서버 실행
if __name__ == "__main__":
    pass