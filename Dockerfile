# 1. 기본 이미지: Python 3.11 슬림 버전 사용
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /code

# 3. requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. [수정] 'app' 폴더 전체를 이미지의 /code/app 으로 복사
COPY ./app /code/app

# 5. Gunicorn이 8000번 포트로 앱을 실행하도록 설정
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "-b", "0.0.0.0:8000"]