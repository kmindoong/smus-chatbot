from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache # ⭐️ 1. lru_cache 임포트

class Settings(BaseSettings):
    APP_ENV: str = "local"
    AWS_PROFILE: str | None = None
    AWS_REGION: str = "ap-northeast-2"
    
    COGNITO_USER_POOL_ID: str | None = None
    COGNITO_APP_CLIENT_ID: str | None = None
    
    BEDROCK_AGENT_ID: str | None = None
    BEDROCK_AGENT_ALIAS_ID: str | None = None
    
    DYNAMODB_SESSION_TABLE: str | None = None
    DYNAMODB_MESSAGES_TABLE: str | None = None

    # ⭐️ [추가] DataZone 도메인 ID
    DATAZONE_DOMAIN_ID: str = "dzd-3ojk7mnm02q5lk"

    # ⭐️ [추가] 챗봇 UI의 URL. 로컬을 기본값으로 설정
    CHATBOT_UI_URL: str = "./chatbot.html"

    @property
    def is_local(self) -> bool:
        """로컬 환경인지 확인"""
        return self.APP_ENV == "local"
    
    # ⭐️ 3. (수정) model_config를 사용하여 .env 파일과 환경 변수를 모두 읽도록 설정
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding='utf-8',
        extra='ignore' # .env 파일에 없는 환경 변수는 무시
    )

# 설정 객체를 앱 전역에서 캐시하여 사용
@lru_cache
def get_settings() -> Settings:
    try:
        settings = Settings()
        print(f"--- [INFO] Successfully loaded settings for APP_ENV: {settings.APP_ENV} ---")
        
        # ⭐️ 4. (중요) ECS 배포 시 필수 값들이 로드되었는지 수동 검증
        if not settings.is_local:
            required_vars = [
                'COGNITO_USER_POOL_ID', 'COGNITO_APP_CLIENT_ID',
                'DYNAMODB_SESSION_TABLE', 'DYNAMODB_MESSAGES_TABLE',
                'DATAZONE_DOMAIN_ID' # ⭐️ [추가]
            ]
            missing_vars = [var for var in required_vars if getattr(settings, var) is None]
            if missing_vars:
                print(f"--- [FATAL ERROR] Missing required env vars: {missing_vars} ---")
                raise ValueError(f"Missing required env vars: {missing_vars}")
                
        return settings
    except Exception as e:
        print(f"--- [FATAL ERROR] Failed to load settings. ---")
        print(f"Error details: {e}")
        raise

settings = get_settings()