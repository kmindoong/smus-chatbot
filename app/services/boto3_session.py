import boto3
from app.core.config import settings

if settings.is_local and settings.AWS_PROFILE:
    # --- 로컬 환경 (Local) ---
    # .env.local의 AWS_PROFILE (예: 'sso-admin')을 사용
    print(f"--- [BOTO3] Running in LOCAL mode. Using AWS Profile: {settings.AWS_PROFILE} ---")
    session = boto3.Session(profile_name=settings.AWS_PROFILE, region_name=settings.AWS_REGION)
else:
    # --- 운영/개발 환경 (Prod/Dev on Fargate) ---
    # Fargate의 IAM Task Role을 사용 (프로필 불필요)
    print(f"--- [BOTO3] Running in PROD/DEV mode. Using IAM Task Role. ---")
    session = boto3.Session(region_name=settings.AWS_REGION)

# 다른 서비스에서 임포트할 클라이언트들
dynamodb = session.resource('dynamodb')
bedrock_agent_runtime = session.client('bedrock-agent-runtime')
cognito_client = session.client('cognito-idp') # (필요시 사용)