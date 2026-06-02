"""chart.db (SQLite) 연결을 위한 공용 헬퍼.

실행 위치(작업 디렉토리)와 무관하게 동작하도록 이 파일 기준 절대경로를 사용한다.
"""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chart.db")


@contextmanager
def get_connection():
    """사용 후 자동으로 닫히는 SQLite 연결을 제공하는 컨텍스트 매니저."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
