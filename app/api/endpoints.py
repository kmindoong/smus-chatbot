import traceback  # <--- 1. 파일 맨 위에 이 라인을 추가하세요.
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
    # user_sub: str = Depends(authenticate_user) 
):
    """
    [인증 필요] Bedrock Agent와 스트리밍으로 대화합니다.
    """
    try:
        # sessionId로 Cognito의 user_sub을 사용
        user_sub = "mjkwon"
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
        
    except Exception as e:  # <--- 3. 이 except 블록 전체를 추가하세요.
        print("\n--- !!! 💥 ERROR IN /api/chat ENDPOINT !!! ---")

        # 콘솔에 상세한 오류 내역(Traceback)을 강제로 출력
        traceback.print_exc() 

        print(f"--- ERROR DETAILS: {e} ---")
        print("--- !!! END OF TRACEBACK !!! ---\n")

        # 클라이언트에게도 500 오류를 보냄
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )