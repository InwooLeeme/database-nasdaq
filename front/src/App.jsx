import "./App.css";
import { useState } from "react";
import Chart from "./components/chart";
import ComparisonChart from "./components/ComparisonChart";
import { API_URL } from "./api";

function App() {
  const [start, setStart] = useState("2018-02-01");
  const [end, setEnd] = useState("2018-02-20");
  const [metric, setMetric] = useState("cosine");
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyze = async () => {
    setLoading(true);
    setError("");
    try {
      const url = `${API_URL}/similar_patterns?start=${start}&end=${end}&metric=${metric}&top=5`;
      const res = await fetch(url);
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail || `요청 실패 (${res.status})`);
      }
      setResult(body);
      setSelected(0);
    } catch (e) {
      setError(e.message || "분석에 실패했습니다");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const highlights = result
    ? result.matches.map((m) => ({ start: m.start, end: m.end }))
    : [];

  return (
    <div className="App">
      <header className="appbar">
        <div className="brand">
          <span className="brand-mark">◆</span>
          <div>
            <div className="brand-name">NASDAQ PATTERN</div>
            <div className="brand-tagline">과거 패턴 유사도 분석</div>
          </div>
        </div>
        <span className="appbar-meta">1980 – 2024 · 일봉</span>
      </header>

      <section className="panel controls-panel">
        <div className="field-group">
          <label className="field">
            <span className="field-label">기준 시작일</span>
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          </label>
          <label className="field">
            <span className="field-label">기준 종료일</span>
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
          </label>
          <div className="field">
            <span className="field-label">유사도 지표</span>
            <div className="segmented" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={metric === "cosine"}
                onClick={() => setMetric("cosine")}
              >
                코사인
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={metric === "pearson"}
                onClick={() => setMetric("pearson")}
              >
                피어슨
              </button>
            </div>
          </div>
        </div>
        <button className="btn-primary" onClick={analyze} disabled={loading}>
          {loading && <span className="spinner" />}
          {loading ? "분석 중" : "유사 구간 찾기"}
        </button>
      </section>

      {error && <div className="banner banner-error">⚠ {error}</div>}

      <section className="panel chart-panel">
        <div className="panel-header">
          <h2 className="panel-title">나스닥 종합지수</h2>
          <div className="legend-inline">
            <span><span className="legend-dot up"></span>상승</span>
            <span><span className="legend-dot down"></span>하락</span>
          </div>
        </div>
        <Chart highlights={highlights} />
      </section>

      {result && result.matches.length > 0 && (
        <section className="results-grid">
          <div className="panel match-panel">
            <h3 className="panel-title">
              유사 구간
              <span className="panel-title-count">TOP {result.matches.length}</span>
            </h3>
            <ul className="match-list">
              {result.matches.map((m, i) => (
                <li
                  key={m.start}
                  role="button"
                  tabIndex={0}
                  className={[i === selected ? "active" : "", i === 0 ? "is-best" : ""]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setSelected(i)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") setSelected(i);
                  }}
                >
                  <span className="match-rank">{String(i + 1).padStart(2, "0")}</span>
                  <span className="match-info">
                    <span className="match-range">{m.start} ~ {m.end}</span>
                    <span className="match-bar-track">
                      <span
                        className="match-bar-fill"
                        style={{ width: `${Math.max(0, Math.min(100, m.similarity * 100))}%` }}
                      />
                    </span>
                  </span>
                  <span className="match-sim">{(m.similarity * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="panel compare-panel">
            <div className="panel-header">
              <h3 className="panel-title">구간 비교</h3>
              <p className="compare-range">
                {result.base.start}~{result.base.end} vs{" "}
                {result.matches[selected].start}~{result.matches[selected].end}
              </p>
            </div>
            <ComparisonChart base={result.base} match={result.matches[selected]} />
            <p className="legend">
              <span className="dot base"></span> 기준 구간
              <span className="dot match"></span> 유사 구간(+이후 {result.nextDays}일)
            </p>
          </div>
        </section>
      )}

      {!result && !loading && !error && (
        <p className="hint">구간을 선택하고 유사 구간 찾기를 눌러보세요</p>
      )}
    </div>
  );
}

export default App;
