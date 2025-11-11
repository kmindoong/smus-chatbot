import requests
import traceback
from jose import jwk, jwt
from jose.utils import base64url_decode
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ... (JWKS 로드 로직은 동일) ...
try:
    response = requests.get(f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json")
    response.raise_for_status() 
    JWKS = response.json()
    print("--- [AUTH] Successfully fetched Cognito JWKS. ---")
except requests.exceptions.RequestException as e:
    print(f"--- [AUTH FATAL] Failed to fetch JWKS from Cognito: {e} ---")
    JWKS = {"keys": []} 

def authenticate_user(token: str = Security(oauth2_scheme)):
    """
    ⭐️ [수정] Cognito JWT 토큰을 검증하고 'sub' 대신 'claims' 객체 전체를 반환합니다.
    """
    try:
        # 1. 토큰 헤더 파싱
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        
        # 2. 헤더의 kid와 일치하는 키를 JWKS에서 찾기
        key = next((k for k in JWKS['keys'] if k['kid'] == kid), None)
        if not key:
            raise HTTPException(status_code=403, detail="Public key not found in JWKS")
        
        # ⭐️ [디버깅 추가] 서버의 현재 UTC 시간을 타임스탬프로 출력
        # import time
        # print(f"--- [AUTH DEBUG] Server Time: {int(time.time())} ---")

        # ⭐️ 3. [수정] 토큰 검증 (서명, 만료, 대상, 발급자 모두 한 번에)
        # 4~7단계 수동 검증 로직을 아래 decode 함수가 모두 대체합니다.
        claims = jwt.decode(
            token,
            key,  # JWKS에서 찾은 key 딕셔너리 객체
            algorithms=['RS256'],
            audience=settings.COGNITO_APP_CLIENT_ID, # 7. Audience (aud) 검증
            issuer=f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}" # ⭐️ 발급자(iss) 검증 (필수)
        )
        
        # 4. ⭐️ [수정] 'sub' 대신 claims 딕셔너리 전체를 반환합니다.
        return claims

    except jwt.ExpiredSignatureError:
        # ⭐️ 라이브러리가 직접 만료 오류를 잡아줍니다.
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.JWTClaimsError as e:
        # ⭐️ Audience(aud) 또는 Issuer(iss)가 일치하지 않을 때
        raise HTTPException(status_code=403, detail=f"Token claims error: {e}")
    except jwt.JWTError as e:
        # ⭐️ 그 외 (서명 오류 등)
        raise HTTPException(status_code=403, detail=f"Token validation error: {e}")
    except Exception as e:
        print("--- !!! ERROR IN authenticate_user (security.py) !!! ---")
        traceback.print_exc()
        print("--- !!! END OF security.py TRACEBACK ---")
        
        raise HTTPException(status_code=500, detail=f"Authentication error: {e}")