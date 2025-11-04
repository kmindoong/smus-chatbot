# app/services/bedrock_service.py

import json
import traceback 
from datetime import datetime, timezone
from app.core.config import settings
from app.services.boto3_session import bedrock_agent_client
from app.services.dynamodb_service import save_message, create_session

def stream_agent_response( 
    user_sub: str, 
    session_id: str | None, 
    message_text: str
):
    """
    [수정] Bedrock Agent의 'invoke_agent' (동기)를 호출하고,
    sessionId가 정규식(regex) 제약 조건을 만족하도록 수정합니다.
    """
    
    is_new_chat = False
    session_id_to_use = session_id 
    
    if not session_id:
        is_new_chat = True
        # ⭐️ (수정) .isoformat()이 '+00:00'을 생성하므로, 'Z'로 대체합니다.
        session_id_to_use = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    try:
        # --- (이하 DB 저장 및 Bedrock 호출 로직은 기존과 동일) ---
        save_message(
            session_id=session_id_to_use, 
            role='user', 
            content=message_text
        )
        if is_new_chat:
            create_session(
                user_id=user_sub, 
                session_id=session_id_to_use, 
                title=message_text
            )

        if is_new_chat:
            yield json.dumps({"sessionId": session_id_to_use}) + "\n"
            
        response = bedrock_agent_client.invoke_agent( 
            agentId=settings.BEDROCK_AGENT_ID,
            agentAliasId=settings.BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id_to_use, 
            inputText=message_text
        )
        
        full_bot_response = ""
        
        stream = response.get('completion') 
        if stream:
            for event in stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        decoded_chunk = chunk['bytes'].decode('utf-8')
                        full_bot_response += decoded_chunk
                        yield decoded_chunk 
        
        if full_bot_response:
            save_message(
                session_id=session_id_to_use,
                role='bot',
                content=full_bot_response
            )
            
    except Exception as e:
        print("--- !!! ERROR IN bedrock_service.stream_agent_response !!! ---")
        traceback.print_exc()
        print("--- !!! END OF bedrock_service TRACEBACK !!! ---")
        raise e