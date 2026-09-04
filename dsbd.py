import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ============================================================
# 기본 설정
# ============================================================

DB_FILE = r"C:\Users\user\work\middleware\THC\sensor_data.db"

st.set_page_config(
    page_title="Environmental Sensor Dashboard",
    page_icon="🌡️",
    layout="wide",
)

# 센서별 임계값 (필요에 맞게 조정하세요)
THRESHOLDS = {
    "temperature": {"low": 18, "high": 28, "unit": "°C"},
    "humidity": {"low": 30, "high": 70, "unit": "%"},
    "cds_value": {"low": 200, "high": 3800, "unit": "ADC"},
    "sound_value": {"low": 0, "high": 700, "unit": ""},
    "distance_cm": {"low": 5, "high": 400, "unit": "cm"},
}

# 센서별 고정 accent 컬러 (KPI 카드 좌측 바 + 차트 공용)
ACCENT = {
    "temperature": "#FF5252",
    "humidity": "#00B8D9",
    "cds_value": "#FFAB00",
    "sound_value": "#D500F9",
    "distance_cm": "#00E676",
}


# ============================================================
# 고시인성 Custom CSS (라이트/다크 모드 공통)
# ============================================================

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: rgba(127, 127, 127, 0.08) !important;
        border: 1px solid rgba(127, 127, 127, 0.3) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stMetricLabel"] { font-weight: 700 !important; font-size: 0.95rem !important; }
    div[data-testid="stMetricValue"] { font-weight: 800 !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px; padding: 8px 16px; font-weight: 600; }

    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.78rem;
        margin-left: 6px;
    }
    .status-ok    { background-color: rgba(0, 230, 118, 0.18); color: #00A152; border: 1px solid rgba(0,230,118,0.4); }
    .status-warn  { background-color: rgba(255, 171, 0, 0.18); color: #B26A00; border: 1px solid rgba(255,171,0,0.4); }
    .status-alert { background-color: rgba(255, 82, 82, 0.18); color: #C62828; border: 1px solid rgba(255,82,82,0.4); }

    /* 카드형 컨테이너 좌측 accent 바 */
    .accent-card {
        border-radius: 10px;
        padding: 12px 16px;
        background-color: rgba(127,127,127,0.06);
        border-left: 5px solid var(--accent, #999);
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌡️ Environmental Sensor Dashboard")
st.caption("Arduino Sensor Monitoring (온/습도, 조도, 소리, 거리)")


# ============================================================
# SQLite 데이터 읽기
# ============================================================

@st.cache_data(ttl=2)
def load_all_sensor_data():
    conn = sqlite3.connect(DB_FILE)

    df_sensor = pd.read_sql_query(
        "SELECT id, temperature, humidity, created_at FROM sensor_data ORDER BY created_at", conn)
    if not df_sensor.empty:
        df_sensor["created_at"] = pd.to_datetime(df_sensor["created_at"])

    df_cds = pd.read_sql_query(
        "SELECT id, timestamp AS created_at, cds_value FROM cds_log ORDER BY timestamp", conn)
    if not df_cds.empty:
        df_cds["created_at"] = pd.to_datetime(df_cds["created_at"])

    df_sound = pd.read_sql_query(
        "SELECT id, timestamp AS created_at, sound_value, deviation FROM sound_log ORDER BY timestamp", conn)
    if not df_sound.empty:
        df_sound["created_at"] = pd.to_datetime(df_sound["created_at"])

    df_distance = pd.read_sql_query(
        "SELECT id, timestamp AS created_at, duration_us, distance_cm FROM distance_logs ORDER BY timestamp", conn)
    if not df_distance.empty:
        df_distance["created_at"] = pd.to_datetime(df_distance["created_at"])

    conn.close()
    return df_sensor, df_cds, df_sound, df_distance


df_sensor, df_cds, df_sound, df_distance = load_all_sensor_data()

if df_sensor.empty and df_cds.empty and df_sound.empty and df_distance.empty:
    st.warning("수집된 데이터가 없습니다. DB 연결을 확인해주세요.")
    st.stop()


# ============================================================
# 공통 헬퍼
# ============================================================

def apply_high_contrast_layout(fig, title_text, height=290):
    fig.update_layout(
        title=dict(text=f"<b>{title_text}</b>", font=dict(size=14)),
        height=height,
        margin=dict(l=25, r=20, t=40, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(127,127,127,0.2)", zerolinecolor="rgba(127,127,127,0.3)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(127,127,127,0.2)", zerolinecolor="rgba(127,127,127,0.3)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def status_of(value, key):
    """임계값 기준 상태 판정: ok / warn / alert"""
    th = THRESHOLDS.get(key)
    if th is None or value is None or pd.isna(value):
        return "ok"
    span = th["high"] - th["low"]
    margin = span * 0.08
    if value < th["low"] or value > th["high"]:
        return "alert"
    if value < th["low"] + margin or value > th["high"] - margin:
        return "warn"
    return "ok"


def status_badge(status):
    label = {"ok": "정상", "warn": "주의", "alert": "경고"}[status]
    cls = {"ok": "status-ok", "warn": "status-warn", "alert": "status-alert"}[status]
    return f'<span class="status-badge {cls}">{label}</span>'


def make_gauge(value, key, title):
    th = THRESHOLDS[key]
    status = status_of(value, key)
    bar_color = {"ok": "#00C853", "warn": "#FFAB00", "alert": "#FF1744"}[status]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(value),
        number={"suffix": f" {th['unit']}", "font": {"size": 26}},
        title={"text": title, "font": {"size": 13}},
        gauge={
            "axis": {"range": [th["low"] - (th["high"] - th["low"]) * 0.15,
                                th["high"] + (th["high"] - th["low"]) * 0.15]},
            "bar": {"color": bar_color, "thickness": 0.3},
            "steps": [
                {"range": [th["low"], th["high"]], "color": "rgba(0,200,83,0.12)"},
            ],
            "threshold": {
                "line": {"color": bar_color, "width": 3},
                "thickness": 0.85,
                "value": float(value),
            },
        },
    ))
    fig.update_layout(height=180, margin=dict(l=15, r=15, t=45, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", font=dict(size=12))
    return fig


def sparkline(df, x, y, color, height=70):
    fig = px.area(df, x=x, y=y, color_discrete_sequence=[color])
    fig.update_traces(line=dict(width=2), fillcolor=color, opacity=0.25)
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def minmax_norm(s):
    if s.max() == s.min():
        return s * 0 + 0.5
    return (s - s.min()) / (s.max() - s.min())


# ============================================================
# 사이드바 설정
# ============================================================

st.sidebar.header("⚙️ 대시보드 설정")

max_rows = max(len(df_sensor), len(df_cds), len(df_sound), len(df_distance), 1)
min_limit = min(10, max_rows)
max_limit = max(10, min(1000, max_rows))

data_count = st.sidebar.slider(
    "표시할 최근 데이터 개수", min_value=min_limit, max_value=max_limit, value=min(100, max_rows))

chart_style = st.sidebar.radio("📈 추이 차트 스타일", ["라인", "영역(면적)"], horizontal=True)

if st.sidebar.button("🔄 데이터 즉시 새로고침", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(f"⏱️ 마지막 조회: {datetime.now().strftime('%H:%M:%S')}")

df_sensor_v = df_sensor.tail(data_count) if not df_sensor.empty else df_sensor
df_cds_v = df_cds.tail(data_count) if not df_cds.empty else df_cds
df_sound_v = df_sound.tail(data_count) if not df_sound.empty else df_sound
df_distance_v = df_distance.tail(data_count) if not df_distance.empty else df_distance

trend_fn = px.area if chart_style == "영역(면적)" else px.line


# ============================================================
# 상단 종합 경고 배너
# ============================================================

alerts = []
if not df_sensor.empty:
    if status_of(df_sensor.iloc[-1]["temperature"], "temperature") == "alert":
        alerts.append(f"온도 이상: {df_sensor.iloc[-1]['temperature']:.1f}°C")
    if status_of(df_sensor.iloc[-1]["humidity"], "humidity") == "alert":
        alerts.append(f"습도 이상: {df_sensor.iloc[-1]['humidity']:.1f}%")
if not df_cds.empty and status_of(df_cds.iloc[-1]["cds_value"], "cds_value") == "alert":
    alerts.append(f"조도 이상: {df_cds.iloc[-1]['cds_value']:,} ADC")
if not df_sound.empty and status_of(df_sound.iloc[-1]["sound_value"], "sound_value") == "alert":
    alerts.append(f"소음 이상: {df_sound.iloc[-1]['sound_value']:,}")
if not df_distance.empty and status_of(df_distance.iloc[-1]["distance_cm"], "distance_cm") == "alert":
    alerts.append(f"거리 이상: {df_distance.iloc[-1]['distance_cm']:.1f} cm")

if alerts:
    st.error("🚨 **경고 감지:** " + " · ".join(alerts))
else:
    st.success("✅ 모든 센서 값이 정상 범위 내에 있습니다.")


# ============================================================
# 탭 구성
# ============================================================

tab_summary, tab_gauge, tab_detail, tab_data = st.tabs(
    ["📊 종합 한눈에 보기", "🎯 실시간 게이지", "🔍 센서별 상세 분석", "📋 원본 데이터 및 다운로드"])


# ------------------------------------------------------------
# TAB 1: 종합 한눈에 보기
# ------------------------------------------------------------
with tab_summary:
    st.subheader("⚡ 실시간 주요 센서 현황")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        if not df_sensor.empty:
            curr_temp = df_sensor.iloc[-1]["temperature"]
            curr_humi = df_sensor.iloc[-1]["humidity"]
            p_temp = df_sensor.iloc[-2]["temperature"] if len(df_sensor) > 1 else curr_temp
            st.metric("🌡️ 현재 온도", f"{curr_temp:.1f} °C", f"{curr_temp - p_temp:+.1f} °C")
            st.markdown(f"💧 습도: **{curr_humi:.1f}%** {status_badge(status_of(curr_temp, 'temperature'))}",
                        unsafe_allow_html=True)
            if not df_sensor_v.empty:
                st.plotly_chart(sparkline(df_sensor_v, "created_at", "temperature", ACCENT["temperature"]),
                                 use_container_width=True, config={"displayModeBar": False})
        else:
            st.metric("🌡️ 온습도", "N/A")

    with kpi_col2:
        if not df_cds.empty:
            curr_cds = df_cds.iloc[-1]["cds_value"]
            p_cds = df_cds.iloc[-2]["cds_value"] if len(df_cds) > 1 else curr_cds
            st.metric("💡 현재 조도", f"{curr_cds:,} ADC", f"{curr_cds - p_cds:+} ADC")
            st.markdown(f"평균: **{df_cds_v['cds_value'].mean():.1f} ADC** {status_badge(status_of(curr_cds, 'cds_value'))}",
                        unsafe_allow_html=True)
            if not df_cds_v.empty:
                st.plotly_chart(sparkline(df_cds_v, "created_at", "cds_value", ACCENT["cds_value"]),
                                 use_container_width=True, config={"displayModeBar": False})
        else:
            st.metric("💡 조도", "N/A")

    with kpi_col3:
        if not df_sound.empty:
            curr_snd = df_sound.iloc[-1]["sound_value"]
            curr_dev = df_sound.iloc[-1]["deviation"]
            p_snd = df_sound.iloc[-2]["sound_value"] if len(df_sound) > 1 else curr_snd
            st.metric("🔊 소리 크기", f"{curr_snd:,}", f"{curr_snd - p_snd:+}")
            st.markdown(f"편차: **{curr_dev:,}** {status_badge(status_of(curr_snd, 'sound_value'))}",
                        unsafe_allow_html=True)
            if not df_sound_v.empty:
                st.plotly_chart(sparkline(df_sound_v, "created_at", "sound_value", ACCENT["sound_value"]),
                                 use_container_width=True, config={"displayModeBar": False})
        else:
            st.metric("🔊 소리", "N/A")

    with kpi_col4:
        if not df_distance.empty:
            curr_dist = df_distance.iloc[-1]["distance_cm"]
            p_dist = df_distance.iloc[-2]["distance_cm"] if len(df_distance) > 1 else curr_dist
            st.metric("📏 감지 거리", f"{curr_dist:.1f} cm", f"{curr_dist - p_dist:+.1f} cm")
            st.markdown(f"최단: **{df_distance_v['distance_cm'].min():.1f} cm** {status_badge(status_of(curr_dist, 'distance_cm'))}",
                        unsafe_allow_html=True)
            if not df_distance_v.empty:
                st.plotly_chart(sparkline(df_distance_v, "created_at", "distance_cm", ACCENT["distance_cm"]),
                                 use_container_width=True, config={"displayModeBar": False})
        else:
            st.metric("📏 거리", "N/A")

    st.divider()

    st.subheader("📈 센서별 실시간 추이 비교")
    grid_col1, grid_col2 = st.columns(2)

    with grid_col1:
        if not df_sensor_v.empty:
            fig_temp = trend_fn(
                df_sensor_v, x="created_at", y=["temperature", "humidity"],
                labels={"created_at": "시간", "value": "측정값", "variable": "항목"},
                color_discrete_sequence=[ACCENT["temperature"], ACCENT["humidity"]],
            )
            fig_temp = apply_high_contrast_layout(fig_temp, "1. 온·습도 추이 (°C / %)")
            st.plotly_chart(fig_temp, use_container_width=True)

        if not df_sound_v.empty:
            fig_snd = trend_fn(
                df_sound_v, x="created_at", y="sound_value",
                labels={"created_at": "시간", "sound_value": "소리 크기"},
                color_discrete_sequence=[ACCENT["sound_value"]],
            )
            fig_snd = apply_high_contrast_layout(fig_snd, "3. 소리 크기 추이")
            st.plotly_chart(fig_snd, use_container_width=True)

    with grid_col2:
        if not df_cds_v.empty:
            fig_cds = trend_fn(
                df_cds_v, x="created_at", y="cds_value",
                labels={"created_at": "시간", "cds_value": "조도 (ADC)"},
                color_discrete_sequence=[ACCENT["cds_value"]],
            )
            fig_cds = apply_high_contrast_layout(fig_cds, "2. 조도 추이 (ADC)")
            st.plotly_chart(fig_cds, use_container_width=True)

        if not df_distance_v.empty:
            fig_dist = trend_fn(
                df_distance_v, x="created_at", y="distance_cm",
                labels={"created_at": "시간", "distance_cm": "거리 (cm)"},
                color_discrete_sequence=[ACCENT["distance_cm"]],
            )
            fig_dist = apply_high_contrast_layout(fig_dist, "4. 초음파 감지 거리 추이 (cm)")
            st.plotly_chart(fig_dist, use_container_width=True)

    st.divider()
    st.subheader("🧭 정규화 종합 트렌드 (한 화면에서 패턴 비교)")
    norm_frames = []
    if not df_sensor_v.empty:
        norm_frames.append(pd.DataFrame({
            "created_at": df_sensor_v["created_at"], "value": minmax_norm(df_sensor_v["temperature"]),
            "항목": "온도"}))
        norm_frames.append(pd.DataFrame({
            "created_at": df_sensor_v["created_at"], "value": minmax_norm(df_sensor_v["humidity"]),
            "항목": "습도"}))
    if not df_cds_v.empty:
        norm_frames.append(pd.DataFrame({
            "created_at": df_cds_v["created_at"], "value": minmax_norm(df_cds_v["cds_value"]), "항목": "조도"}))
    if not df_sound_v.empty:
        norm_frames.append(pd.DataFrame({
            "created_at": df_sound_v["created_at"], "value": minmax_norm(df_sound_v["sound_value"]), "항목": "소리"}))
    if not df_distance_v.empty:
        norm_frames.append(pd.DataFrame({
            "created_at": df_distance_v["created_at"], "value": minmax_norm(df_distance_v["distance_cm"]),
            "항목": "거리"}))

    if norm_frames:
        df_norm = pd.concat(norm_frames, ignore_index=True)
        fig_norm = px.line(
            df_norm, x="created_at", y="value", color="항목",
            labels={"created_at": "시간", "value": "정규화 값 (0~1)"},
            color_discrete_sequence=[ACCENT["temperature"], ACCENT["humidity"], ACCENT["cds_value"],
                                      ACCENT["sound_value"], ACCENT["distance_cm"]],
        )
        fig_norm = apply_high_contrast_layout(fig_norm, "센서 간 상대적 변화 패턴 비교 (0~1 정규화)", height=320)
        st.plotly_chart(fig_norm, use_container_width=True)
        st.caption("서로 단위가 다른 센서 값을 0~1 범위로 정규화하여 변화 패턴(동조/역행 여부)을 함께 비교합니다.")


# ------------------------------------------------------------
# TAB 2: 실시간 게이지
# ------------------------------------------------------------
with tab_gauge:
    st.subheader("🎯 임계값 기반 실시간 게이지")
    st.caption("각 게이지는 정상 범위(초록 영역)와 현재 값을 함께 보여줍니다. 범위를 벗어나면 바늘 색이 주황/빨강으로 바뀝니다.")

    g1, g2, g3, g4, g5 = st.columns(5)
    with g1:
        if not df_sensor.empty:
            st.plotly_chart(make_gauge(df_sensor.iloc[-1]["temperature"], "temperature", "온도"),
                             use_container_width=True, config={"displayModeBar": False})
    with g2:
        if not df_sensor.empty:
            st.plotly_chart(make_gauge(df_sensor.iloc[-1]["humidity"], "humidity", "습도"),
                             use_container_width=True, config={"displayModeBar": False})
    with g3:
        if not df_cds.empty:
            st.plotly_chart(make_gauge(df_cds.iloc[-1]["cds_value"], "cds_value", "조도"),
                             use_container_width=True, config={"displayModeBar": False})
    with g4:
        if not df_sound.empty:
            st.plotly_chart(make_gauge(df_sound.iloc[-1]["sound_value"], "sound_value", "소리"),
                             use_container_width=True, config={"displayModeBar": False})
    with g5:
        if not df_distance.empty:
            st.plotly_chart(make_gauge(df_distance.iloc[-1]["distance_cm"], "distance_cm", "거리"),
                             use_container_width=True, config={"displayModeBar": False})

    st.divider()
    st.subheader("📋 상태 요약 테이블")
    rows = []
    if not df_sensor.empty:
        t = df_sensor.iloc[-1]["temperature"]
        h = df_sensor.iloc[-1]["humidity"]
        rows.append(["온도", f"{t:.1f} °C", status_of(t, "temperature")])
        rows.append(["습도", f"{h:.1f} %", status_of(h, "humidity")])
    if not df_cds.empty:
        c = df_cds.iloc[-1]["cds_value"]
        rows.append(["조도", f"{c:,} ADC", status_of(c, "cds_value")])
    if not df_sound.empty:
        s = df_sound.iloc[-1]["sound_value"]
        rows.append(["소리", f"{s:,}", status_of(s, "sound_value")])
    if not df_distance.empty:
        d = df_distance.iloc[-1]["distance_cm"]
        rows.append(["거리", f"{d:.1f} cm", status_of(d, "distance_cm")])

    status_kr = {"ok": "🟢 정상", "warn": "🟠 주의", "alert": "🔴 경고"}
    df_status = pd.DataFrame(rows, columns=["센서", "현재값", "상태"])
    df_status["상태"] = df_status["상태"].map(status_kr)
    st.dataframe(df_status, use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# TAB 3: 센서별 상세 분석
# ------------------------------------------------------------
with tab_detail:
    st.subheader("🔍 센서별 상세 지표 및 분포")

    sec1, sec2 = st.columns(2)
    with sec1:
        st.markdown("### 🌡️ 온·습도 상세")
        if not df_sensor_v.empty:
            st.write(f"**평균 온도:** `{df_sensor_v['temperature'].mean():.1f} °C` | "
                     f"**평균 습도:** `{df_sensor_v['humidity'].mean():.1f} %`")
            fig = px.histogram(df_sensor_v, x="temperature", nbins=15,
                                color_discrete_sequence=[ACCENT["temperature"]])
            fig = apply_high_contrast_layout(fig, "온도 분포 히스토그램", height=240)
            st.plotly_chart(fig, use_container_width=True)

            fig_box = px.box(df_sensor_v, y=["temperature", "humidity"],
                              color_discrete_sequence=[ACCENT["temperature"], ACCENT["humidity"]])
            fig_box = apply_high_contrast_layout(fig_box, "온·습도 박스플롯 (분산/이상치 확인)", height=240)
            st.plotly_chart(fig_box, use_container_width=True)

    with sec2:
        st.markdown("### 💡 조도 상세")
        if not df_cds_v.empty:
            st.write(f"**최대 조도:** `{df_cds_v['cds_value'].max():,} ADC` | "
                     f"**최저 조도:** `{df_cds_v['cds_value'].min():,} ADC`")
            fig = px.histogram(df_cds_v, x="cds_value", nbins=15,
                                color_discrete_sequence=[ACCENT["cds_value"]])
            fig = apply_high_contrast_layout(fig, "조도 분포 히스토그램", height=240)
            st.plotly_chart(fig, use_container_width=True)

            fig_gauge_mini = make_subplots(rows=1, cols=1, specs=[[{"type": "indicator"}]])
            fig_gauge_mini.add_trace(go.Indicator(
                mode="number+delta",
                value=df_cds_v["cds_value"].iloc[-1],
                delta={"reference": df_cds_v["cds_value"].mean(), "relative": False},
                title={"text": "현재값 vs 평균"},
            ))
            fig_gauge_mini.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10),
                                          paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gauge_mini, use_container_width=True)

    st.divider()

    sec3, sec4 = st.columns(2)
    with sec3:
        st.markdown("### 🔊 소리 편차 상세")
        if not df_sound_v.empty:
            fig = px.line(df_sound_v, x="created_at", y="deviation",
                           color_discrete_sequence=[ACCENT["sound_value"]])
            fig = apply_high_contrast_layout(fig, "소리 편차(Deviation) 추이", height=240)
            st.plotly_chart(fig, use_container_width=True)

            fig_scatter = px.scatter(df_sound_v, x="sound_value", y="deviation",
                                      color_discrete_sequence=[ACCENT["sound_value"]],
                                      opacity=0.6)
            fig_scatter = apply_high_contrast_layout(fig_scatter, "소리 크기 vs 편차 상관관계", height=240)
            st.plotly_chart(fig_scatter, use_container_width=True)

    with sec4:
        st.markdown("### 📏 초음파 신호 시간 상세")
        if not df_distance_v.empty:
            fig = px.line(df_distance_v, x="created_at", y="duration_us",
                           color_discrete_sequence=[ACCENT["distance_cm"]])
            fig = apply_high_contrast_layout(fig, "신호 반사 시간(duration_us) 추이", height=240)
            st.plotly_chart(fig, use_container_width=True)

            fig_scatter2 = px.scatter(df_distance_v, x="duration_us", y="distance_cm",
                                       color_discrete_sequence=[ACCENT["distance_cm"]],
                                       opacity=0.6)
            fig_scatter2 = apply_high_contrast_layout(fig_scatter2, "반사 시간 vs 거리 관계", height=240)
            st.plotly_chart(fig_scatter2, use_container_width=True)

    st.divider()
    st.subheader("🌡️🔊 온도 × 소리 상관관계 히트맵 (병합 가능 시)")
    if not df_sensor_v.empty and not df_sound_v.empty:
        merged = pd.merge_asof(
            df_sound_v.sort_values("created_at"),
            df_sensor_v.sort_values("created_at"),
            on="created_at", direction="nearest",
        )
        if len(merged) > 3:
            corr = merged[["temperature", "humidity", "sound_value", "deviation"]].corr()
            fig_heat = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            fig_heat = apply_high_contrast_layout(fig_heat, "센서 간 상관계수 히트맵", height=350)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("상관관계 계산을 위한 데이터가 충분하지 않습니다.")


# ------------------------------------------------------------
# TAB 4: 원본 데이터 및 다운로드
# ------------------------------------------------------------
with tab_data:
    st.subheader("📋 수집 데이터 통합 조회 및 다운로드")

    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["온습도", "조도", "소리", "거리"])

    with d_tab1:
        st.dataframe(
            df_sensor_v.sort_values("created_at", ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "temperature": st.column_config.ProgressColumn(
                    "온도(°C)", min_value=float(df_sensor_v["temperature"].min()) if not df_sensor_v.empty else 0,
                    max_value=float(df_sensor_v["temperature"].max()) if not df_sensor_v.empty else 1, format="%.1f"),
                "humidity": st.column_config.ProgressColumn(
                    "습도(%)", min_value=float(df_sensor_v["humidity"].min()) if not df_sensor_v.empty else 0,
                    max_value=float(df_sensor_v["humidity"].max()) if not df_sensor_v.empty else 1, format="%.1f"),
            },
        )
        st.download_button("온습도 CSV 다운로드", data=df_sensor_v.to_csv(index=False).encode("utf-8-sig"),
                            file_name="sensor_data.csv")

    with d_tab2:
        st.dataframe(df_cds_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("조도 CSV 다운로드", data=df_cds_v.to_csv(index=False).encode("utf-8-sig"),
                            file_name="cds_data.csv")

    with d_tab3:
        st.dataframe(df_sound_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("소리 CSV 다운로드", data=df_sound_v.to_csv(index=False).encode("utf-8-sig"),
                            file_name="sound_data.csv")

    with d_tab4:
        st.dataframe(df_distance_v.sort_values("created_at", ascending=False), use_container_width=True,
                     hide_index=True)
        st.download_button("거리 CSV 다운로드", data=df_distance_v.to_csv(index=False).encode("utf-8-sig"),
                            file_name="distance_data.csv")