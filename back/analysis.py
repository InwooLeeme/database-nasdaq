"""유사 패턴 분석 (API용).

사용자가 고른 기준 구간과 가장 비슷하게 움직였던 과거 구간을 찾는다.
"""
from functools import lru_cache

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from db import get_connection

NEXT_DATE = 5  # 유사 패턴 이후 함께 보여줄 일수


@lru_cache(maxsize=1)
def load_closes():
    """stocks 테이블에서 (날짜 리스트, 종가 ndarray)를 날짜 오름차순으로 반환.

    종가 데이터는 요청 중에 바뀌지 않으므로(읽기전용 DB) 워커 프로세스 내에서
    한 번만 로드해 재사용한다.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT date, stock_closing_price FROM stocks ORDER BY date ASC"
        ).fetchall()
    dates = [r[0] for r in rows]
    closes = np.array([r[1] for r in rows], dtype=float)
    return dates, closes


def _normalize(arr):
    """[0, 1] 최소-최대 정규화 (1차원)."""
    lo = arr.min()
    rng = arr.max() - lo
    if rng == 0:
        return np.zeros_like(arr)
    return (arr - lo) / rng


def _safe_divide(num, den):
    out = np.zeros_like(num, dtype=float)
    nz = den != 0
    out[nz] = num[nz] / den[nz]
    return out


def _similarities(base, windows, metric):
    """기준 패턴(base)과 모든 윈도우(windows) 간 유사도 벡터를 계산."""
    if metric == "pearson":
        # 피어슨 상관: 평균 제거 후 정규화 내적 (선형변환에 불변이라 정규화 불필요)
        b = base - base.mean()
        w = windows - windows.mean(axis=1, keepdims=True)
    else:
        # 코사인: 각 구간을 [0,1] 정규화한 뒤 코사인 유사도
        b = _normalize(base)
        lo = windows.min(axis=1, keepdims=True)
        rng = windows.max(axis=1, keepdims=True) - lo
        w = (windows - lo) / np.where(rng == 0, 1, rng)

    num = w @ b
    den = np.sqrt((w ** 2).sum(axis=1)) * np.sqrt((b ** 2).sum())
    return _safe_divide(num, den)


def _overlaps(a0, a1, b0, b1):
    return not (a1 < b0 or a0 > b1)


def find_similar(start, end, metric="cosine", top=5):
    """기준 구간 [start, end] 와 유사한 과거 구간 top 개를 찾는다.

    반환: {base, window, metric, matches[]} (dict) 또는 None(구간 부적합).
    각 match 의 series 는 윈도우+이후 NEXT_DATE 일을 함께 정규화한 값으로,
    프론트의 비교 오버레이 차트가 그대로 그릴 수 있다.
    """
    dates, closes = load_closes()
    n = len(dates)

    base_idx = [i for i, d in enumerate(dates) if start <= d <= end]
    if len(base_idx) < 2:
        return None  # 데이터 범위 밖이거나 구간이 너무 짧음

    b0, b1 = base_idx[0], base_idx[-1]
    window = b1 - b0 + 1

    last = n - window - NEXT_DATE  # 미래 NEXT_DATE 일을 남길 수 있는 마지막 시작 인덱스
    if last < 0:
        return None  # 윈도우가 전체 데이터보다 큼

    base = closes[b0:b1 + 1]
    windows = sliding_window_view(closes, window)[: last + 1]
    sims = _similarities(base, windows, metric)

    # 유사도 내림차순으로, 기준 구간 및 이미 고른 구간과 겹치지 않게 선택
    chosen = []
    for i in np.argsort(sims)[::-1]:
        s = int(i)
        e = s + window - 1
        if _overlaps(s, e, b0, b1):
            continue
        if any(_overlaps(s, e, c[0], c[1]) for c in chosen):
            continue
        chosen.append((s, e, float(sims[i])))
        if len(chosen) >= top:
            break

    matches = []
    for s, e, sim in chosen:
        span = closes[s:e + 1 + NEXT_DATE]  # 윈도우 + 이후 NEXT_DATE 일
        matches.append({
            "start": dates[s],
            "end": dates[e],
            "futureEnd": dates[min(e + NEXT_DATE, n - 1)],
            "similarity": round(sim, 4),
            "series": [round(v, 4) for v in _normalize(span).tolist()],
        })

    return {
        "base": {
            "start": dates[b0],
            "end": dates[b1],
            "series": [round(v, 4) for v in _normalize(base).tolist()],
        },
        "window": window,
        "nextDays": NEXT_DATE,
        "metric": metric,
        "matches": matches,
    }
