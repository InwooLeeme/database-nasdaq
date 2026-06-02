import os
import sys

# back/ 디렉토리를 import 경로에 추가하여 기존 FastAPI 앱을 그대로 재사용한다.
BACK_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "back"
)
sys.path.insert(0, BACK_DIR)

from fastapi import FastAPI
from main import app as backend_app  # back/main.py 의 FastAPI 인스턴스

# Vercel 은 이 파일을 /api 경로의 서버리스 함수로 서빙한다.
# vercel.json 의 rewrite 가 /api/* 요청을 이 함수로 보내므로,
# 백엔드 앱을 /api 에 마운트하여 내부 라우트(/nasdaq_chart 등)가
# /api/nasdaq_chart 형태로 노출되도록 한다. (마운트가 경로 접두사를 제거)
app = FastAPI()
app.mount("/api", backend_app)
