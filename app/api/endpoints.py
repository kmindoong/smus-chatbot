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

# ⭐️ [수정] ChatRequest 모델 변경
class ChatRequest(BaseModel):
    message: str
    sessionId: str | None = None 
    agentId: str        # ⭐️ [추가]
    agentAliasId: str   # ⭐️ [추가]

# ⭐️ [신규] /api/config 엔드포인트 (이전 요청 반영)
@router.get("/config")
def get_app_config():
    return {"chatbotUiUrl": settings.CHATBOT_UI_URL}

# ⭐️ [신규] Agent 목록을 반환하는 엔드포인트
@router.get("/agents")
def get_available_agents_for_user(
    claims: dict = Depends(authenticate_user) # ⭐️ 'claims' 객체 받기
):
    """
    [수정] 인증된 사용자의 'email'을 기반으로
    DataZone에서 공유된 Bedrock Agent 목록을 가져옵니다.
    """
    # ⭐️ [수정] 'cognito:username' 대신 'email'을 사용 (Notebook 기반)
    user_email = claims.get('email') 
    
    if not user_email:
        raise HTTPException(status_code=403, detail="Email not found in token claims.")
        
    try:
        # ⭐️ [수정] user_email 전달
        agent_mapping = bedrock_service.get_available_agents(user_email=user_email)
        return agent_mapping
    except Exception as e:
        print(f"Error in get_available_agents_for_user endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent list: {str(e)}"
        )

# ⭐️ [수정] /api/chat 엔드포인트
@router.post("/chat")
def chat_with_bot(
    request: ChatRequest,
    claims: dict = Depends(authenticate_user) # ⭐️ 'claims' 객체 받기
):
    try:
        user_sub = claims.get('sub') # ⭐️ DDB 저장용 고유 ID
        
        # ⭐️ bedrock_service로 agentId, agentAliasId 전달
        generator = bedrock_service.stream_agent_response(
            user_sub=user_sub,
            session_id=request.sessionId, 
            message_text=request.message,
            agent_id=request.agentId,
            agent_alias_id=request.agentAliasId
        )
        
        return StreamingResponse(generator, media_type='text/event-stream')

    except Exception as e:
        print(f"Error in chat_with_bot endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
# ⭐️ [수정] /api/sessions 엔드포인트
@router.get("/sessions")
def get_sessions(
    claims: dict = Depends(authenticate_user) # ⭐️ 'claims' 객체 받기
):
    user_sub = claims.get('sub')
    sessions = dynamodb_service.get_sessions_by_user(user_id=user_sub)
    return sessions

# ⭐️ [수정] /api/messages/{session_id} 엔드포인트
@router.get("/messages/{session_id}")
def get_messages(
    session_id: str, 
    claims: dict = Depends(authenticate_user) # ⭐️ 'claims' 객체 받기
):
    # (보안 검증 - 필요시 user_sub와 session_id 소유권 검증)
    messages = dynamodb_service.get_messages_by_session(session_id=session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Messages not found")
    return messages