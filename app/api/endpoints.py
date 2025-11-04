from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.security import authenticate_user
from app.services import bedrock_service, dynamodb_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    # sessionId는 이제 토큰에서 자동으로 가져옵니다.

@router.post("/chat")
async def chat_with_bot(
    request: ChatRequest,
    # [복원] Cognito 토큰을 검증하고 사용자의 고유 ID(sub)를 가져옵니다.
    user_sub: str = Depends(authenticate_user) 
):
    """
    [인증 필요] Bedrock Agent와 스트리밍으로 대화합니다.
    """
    try:
        # sessionId로 Cognito의 user_sub을 사용
        session_id = user_sub 
        
        streaming_generator = bedrock_service.invoke_agent_streaming(
            session_id=session_id,
            prompt=request.message
        )
        
        # (이전과 동일한 스트리밍 수집 및 DynamoDB 저장 로직)
        full_response_text = ""
        async for chunk in streaming_generator:
            full_response_text += chunk.decode('utf-8')

        if "error" not in full_response_text:
             dynamodb_service.update_session_history(
                 session_id, 
                 request.message, 
                 full_response_text
             )
        
        async def final_streamer(text):
            yield text.encode('utf-8')

        return StreamingResponse(
            final_streamer(full_response_text), 
            media_type="text/event-stream"
        )
        
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")