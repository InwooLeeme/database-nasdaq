import React, { useEffect, useRef, useState } from "react";
import { createChart, CandlestickSeries } from "lightweight-charts";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// "15,605.48" -> 15605.48
const toNumber = (value) => Number(String(value).split(",").join(""));

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

const Chart = () => {
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let chart;
    let disposed = false;
    const chartElement = containerRef.current;

    const load = async () => {
      const res = await fetch(`${API_URL}/nasdaq_chart`);
      const json = await res.json();
      if (disposed || !chartElement) return;

      // lightweight-charts 는 시간 오름차순 + 중복 없는 데이터를 요구한다.
      // API 는 날짜 내림차순으로 주므로 정렬하고, 날짜 문자열의 공백("2024- 05- 01")을 제거한다.
      const seen = new Set();
      const data = json
        .map((item) => ({
          time: item.date.replace(/\s/g, ""),
          open: toNumber(item.stock_market_price),
          high: toNumber(item.stock_high_price),
          low: toNumber(item.stock_low_price),
          close: toNumber(item.stock_closing_price),
        }))
        .filter((d) => {
          if (!DATE_RE.test(d.time) || seen.has(d.time)) return false;
          if (![d.open, d.high, d.low, d.close].every(Number.isFinite)) return false;
          seen.add(d.time);
          return true;
        })
        .sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));

      chart = createChart(chartElement, {
        autoSize: true,
        layout: {
          background: { color: "transparent" },
          textColor: "#d1d4dc",
        },
        grid: {
          vertLines: { color: "rgba(255, 255, 255, 0.06)" },
          horzLines: { color: "rgba(255, 255, 255, 0.06)" },
        },
        rightPriceScale: { borderColor: "rgba(255, 255, 255, 0.2)" },
        timeScale: { borderColor: "rgba(255, 255, 255, 0.2)" },
      });

      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#26a69a",
        downColor: "#ef5350",
        borderVisible: false,
        wickUpColor: "#26a69a",
        wickDownColor: "#ef5350",
      });
      series.setData(data);
      chart.timeScale().fitContent();
      setLoading(false);
    };

    load();

    return () => {
      disposed = true;
      if (chart) chart.remove();
    };
  }, []);

  return (
    <div>
      {loading && <h1>로딩중...</h1>}
      <div ref={containerRef} style={{ width: "100%", height: 500 }} />
    </div>
  );
};

export default Chart;
