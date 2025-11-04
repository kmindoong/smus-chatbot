import json
from typing import AsyncGenerator
from app.core.config import settings
from app.services.boto3_session import bedrock_agent_runtime # [수정] 중앙 Boto3 세션에서 임포트

async def invoke_agent_streaming(
    session_id: str, 
    prompt: str
) -> AsyncGenerator[bytes, None]:
    """
    Bedrock Agent를 호출하고 응답을 스트리밍합니다.
    """
    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=settings.BEDROCK_AGENT_ID,
            agentAliasId=settings.BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=prompt,
        )
        
        event_stream = response.get('completion')
        if not event_stream:
            yield json.dumps({"error": "No completion stream"}).encode('utf-8')
            return

        for event in event_stream:
            if 'chunk' in event:
                data_chunk = event['chunk'].get('bytes', b'')
                yield data_chunk
            # (기타 trace, error 이벤트 처리)

    except Exception as e:
        print(f"Error invoking Bedrock agent: {e}")
        yield json.dumps({"error": f"Internal Server Error: {str(e)}"}).encode('utf-8')