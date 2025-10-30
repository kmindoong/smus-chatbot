import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # CORS 처리를 위해
import time

# 1. FastAPI 앱 인스턴스 생성
app = FastAPI()

# 2. CORS (Cross-Origin Resource Sharing) 설정
# index.html(다른 도메인)에서 오는 API 요청을 허용해야 합니다.
origins = [
    "http://localhost",
    "http://localhost:8080",
    "null", # 로컬에서 file:// 로 index.html을 열 경우
    "*"     # (보안상 실제 배포 시에는 "*" 대신 .NET 포털 도메인을 넣어야 합니다)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메소드 허용
    allow_headers=["*"], # 모든 헤더 허용
)

# 3. 요청(Request) 바디 모델 정의
# JavaScript가 {"message": "안녕하세요"} 형태로 보낼 것입니다.
class ChatRequest(BaseModel):
    message: str
    # (추가) 나중에 사용자 ID나 대화 기록을 받을 수 있습니다.
    # user_id: str
    # history: list

# 4. 응답(Response) 바디 모델 정의
class ChatResponse(BaseModel):
    response: str

# 5. (핵심) /chat API 엔드포인트 생성
@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    사용자의 채팅 메시지를 받아 봇의 응답을 반환합니다.
    """
    user_prompt = request.message
    
    # 0.5초 생각하는 척 (LLM 호출 시뮬레이션)
    time.sleep(0.5) 
    
    # Streamlit에 있던 가짜 답변 로직
    if user_prompt == "강의 계획서 찾아줘":
        bot_response = "강의 계획서 조회 메뉴로 안내해 드릴게요. [여기]를 클릭하세요."
    elif user_prompt == "휴학 신청은 어떻게 해?":
        bot_response = "휴학 신청은 [학사정보시스템 > 학적변동] 메뉴에서 하실 수 있습니다."
    elif user_prompt == "성적 조회 알려줘":
        bot_response = "이번 학기 성적 조회는 7월 25일부터 가능합니다."
    else:
        # (실제로는 여기서 LLM이나 RAG가 호출됩니다)
        bot_response = f"'{user_prompt}'에 대해 답변을 생성 중입니다. (FastAPI 응답)"

    # JSON 형태로 응답 반환
    return ChatResponse(response=bot_response)

# 6. (로컬 테스트용) 서버 실행
if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    # 터미널에서 'uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload'로 실행
    pass