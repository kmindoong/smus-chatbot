from app.core.config import settings
from app.services.boto3_session import dynamodb # [수정] 중앙 Boto3 세션에서 임포트

try:
    DYNAMODB_TABLE = dynamodb.Table(settings.DYNAMODB_SESSION_TABLE)
    print(f"--- [DB] Successfully connected to DynamoDB table: {settings.DYNAMODB_SESSION_TABLE} ---")
except Exception as e:
    print(f"--- [DB FATAL] Failed to connect to DynamoDB: {e} ---")
    DYNAMODB_TABLE = None

def get_session_history(session_id: str) -> list:
    """
    DynamoDB에서 세션 기록을 조회합니다.
    (session_id는 Cognito 'sub' 사용 권장)
    """
    if not DYNAMODB_TABLE: return []
    try:
        response = DYNAMODB_TABLE.get_item(Key={'sessionId': session_id})
        return response.get('Item', {}).get('history', [])
    except Exception as e:
        print(f"Error getting session from DynamoDB: {e}")
        return []

def update_session_history(session_id: str, user_prompt: str, bot_response: str):
    """
    DynamoDB에 세션 기록을 저장합니다.
    """
    if not DYNAMODB_TABLE: return
    try:
        DYNAMODB_TABLE.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="SET history = list_append(if_not_exists(history, :empty_list), :new_message)",
            ExpressionAttributeValues={
                ':new_message': [{'user': user_prompt, 'bot': bot_response}],
                ':empty_list': []
            }
        )
    except Exception as e:
        print(f"Error updating session to DynamoDB: {e}")