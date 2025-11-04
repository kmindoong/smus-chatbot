from pydantic_settings import BaseSettings
from functools import lru_cache # ⭐️ 1. lru_cache 임포트

class Settings(BaseSettings):
    APP_ENV: str = "local"
    AWS_PROFILE: str | None = None
    AWS_REGION: str = "ap-northeast-2"
    
    COGNITO_USER_POOL_ID: str
    COGNITO_APP_CLIENT_ID: str
    
    BEDROCK_AGENT_ID: str
    BEDROCK_AGENT_ALIAS_ID: str
    
    DYNAMODB_SESSION_TABLE: str
    DYNAMODB_MESSAGES_TABLE: str

    @property
    def is_local(self) -> bool:
        """로컬 환경인지 확인"""
        return self.APP_ENV == "local"
    
    class Config:
        # ⭐️ 2. BaseSettings가 .env 파일을 읽도록 Config 클래스 안에 경로를 지정
        env_file = ".env.local"
        env_file_encoding = 'utf-8'

# 설정 객체를 앱 전역에서 캐시하여 사용
@lru_cache
def get_settings() -> Settings:
    # ⭐️ 3. get_settings 함수를 단순화 (Settings()가 알아서 env_file을 읽음)
    try:
        settings = Settings()
        print(f"--- [INFO] Successfully loaded settings for APP_ENV: {settings.APP_ENV} ---")
        return settings
    except Exception as e:
        print(f"--- [FATAL ERROR] Failed to load settings. Ensure .env.local file exists. ---")
        print(f"Error details: {e}")
        raise

settings = get_settings()