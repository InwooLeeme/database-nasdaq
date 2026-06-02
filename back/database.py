"""CSV(나스닥 과거 데이터)를 읽어 chart.db 의 stocks 테이블로 적재하는 일회성 스크립트."""
import os

import pandas as pd

from db import get_connection

BACK_DIR = os.path.dirname(os.path.abspath(__file__))
TABLE_NAME = "stocks"
COLUMN_RENAME = {
    "날짜": "date",
    "종가": "stock_closing_price",
    "시가": "stock_market_price",
    "고가": "stock_high_price",
    "저가": "stock_low_price",
    "거래량": "volume",
    "변동 %": "change",
}


def load_csv_data(directory):
    """디렉토리 내 '나스닥'으로 시작하는 CSV들을 읽어 하나의 DataFrame으로 합친다."""
    frames = [
        pd.read_csv(os.path.join(directory, filename))
        for filename in os.listdir(directory)
        if filename.startswith("나스닥")
    ]
    if not frames:
        raise ValueError("CSV 파일에 데이터가 없습니다.")
    return pd.concat(frames, ignore_index=True).rename(columns=COLUMN_RENAME)


def build_database():
    csv_data = load_csv_data(BACK_DIR)
    with get_connection() as conn:
        csv_data.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.commit()
    print(f"'{TABLE_NAME}' 테이블에 {len(csv_data)}개 행을 적재했습니다.")


if __name__ == "__main__":
    build_database()
