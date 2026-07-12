import React, { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  createSeriesMarkers,
} from "lightweight-charts";
import { API_URL } from "../api";

const Chart = ({ highlights = [] }) => {
  const containerRef = useRef(null);
  const seriesRef = useRef(null);
  const markersRef = useRef(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let chart;
    let disposed = false;
    const chartElement = containerRef.current;

    const load = async () => {
      const res = await fetch(`${API_URL}/nasdaq_chart`);
      const json = await res.json();
      if (disposed || !chartElement) return;

      // lightweight-charts 는 시간 오름차순 데이터를 요구한다.
      // API 는 날짜 내림차순으로 주므로 뒤집기만 하면 된다.
      const data = json
        .slice()
        .reverse()
        .map((item) => ({
          time: item.date,
          open: item.stock_market_price,
          high: item.stock_high_price,
          low: item.stock_low_price,
          close: item.stock_closing_price,
        }));

      chart = createChart(chartElement, {
        autoSize: true,
        layout: {
          background: { color: "transparent" },
          textColor: "#8b93a7",
        },
        grid: {
          vertLines: { color: "rgba(255, 255, 255, 0.08)" },
          horzLines: { color: "rgba(255, 255, 255, 0.08)" },
        },
        rightPriceScale: { borderColor: "rgba(255, 255, 255, 0.15)" },
        timeScale: { borderColor: "rgba(255, 255, 255, 0.15)" },
      });

      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#26a69a",
        downColor: "#ef5350",
        borderVisible: false,
        wickUpColor: "#26a69a",
        wickDownColor: "#ef5350",
      });
      series.setData(data);
      seriesRef.current = series;
      markersRef.current = createSeriesMarkers(series, []);
      chart.timeScale().fitContent();
      setLoading(false);
    };

    load();

    return () => {
      disposed = true;
      seriesRef.current = null;
      markersRef.current = null;
      if (chart) chart.remove();
    };
  }, []);

  // 유사 구간을 메인 차트 위에 마커로 표시한다.
  useEffect(() => {
    if (!markersRef.current) return;
    const markers = (highlights || [])
      .map((h) => ({
        time: h.start,
        position: "aboveBar",
        color: "#f5a524",
        shape: "arrowDown",
        text: "유사",
      }))
      .sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
    markersRef.current.setMarkers(markers);
  }, [highlights]);

  return (
    <div className="chart-container">
      {loading && (
        <div className="chart-loading">
          <span className="spinner spinner-accent" />
          <span>차트 불러오는 중</span>
        </div>
      )}
      <div ref={containerRef} style={{ width: "100%", height: 500 }} />
    </div>
  );
};

export default Chart;
