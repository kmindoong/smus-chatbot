import requests
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings  # [수정] config 대신 settings 임포트

# Cognito에서 토큰을 받아올 때 사용 (여기서는 /chat 호출 시 Bearer 토큰을 받음)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Cognito User Pool의 JWKS (JSON Web Key Set) URL
COGNITO_JWKS_URL = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"

# JWKS를 캐시하여 매번 요청하지 않도록 함
try:
    response = requests.get(COGNITO_JWKS_URL)
    response.raise_for_status() # 오류가 있으면 예외 발생
    JWKS = response.json()
    print("--- [AUTH] Successfully fetched Cognito JWKS. ---")
except requests.exceptions.RequestException as e:
    print(f"--- [AUTH FATAL] Failed to fetch JWKS from Cognito: {e} ---")
    JWKS = {"keys": []} # 앱이 죽지 않도록 비워둠 (어차피 인증 실패)

def authenticate_user(token: str = Security(oauth2_scheme)):
    """
    Cognito JWT 토큰을 검증하고 사용자 'sub' (고유 ID)를 반환합니다.
    """
    try:
        # 1. 토큰 헤더 파싱
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        
        # 2. 헤더의 kid와 일치하는 키를 JWKS에서 찾기
        key = next((k for k in JWKS['keys'] if k['kid'] == kid), None)
        if not key:
            raise HTTPException(status_code=403, detail="Public key not found in JWKS")

        # 3. 공개키 생성
        public_key = jwk.construct(key)
        
        # 4. 토큰 메시지 분리 (서명 검증 전)
        message, encoded_signature = str(token).rsplit('.', 1)
        
        # 5. 서명 검증
        decoded_signature = base64url_decode(encoded_signature)
        if not public_key.verify(message.encode("utf-8"), decoded_signature):
            raise HTTPException(status_code=403, detail="Signature verification failed")
            
        # 6. 토큰 만료 시간(exp) 검증
        claims = jwt.get_unverified_claims(token)
        if time.time() > claims['exp']:
            raise HTTPException(status_code=403, detail="Token has expired")
            
        # 7. Audience (aud) 검증
        # [수정] settings 객체에서 값 비교
        if claims['aud'] != settings.COGNITO_APP_CLIENT_ID:
            raise HTTPException(status_code=403, detail="Token was not issued for this app client")
        
        # 8. 검증 성공 시 사용자 정보 반환 (예: username) -> username 대신 고유 ID인 'sub'를 반환
        return claims['sub']

    except jwt.JWTError as e:
        raise HTTPException(status_code=403, detail=f"Token validation error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {e}")