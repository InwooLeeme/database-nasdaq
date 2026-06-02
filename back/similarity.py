"""stocks 종가 데이터로 패턴 유사도를 계산/시각화하는 공용 모듈.

cosine.py / pearson.py 가 공유한다. 유사도 지표 함수만 바꿔 끼우면 된다.
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from db import get_connection

BACK_DIR = os.path.dirname(os.path.abspath(__file__))
TABLE_NAME = "stocks"

# stocks 테이블의 실제 컬럼 순서 (database.py 적재 결과 기준)
STOCK_COLUMNS = [
    "datetime",
    "stock_closing_price",
    "stock_market_price",
    "stock_high_price",
    "stock_low_price",
    "volume",
    "change",
]

NEXT_DATE = 5  # 예측 기간(일): 유사 패턴 이후 며칠까지 함께 그릴지


def cosine_similarity(x, y):
    return np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))


def pearson_similarity(x, y):
    return np.corrcoef(x, y)[0, 1]


def normalize(series):
    """[0, 1] 범위로 최소-최대 정규화."""
    return (series - series.min()) / (series.max() - series.min())


def load_close_prices():
    """stocks 테이블을 읽어 datetime 인덱스 + 숫자형 종가를 가진 DataFrame을 반환."""
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM {TABLE_NAME} ORDER BY date ASC"
        ).fetchall()

    df = pd.DataFrame(rows, columns=STOCK_COLUMNS)
    df["datetime"] = df["datetime"].str.replace(" ", "")
    df.set_index("datetime", inplace=True)
    df["stock_closing_price"] = pd.to_numeric(
        df["stock_closing_price"].str.replace(",", ""), errors="coerce"
    )
    return df


def compute_similarities(df, base, metric):
    """base 패턴과 전체 구간의 슬라이딩 윈도우 간 유사도 시리즈를 계산."""
    window_size = len(base)
    mv_cnt = len(df) - window_size - NEXT_DATE - 1
    sims = []
    for i in range(mv_cnt):
        target = normalize(df["stock_closing_price"].iloc[i : i + window_size])
        sims.append(metric(base, target))
    return pd.Series(sims)


def plot_pattern(base, df, idx, save_path):
    """base 패턴과, 유사 구간(idx)의 향후(NEXT_DATE일) 추이를 겹쳐 그려 저장."""
    window_size = len(base)
    target = normalize(
        df["stock_closing_price"].iloc[idx : idx + window_size + NEXT_DATE]
    )
    plt.plot(base.values, label="base", color="grey")
    plt.plot(target.values, label="target", color="orangered")
    plt.xticks(
        np.arange(len(target)),
        pd.to_datetime(target.index.values).strftime("%Y-%m-%d"),
        rotation=45,
    )
    plt.axvline(x=len(base) - 1, c="grey", linestyle="--")
    plt.axvspan(
        len(base.values) - 1, len(target.values) - 1, facecolor="ivory", alpha=0.7
    )
    plt.legend()
    plt.savefig(save_path)
    plt.close()
