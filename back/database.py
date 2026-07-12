"""CSV(나스닥 과거 데이터)를 정제해 chart.db 의 stocks 테이블로 적재하는 일회성 스크립트."""
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
PRICE_COLUMNS = [
    "stock_closing_price",
    "stock_market_price",
    "stock_high_price",
    "stock_low_price",
]
VOLUME_SUFFIX = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}


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


def _parse_price(value):
    """"4,069.31" 같은 천단위 구분자 문자열(또는 이미 숫자인 값)을 float 로 변환."""
    if isinstance(value, str):
        value = value.replace(",", "")
    return float(value)


def _parse_volume(value):
    """"283.38M" / "1.12B" 형태의 거래량 문자열을 float 로 변환. 값이 없으면 None."""
    if pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    suffix = text[-1].upper()
    if suffix in VOLUME_SUFFIX:
        return float(text[:-1]) * VOLUME_SUFFIX[suffix]
    return float(text)


def _parse_change(value):
    """"1.08%" 같은 문자열(또는 이미 숫자인 값)을 float(1.08) 로 변환."""
    if isinstance(value, str):
        value = value.replace("%", "")
    return float(value)


def clean_data(df):
    """"1989- 12- 29" 같은 공백 낀 날짜, "4,069.31" 같은 천단위 구분자,
    "283.38M" 거래량, "1.08%" 변동률을 각각 순수한 date/float 값으로 정규화한다.
    파일마다 pandas 가 원본 타입을 다르게 추론해(숫자가 작아 콤마가 없는 구간은
    float64로, 그 외는 문자열로) 컬럼이 혼합 타입이 되므로 apply 로 값 단위 처리한다.
    """
    df = df.copy()
    df["date"] = df["date"].str.replace(" ", "", regex=False)
    for col in PRICE_COLUMNS:
        df[col] = df[col].apply(_parse_price)
    df["volume"] = df["volume"].apply(_parse_volume)
    df["change"] = df["change"].apply(_parse_change)
    return df


def build_database():
    csv_data = clean_data(load_csv_data(BACK_DIR))
    with get_connection() as conn:
        csv_data.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.execute(f"CREATE UNIQUE INDEX idx_{TABLE_NAME}_date ON {TABLE_NAME}(date)")
        conn.commit()
    print(f"'{TABLE_NAME}' 테이블에 {len(csv_data)}개 행을 적재했습니다.")


if __name__ == "__main__":
    build_database()
