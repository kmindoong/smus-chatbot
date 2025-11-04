from datetime import datetime, timezone
# ⭐️ boto3_session.py에서 초기화된 테이블 리소스를 가져옵니다.
from app.services.boto3_session import sessions_table, messages_table

def create_session(user_id: str, session_id: str, title: str):
    """(신규) sessions_table에 새 대화방을 생성합니다."""
    try:
        sessions_table.put_item(
            Item={
                'user_id': user_id,
                'session_id': session_id,
                'session_title': title[:100] # 제목은 100자로 제한
            }
        )
    except Exception as e:
        print(f"Error creating session: {e}")

def save_message(session_id: str, role: str, content: str):
    """(신규) messages_table에 메시지를 저장합니다."""
    try:
        # 메시지 타임스탬프는 여기서 생성
        timestamp = datetime.now(timezone.utc).isoformat()
        messages_table.put_item(
            Item={
                'session_id': session_id,
                'message_timestamp': timestamp,
                'role': role,
                'content': content
            }
        )
    except Exception as e:
        print(f"Error saving message: {e}")

def get_sessions_by_user(user_id: str):
    """(신규) 특정 사용자의 모든 대화 목록을 조회합니다."""
    try:
        response = sessions_table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False # 최신순 정렬
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return []

def get_messages_by_session(session_id: str):
    """(신규) 특정 세션의 모든 메시지를 조회합니다."""
    try:
        response = messages_table.query(
            KeyConditionExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': session_id}
            # SK(message_timestamp)로 자동 정렬됨
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []