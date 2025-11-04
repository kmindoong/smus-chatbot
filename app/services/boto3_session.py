import boto3
from app.core.config import settings

# 1. Boto3 세션 초기화 (기존 로직)
session_kwargs = {"region_name": settings.AWS_REGION}
if settings.APP_ENV == "local" and settings.AWS_PROFILE:
    session_kwargs["profile_name"] = settings.AWS_PROFILE

session = boto3.Session(**session_kwargs)

# 2. 클라이언트 초기화 (기존 로직 - 예시)
cognito_client = session.client('cognito-idp')
bedrock_agent_client = session.client('bedrock-agent-runtime')
# ... (다른 클라이언트) ...

# 3. ⭐️ DynamoDB 리소스 및 테이블 2개 초기화 (수정/추가)
dynamodb_resource = session.resource('dynamodb')

sessions_table = dynamodb_resource.Table(settings.DYNAMODB_SESSION_TABLE)
messages_table = dynamodb_resource.Table(settings.DYNAMODB_MESSAGES_TABLE)