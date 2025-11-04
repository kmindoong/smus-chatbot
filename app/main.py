import traceback  # 1. traceback 임포트
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.api import endpoints

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="SMUS Chatbot API")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    모든 예외를 가로채서 상세한 트레이스백을 콘솔에 출력하는 핸들러
    """
    print("--- !!! GLOBAL EXCEPTION HANDLER CAUGHT AN ERROR !!! ---")
    print(f"--- Request: {request.method} {request.url} ---")
    
    # 가장 중요: 콘솔에 전체 오류 스택을 강제로 출력
    traceback.print_exc() 
    
    print("--- !!! END OF TRACEBACK !!! ---")
    
    # 클라이언트에게는 표준 500 오류 응답을 보냄
    return JSONResponse(
        status_code=500,
        content={
            "message": "An internal server error occurred.",
            "error_type": type(exc).__name__,
            "error_details": str(exc)
        },
    )

# CORS 설정 (내부망이라도 ALB 등을 거칠 수 있으므로 설정 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실제 운영 환경에서는 ALB DNS 등으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 포함 (prefix='/api' 사용)
app.include_router(endpoints.router, prefix="/api")

# 정적 파일(UI) 마운트
# app/main.py 기준, 같은 폴더 내의 'frontend' 디렉토리를 / 에 마운트
frontend_dir = Path(__file__).parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")