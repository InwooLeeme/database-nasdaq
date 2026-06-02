from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3

from db import get_connection

app = FastAPI()

# CORS 설정
# 환경변수 FRONTEND_ORIGINS(쉼표 구분)가 있으면 해당 도메인만 허용,
# 없으면 모든 출처 허용(공개 읽기전용 API). 후자는 인증정보를 쓰지 않으므로
# allow_credentials 를 끈다(스펙상 "*" 와 credentials 동시 사용 불가).
allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]
allow_all = not allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else allowed_origins,
    allow_credentials=not allow_all,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# stocks 테이블의 실제 물리적 컬럼 순서 (database.py 적재 결과 기준).
# 시가(market)/고가(high)/저가(low) 순서가 정확히 매핑되도록 한다.
STOCKS_COLUMNS = [
    "date",
    "stock_closing_price",
    "stock_market_price",
    "stock_high_price",
    "stock_low_price",
    "volume",
    "change",
]


def fetch_all(sql):
    """주어진 SELECT 문을 실행해 모든 행을 반환한다. 결과가 비어 있으면 404."""
    try:
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not rows:
        raise HTTPException(status_code=404, detail="Chart data not found")
    return rows


@app.get("/nasdaq_chart")
async def get_nasdaq_chart():
    rows = fetch_all("SELECT * FROM stocks ORDER BY date DESC")
    return [dict(zip(STOCKS_COLUMNS, row)) for row in rows]


@app.get("/cosine_similarity")
async def get_cosine_similarity():
    rows = fetch_all("SELECT idx, similarity FROM cosine ORDER BY similarity DESC")
    return [{"idx": idx, "similarity": similarity} for idx, similarity in rows]
