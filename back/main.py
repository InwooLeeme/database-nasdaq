from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from functools import lru_cache
import os
import re
import sqlite3

from db import get_connection
from analysis import find_similar

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

app = FastAPI()

# 응답 gzip 압축
app.add_middleware(GZipMiddleware, minimum_size=500)

# 정적(읽기전용) 데이터이므로 CDN(엣지)에 장기 캐시.
# s-maxage: 엣지 캐시 1년(새 배포 시 Vercel이 자동 무효화).
# max-age: 브라우저 캐시 5분. stale-while-revalidate: 만료 후에도 갱신 동안 stale 제공.
CACHE_CONTROL = "public, max-age=300, s-maxage=31536000, stale-while-revalidate=86400"

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
    allow_methods=["GET"],
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


@lru_cache(maxsize=8)
def fetch_all(sql):
    """주어진 SELECT 문을 실행해 모든 행을 반환한다(워커 프로세스 내 캐시).

    stocks 테이블은 읽기전용이라 동일 쿼리를 반복 실행할 필요가 없다.
    결과가 비어 있으면 404.
    """
    try:
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not rows:
        raise HTTPException(status_code=404, detail="Chart data not found")
    return rows


@app.get("/nasdaq_chart")
async def get_nasdaq_chart(response: Response):
    response.headers["Cache-Control"] = CACHE_CONTROL
    rows = fetch_all("SELECT * FROM stocks ORDER BY date DESC")
    return [dict(zip(STOCKS_COLUMNS, row)) for row in rows]


@app.get("/similar_patterns")
async def get_similar_patterns(
    response: Response,
    start: str,
    end: str,
    metric: str = "cosine",
    top: int = 5,
):
    """기준 구간 [start, end]와 유사한 과거 구간을 찾아 반환한다."""
    if not DATE_RE.match(start) or not DATE_RE.match(end):
        raise HTTPException(status_code=400, detail="날짜 형식은 YYYY-MM-DD 여야 합니다")
    if start > end:
        raise HTTPException(status_code=400, detail="start 는 end 보다 앞서야 합니다")
    if metric not in ("cosine", "pearson"):
        raise HTTPException(status_code=400, detail="metric 은 cosine 또는 pearson 이어야 합니다")

    try:
        result = find_similar(start, end, metric=metric, top=max(1, min(top, 20)))
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="기준 구간이 너무 짧거나 데이터 범위를 벗어났습니다 (최소 2거래일 필요)",
        )

    response.headers["Cache-Control"] = CACHE_CONTROL
    return result
