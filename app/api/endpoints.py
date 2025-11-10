# app/api/endpoints.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.security import authenticate_user 
from app.services import bedrock_service, dynamodb_service
from app.core.config import settings # ⭐️ settings 임포트

router = APIRouter()

# ⭐️ [추가] 프론트엔드 설정을 위한 모델
class AppConfig(BaseModel):
    chatbotUiUrl: str

# ⭐️ [추가] 프론트엔드에 설정을 전달하는 엔드포인트
@router.get("/config", response_model=AppConfig)
def get_app_config():
    """
    프론트엔드에 필요한 환경별 설정을 반환합니다.
    (예: 챗봇 iframe의 src URL)
    """
    return AppConfig(chatbotUiUrl=settings.CHATBOT_UI_URL)
class ChatRequest(BaseModel):
    message: str
    sessionId: str | None = None 

# --- 1. /api/chat 엔드포인트 (async def -> def) ---
@router.post("/chat")
def chat_with_bot( # ⭐️ 'async' 삭제
    request: ChatRequest,
    user_sub: str = Depends(authenticate_user) 
):
    """
    [수정] Bedrock Agent와 스트리밍 채팅을 하고, DynamoDB에 대화를 저장합니다.
    (동기식으로 변경하여 블로킹 방지)
    """
    try:
        # ⭐️ bedrock_service의 동기식 제너레이터 호출
        generator = bedrock_service.stream_agent_response(
            user_sub=user_sub,
            session_id=request.sessionId, 
            message_text=request.message
        )
        
        return StreamingResponse(generator, media_type='text/event-stream')

    except Exception as e:
        print(f"Error in chat_with_bot endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
# --- 2. /api/sessions 엔드포인트 (async def -> def) ---
@router.get("/sessions")
def get_sessions( # ⭐️ 'async' 삭제
    user_sub: str = Depends(authenticate_user)
):
    sessions = dynamodb_service.get_sessions_by_user(user_id=user_sub)
    return sessions

# --- 3. /api/messages/{id} 엔드포인트 (async def -> def) ---
@router.get("/messages/{session_id}")
def get_messages( # ⭐️ 'async' 삭제
    session_id: str, 
    user_sub: str = Depends(authenticate_user)
):
    # (보안 검증)
    messages = dynamodb_service.get_messages_by_session(session_id=session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Messages not found")
    return messages