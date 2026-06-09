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
      <h1 className="title">나스닥 패턴 분석</h1>

      <div className="controls">
        <label>
          기준 시작일
          <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        </label>
        <label>
          기준 종료일
          <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </label>
        <label>
          지표
          <select value={metric} onChange={(e) => setMetric(e.target.value)}>
            <option value="cosine">코사인</option>
            <option value="pearson">피어슨</option>
          </select>
        </label>
        <button onClick={analyze} disabled={loading}>
          {loading ? "분석 중..." : "유사 구간 찾기"}
        </button>
      </div>

      {error && <p className="error">⚠ {error}</p>}

      <div className="chart">
        <Chart highlights={highlights} />
      </div>

      {result && result.matches.length > 0 && (
        <div className="result">
          <div className="matchList">
            <h3>유사 구간 (상위 {result.matches.length})</h3>
            <ul>
              {result.matches.map((m, i) => (
                <li
                  key={m.start}
                  className={i === selected ? "active" : ""}
                  onClick={() => setSelected(i)}
                >
                  <span>{m.start} ~ {m.end}</span>
                  <span className="sim">{(m.similarity * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="comparison">
            <h3>
              기준({result.base.start}~{result.base.end}) vs{" "}
              {result.matches[selected].start}~{result.matches[selected].end}
            </h3>
            <ComparisonChart base={result.base} match={result.matches[selected]} />
            <p className="legend">
              <span className="dot base"></span> 기준 구간
              <span className="dot match"></span> 유사 구간(+이후 {result.nextDays}일)
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
