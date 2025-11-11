import boto3
from app.core.config import settings
from requests_aws4auth import AWS4Auth # ⭐️ [신규]

# 1. Boto3 세션 초기화 (기존 로직)
session_kwargs = {"region_name": settings.AWS_REGION}
if settings.APP_ENV == "local" and settings.AWS_PROFILE:
    session_kwargs["profile_name"] = settings.AWS_PROFILE

session = boto3.Session(**session_kwargs)

# 2. 클라이언트 초기화 (기존 로직 - 예시)
cognito_client = session.client('cognito-idp')
bedrock_agent_client = session.client('bedrock-agent-runtime')

# ⭐️ [신규] Bedrock Agent 관리를 위한 클라이언트 (ListAgents)
bedrock_agent_mgmt_client = session.client('bedrock-agent')

# ⭐️ [신규] DataZone 클라이언트 (SearchUserProfiles)
datazone_client = session.client('datazone')

# 3. ⭐️ DynamoDB 리소스 및 테이블 2개 초기화 (수정/추가)
dynamodb_resource = session.resource('dynamodb')

sessions_table = dynamodb_resource.Table(settings.DYNAMODB_SESSION_TABLE)
messages_table = dynamodb_resource.Table(settings.DYNAMODB_MESSAGES_TABLE)

# 4. ⭐️ [추가] DataZone의 비-SDK API 호출을 위한 서명(SigV4) 헬퍼
def get_datazone_auth_signer():
    """
    Boto3 세션의 현재 자격 증명(Fargate Task Role)을 사용하여
    DataZone API 요청에 서명할 AWS4Auth 객체를 반환합니다.
    """
    credentials = session.get_credentials().get_frozen_credentials()
    return AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        settings.AWS_REGION,
        "datazone",
        session_token=credentials.token
    )