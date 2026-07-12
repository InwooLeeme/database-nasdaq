import React, { useEffect, useRef } from "react";
import { createChart, LineSeries } from "lightweight-charts";

// 기준 구간과 유사 구간을 정규화해 같은 x축(거래일 경과) 위에 겹쳐 그리기.
const ComparisonChart = ({ base, match }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !base || !match) return;

    const chart = createChart(el, {
      autoSize: true,
      layout: { background: { color: "transparent" }, textColor: "#8b93a7" },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.08)" },
        horzLines: { color: "rgba(255, 255, 255, 0.08)" },
      },
      rightPriceScale: { borderColor: "rgba(255, 255, 255, 0.15)" },
      timeScale: { visible: false }, // x축은 인덱스(거래일 경과)라 날짜 라벨을 숨긴다
    });

    // index -> 하루 간격 타임스탬프(라벨은 숨김). 정규화 값(0~1)을 y로.
    const toPoints = (series) =>
      series.map((value, i) => ({ time: i * 86400, value }));

    const baseLine = chart.addSeries(LineSeries, {
      color: "#9ca3af",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const matchLine = chart.addSeries(LineSeries, {
      color: "#f5a524",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    baseLine.setData(toPoints(base.series));
    matchLine.setData(toPoints(match.series));
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [base, match]);

  return <div ref={containerRef} style={{ width: "100%", height: 300 }} />;
};

export default ComparisonChart;
