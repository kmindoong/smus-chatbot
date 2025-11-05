# 1. 베이스 이미지 (Python 3.12 기준)
FROM python:3.12-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. Python 의존성 설치
# (requirements.txt가 있다면)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# (Poetry를 사용한다면)
# COPY pyproject.toml poetry.lock* ./
# RUN pip install poetry && poetry export -f requirements.txt | pip install -r /dev/stdin

# (임시: 의존성 파일이 없다면 FastAPI/Uvicorn/Boto3 등 설치)
# RUN pip install --no-cache-dir "fastapi[all]" "boto3" "uvicorn[standard]" "python-jose[cryptography]" "pydantic-settings" "requests"

# 4. 앱 소스코드 복사
# (main.py, config.py 등이 app/ 폴더 안에 있으므로 app 폴더를 통째로 복사)
COPY ./app /app/app

# 5. Uvicorn 서버 실행
# --host 0.0.0.0 은 컨테이너 외부에서 접근하기 위해 필수
# --port 8000 은 로드 밸런서와 연결할 포트
# --reload 플래그는 운영 환경이므로 제거
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
