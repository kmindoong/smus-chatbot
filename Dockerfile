# 1. 베이스 이미지 (Python 3.12 기준)
FROM python:3.12-slim

# 2. 작업 디렉토리 설정
WORKDIR /code

# 3. Python 의존성 설치
# requirements.txt 먼저 복사 및 설치 (이것이 Docker 캐시 활용의 핵심)
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 4. ⭐️ [중요] 'app' 폴더 전체를 이미지 안으로 복사
#    (app/main.py, app/frontend/*, app/api/* 등이 모두 복사됨)
COPY ./app /code/app

# 5. Uvicorn 서버 실행
# --host 0.0.0.0 은 컨테이너 외부에서 접근하기 위해 필수
# --port 8000 은 로드 밸런서와 연결할 포트
# --reload 플래그는 운영 환경이므로 제거
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
