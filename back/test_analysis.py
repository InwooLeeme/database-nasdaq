import datetime as dt

import numpy as np
import pytest

import analysis
from analysis import _normalize, _overlaps, _safe_divide, _similarities, find_similar


def _dates(n, start="2020-01-01"):
    d0 = dt.date.fromisoformat(start)
    return [str(d0 + dt.timedelta(days=i)) for i in range(n)]


class TestNormalize:
    def test_min_max_range(self):
        result = _normalize(np.array([1.0, 2.0, 3.0]))
        assert np.allclose(result, [0.0, 0.5, 1.0])

    def test_constant_array_returns_zeros(self):
        result = _normalize(np.array([5.0, 5.0, 5.0]))
        assert np.allclose(result, [0.0, 0.0, 0.0])


class TestSafeDivide:
    def test_normal_division(self):
        num = np.array([4.0, 9.0])
        den = np.array([2.0, 3.0])
        assert np.allclose(_safe_divide(num, den), [2.0, 3.0])

    def test_zero_denominator_returns_zero(self):
        num = np.array([4.0, 0.0])
        den = np.array([0.0, 0.0])
        assert np.allclose(_safe_divide(num, den), [0.0, 0.0])


class TestOverlaps:
    def test_disjoint_ranges(self):
        assert _overlaps(0, 4, 5, 9) is False
        assert _overlaps(5, 9, 0, 4) is False

    def test_touching_boundary_overlaps(self):
        assert _overlaps(0, 4, 4, 9) is True

    def test_contained_range_overlaps(self):
        assert _overlaps(0, 10, 3, 5) is True


class TestSimilarities:
    base = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    windows = np.array(
        [
            [13.0, 23.0, 33.0, 23.0, 13.0],  # base*10+3 (affine 변환, 모양 동일)
            [5.0, 5.0, 4.0, 6.0, 5.0],  # 무관한 패턴
        ]
    )

    def test_cosine_is_invariant_to_affine_transform(self):
        sims = _similarities(self.base, self.windows, metric="cosine")
        assert sims[0] == pytest.approx(1.0, abs=1e-9)
        assert sims[1] < sims[0]

    def test_pearson_is_invariant_to_affine_transform(self):
        sims = _similarities(self.base, self.windows, metric="pearson")
        assert sims[0] == pytest.approx(1.0, abs=1e-9)
        assert sims[1] < sims[0]


class TestFindSimilar:
    def test_returns_none_for_single_day_range(self, monkeypatch):
        dates = _dates(10)
        closes = np.arange(10, dtype=float)
        monkeypatch.setattr(analysis, "load_closes", lambda: (dates, closes))

        assert find_similar(dates[0], dates[0]) is None

    def test_returns_none_when_no_future_days_available(self, monkeypatch):
        dates = _dates(10)
        closes = np.arange(10, dtype=float)
        monkeypatch.setattr(analysis, "load_closes", lambda: (dates, closes))

        # 기준 구간이 전체 데이터를 거의 다 차지하면 미래 NEXT_DATE 일을 남길 수 없다.
        assert find_similar(dates[0], dates[-1]) is None

    def test_finds_scaled_shifted_match(self, monkeypatch):
        pattern = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
        noise = np.array([5.0, 5.0, 4.0, 6.0, 5.0, 4.0, 6.0])
        closes = np.concatenate([pattern, noise, pattern * 10 + 3, noise])
        dates = _dates(len(closes))
        monkeypatch.setattr(analysis, "load_closes", lambda: (dates, closes))

        result = find_similar(dates[0], dates[4], metric="cosine", top=1)

        assert result is not None
        assert result["base"]["start"] == dates[0]
        assert result["base"]["end"] == dates[4]
        best = result["matches"][0]
        assert best["start"] == dates[len(pattern) + len(noise)]
        assert best["similarity"] > 0.99

    def test_matches_never_overlap_each_other_or_base(self, monkeypatch):
        pattern = np.array([1.0, 3.0, 2.0, 4.0, 1.0])
        gap = np.array([9.0, 9.0])
        closes = np.concatenate(
            [pattern] + [np.concatenate([gap, pattern]) for _ in range(4)]
        )
        dates = _dates(len(closes))
        monkeypatch.setattr(analysis, "load_closes", lambda: (dates, closes))

        result = find_similar(dates[0], dates[4], metric="pearson", top=3)

        assert result is not None
        spans = [
            (dates.index(m["start"]), dates.index(m["end"]))
            for m in result["matches"]
        ]
        for i in range(len(spans)):
            for j in range(i + 1, len(spans)):
                a0, a1 = spans[i]
                b0, b1 = spans[j]
                assert a1 < b0 or a0 > b1
