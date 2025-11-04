from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.api import endpoints

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="SMUS Chatbot API")

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