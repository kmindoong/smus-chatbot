import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# 1. 어떤 환경인지 확인 (기본값: 'local')
#    Fargate에서는 이 변수를 'dev' 또는 'prod'로 주입합니다.
APP_ENV = os.getenv("APP_ENV", "local")

# 2. 환경에 맞는 .env 파일 경로 설정
env_file = f".env.{APP_ENV}" # 예: .env.local

class Settings(BaseSettings):
    """
    환경 변수 또는 .env.{APP_ENV} 파일에서 설정을 읽어옵니다.
    """
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # 1. 공통 설정
    APP_ENV: str = APP_ENV
    AWS_REGION: str = "ap-northeast-2"
    
    # 2. 로컬 전용 설정 ('.env.local' 파일에만 있어야 함)
    AWS_PROFILE: str | None = None 

    # 3. 환경별 AWS 리소스 (dev/prod 값이 달라야 함)
    COGNITO_USER_POOL_ID: str
    COGNITO_APP_CLIENT_ID: str
    BEDROCK_AGENT_ID: str
    BEDROCK_AGENT_ALIAS_ID: str
    DYNAMODB_SESSION_TABLE: str

    @property
    def is_local(self) -> bool:
        """로컬 환경인지 확인"""
        return self.APP_ENV == "local"

# 설정 객체를 앱 전역에서 캐시하여 사용
@lru_cache
def get_settings() -> Settings:
    try:
        settings = Settings()
        print(f"--- [INFO] Successfully loaded settings for APP_ENV: {settings.APP_ENV} from {env_file} ---")
        return settings
    except Exception as e:
        print(f"--- [FATAL ERROR] Failed to load settings from {env_file}. Ensure file exists and variables are set. ---")
        print(f"Error details: {e}")
        raise

settings = get_settings()