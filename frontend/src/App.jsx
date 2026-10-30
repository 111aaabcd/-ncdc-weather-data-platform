import { useEffect, useMemo, useRef, useState } from "react";
import * as echarts from "echarts";
import chinaGeoJson from "./assets/china.json";

echarts.registerMap("china", chinaGeoJson);

const MONTHS = Array.from({ length: 12 }, (_, index) => `${index + 1}月`);
const MODEL_LABELS = {
  seasonal_naive: "季节朴素基线",
  harmonic_trend: "谐波趋势回归",
  month_dummy_trend: "月份哑变量趋势回归",
  harmonic_seasonal_blend_v1: "谐波与季节基线混合",
};

function Chart({ option, className = "chart", label }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return undefined;
    const instance = echarts.init(ref.current, null, { renderer: "canvas" });
    instance.setOption(option, true);
    const resize = () => instance.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      instance.dispose();
    };
  }, [option]);

  return <div ref={ref} className={className} role="img" aria-label={label} />;
}

function Panel({ title, subtitle, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <header className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <span className="panel-mark" aria-hidden="true" />
      </header>
      {children}
    </section>
  );
}

function Dashboard({ data, city, year, onCityChange, onYearChange }) {
  const axisStyle = { color: "#6f8eb9", fontSize: 11 };
  const splitLine = { lineStyle: { color: "rgba(92, 151, 205, 0.13)" } };
  const tooltip = {
    trigger: "axis",
    backgroundColor: "rgba(2, 18, 45, 0.96)",
    borderColor: "#23b8e9",
    textStyle: { color: "#d8f5ff" },
  };

  const tempOption = useMemo(() => ({
    animationDuration: 700,
    tooltip,
    legend: { data: ["平均", "最高", "最低"], right: 8, top: 0, textStyle: { color: "#86a6ce" } },
    grid: { left: 42, right: 12, top: 34, bottom: 28 },
    xAxis: { type: "category", data: MONTHS, axisLabel: axisStyle, axisLine: { lineStyle: { color: "#31567c" } } },
    yAxis: { type: "value", name: "°C", nameTextStyle: axisStyle, axisLabel: axisStyle, splitLine },
    series: [
      { name: "平均", type: "line", smooth: true, symbolSize: 6, data: data.monthly.map((item) => item.avg_temp_c), lineStyle: { width: 3, color: "#00d9ff" }, itemStyle: { color: "#00d9ff" } },
      { name: "最高", type: "line", smooth: true, symbol: "none", data: data.monthly.map((item) => item.max_temp_c), lineStyle: { width: 1.5, color: "#ffb547", type: "dashed" } },
      { name: "最低", type: "line", smooth: true, symbol: "none", data: data.monthly.map((item) => item.min_temp_c), lineStyle: { width: 1.5, color: "#7d8dff", type: "dashed" } },
    ],
  }), [data]);

  const rankOption = useMemo(() => {
    const ranking = [...data.rankings].sort((a, b) => b.precip_mm - a.precip_mm);
    return {
      tooltip: { ...tooltip, trigger: "item", formatter: ({ name, value }) => `${name}<br/>年降水 ${value} mm` },
      grid: { left: 60, right: 38, top: 10, bottom: 22 },
      xAxis: { type: "value", axisLabel: axisStyle, splitLine },
      yAxis: { type: "category", inverse: true, data: ranking.map((item) => item.city), axisLabel: { ...axisStyle, color: "#b9d9f4" }, axisLine: { show: false }, axisTick: { show: false } },
      series: [{
        type: "bar",
        data: ranking.map((item) => item.precip_mm),
        barWidth: 10,
        itemStyle: { color: "#168cf2", borderColor: "#47d8ff", borderWidth: 1, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: "right", color: "#8cb7d8", fontSize: 10 },
      }],
    };
  }, [data]);

  const mapOption = useMemo(() => ({
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(2, 18, 45, 0.96)",
      borderColor: "#23b8e9",
      textStyle: { color: "#d8f5ff" },
      formatter: ({ name, value }) => value ? `${name}<br/>年平均温度 ${value[2]} °C` : name,
    },
    visualMap: {
      min: -2,
      max: 24,
      calculable: false,
      orient: "horizontal",
      left: "center",
      bottom: 4,
      text: ["暖", "冷"],
      textStyle: { color: "#86a6ce" },
      inRange: { color: ["#2364ff", "#00d9ff", "#d7f63a", "#ff8a3d"] },
    },
    geo: {
      map: "china",
      roam: true,
      zoom: 1.1,
      label: { show: false },
      itemStyle: { areaColor: "#0b4ea7", borderColor: "#37b9ee", borderWidth: 1 },
      emphasis: { label: { show: true, color: "#fff" }, itemStyle: { areaColor: "#1269ca" } },
    },
    series: [{
      name: "城市年均温",
      type: "effectScatter",
      coordinateSystem: "geo",
      data: data.city_points.map((item) => ({
        name: item.city,
        value: [item.longitude, item.latitude, item.avg_temp_c],
      })),
      symbolSize: (value) => Math.max(10, 10 + value[2] / 2),
      rippleEffect: { scale: 2.8, brushType: "stroke" },
      itemStyle: { color: "#f8f334", shadowBlur: 12, shadowColor: "#f8f334" },
      label: { show: true, formatter: "{b}", position: "right", color: "#e7fbff", fontSize: 11 },
    }],
  }), [data]);

  const forecastOption = useMemo(() => {
    const historyLabels = data.monthly.map((item) => `${year}-${String(item.month).padStart(2, "0")}`);
    const labels = [...historyLabels, ...data.forecast.map((item) => item.target_month)];
    const actual = [...data.monthly.map((item) => item.avg_temp_c), ...Array(data.forecast.length).fill(null)];
    const forecast = [
      ...Array(Math.max(0, data.monthly.length - 1)).fill(null),
      data.monthly.at(-1)?.avg_temp_c ?? null,
      ...data.forecast.map((item) => item.forecast_temp_c),
    ];
    return {
      tooltip,
      legend: { data: ["历史月均温", "未来预测"], right: 4, top: 0, textStyle: { color: "#86a6ce" } },
      grid: { left: 42, right: 12, top: 34, bottom: 42 },
      xAxis: { type: "category", data: labels, axisLabel: { ...axisStyle, interval: 2, rotate: 34 }, axisLine: { lineStyle: { color: "#31567c" } } },
      yAxis: { type: "value", name: "°C", nameTextStyle: axisStyle, axisLabel: axisStyle, splitLine },
      series: [
        { name: "历史月均温", type: "line", data: actual, showSymbol: false, lineStyle: { width: 2, color: "#00d9ff" } },
        { name: "未来预测", type: "line", data: forecast, showSymbol: true, symbolSize: 5, lineStyle: { width: 2.5, color: "#ff9f43" }, itemStyle: { color: "#ff9f43" }, areaStyle: { color: "rgba(255,159,67,0.08)" } },
      ],
    };
  }, [data, year]);

  const metric = data.model_metric;
  const improvement = metric && metric.baseline_mae_c !== 0
    ? ((metric.baseline_mae_c - metric.mae_c) / metric.baseline_mae_c * 100)
    : 0;

  return (
    <main className="dashboard-shell">
      <header className="hero">
        <div className="hero-rule" aria-hidden="true" />
        <div>
          <p className="eyebrow">NOAA / NCEI · GLOBAL SUMMARY OF THE DAY</p>
          <h1>NCDC 气象数据分析与预测平台</h1>
          <p>2019–2024 · 8个中国城市站点 · ETL、回测与可视化一体化</p>
        </div>
        <div className="filters" aria-label="仪表盘筛选器">
          <label>城市
            <select value={city} onChange={(event) => onCityChange(event.target.value)}>
              {data.meta.cities.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label>年份
            <select value={year} onChange={(event) => onYearChange(Number(event.target.value))}>
              {data.meta.years.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
        </div>
      </header>

      <section className="dashboard-grid">
        <div className="column side-column">
          <Panel title={`${city}${year}年月度气温`} subtitle="平均/最高/最低温度（°C）">
            <Chart option={tempOption} label={`${city}${year}年月度气温折线图`} />
          </Panel>
          <Panel title={`${year}年城市降水排名`} subtitle="仅显示降水记录覆盖率≥80%的站点（mm）">
            <Chart option={rankOption} label={`${year}年城市降水排名条形图`} />
          </Panel>
        </div>

        <Panel title={`${year}年城市气温空间分布`} subtitle="滚轮缩放 · 拖拽移动 · 点击查看站点" className="map-panel">
          <Chart option={mapOption} className="map-chart" label={`${year}年中国城市气温地图`} />
          <div className="map-caption">
            <strong>{data.city_points.length}</strong>
            <span>个有效站点</span>
            <i />
            <strong>{data.quality.start_date}</strong>
            <span>数据起始</span>
          </div>
        </Panel>

        <div className="column side-column">
          <Panel title={`${city}未来12个月气温预测`} subtitle={`${MODEL_LABELS[metric?.model] ?? "候选模型"}；橙色为预测结果`}>
            <Chart option={forecastOption} label={`${city}历史气温和未来预测折线图`} />
          </Panel>
          <Panel title="模型与数据质量" subtitle="先确认数据可信，再解释预测结果">
            <div className="quality-list">
              <div><span>年平均温度</span><strong>{data.kpis.year_avg_temp_c} °C</strong></div>
              <div><span>全年累计降水</span><strong>{data.kpis.year_precip_mm ?? "--"} mm</strong></div>
              <div><span>留出集 RMSE</span><strong>{metric?.rmse_c} °C</strong></div>
              <div><span>相对季节基线</span><strong>{improvement >= 0 ? "+" : ""}{improvement.toFixed(1)}%</strong></div>
            </div>
            <p className="model-note">先用2023年验证集选模型，再用2024年测试集评估。当前城市降水记录覆盖率为{(data.kpis.precip_coverage * 100).toFixed(1)}%；低于80%时不展示年降水。模型未使用湿度、气压或数值天气预报特征。</p>
          </Panel>
        </div>
      </section>

      <footer>
        <div><span className="status-dot" /> ETL 与 API 已连接</div>
        <p>来源：NOAA/NCEI Global Summary of the Day · 温度已换算为摄氏度 · 降水已换算为毫米</p>
        <div>最近处理：{data.meta.latest_etl?.completed_at?.slice(0, 10) ?? "--"}</div>
      </footer>
    </main>
  );
}

export function App() {
  const [city, setCity] = useState("北京");
  const [year, setYear] = useState(2024);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setError("");
    fetch(`/api/summary/?city=${encodeURIComponent(city)}&year=${year}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`API ${response.status}`);
        return response.json();
      })
      .then(setData)
      .catch((reason) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    return () => controller.abort();
  }, [city, year]);

  if (error) {
    return <main className="state-screen"><h1>数据服务未就绪</h1><p>{error}</p><code>先运行 python -m pipeline.run_pipeline，再启动 Django。</code></main>;
  }
  if (!data) {
    return <main className="state-screen"><div className="loader" /><h1>正在加载气象数据</h1><p>读取月度指标、预测结果和数据质量信息…</p></main>;
  }
  return <Dashboard data={data} city={city} year={year} onCityChange={setCity} onYearChange={setYear} />;
}
