import sqlite3
import pandas as pd
import plotly.express as px
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

st.title("🌡️ Environmental Sensor Dashboard")
st.caption("Arduino DHT11 & CDS Light Sensor Monitoring")


# ============================================================
# SQLite 데이터 읽기 (독립적 처리)
# ============================================================

def load_sensor_data():
    """온도 및 습도 데이터 로드"""
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT id, temperature, humidity, created_at 
        FROM sensor_data
        ORDER BY created_at
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def load_cds_data():
    """조도(CDS) 데이터 로드"""
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT id, timestamp AS created_at, cds_value 
        FROM cds_log
        ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


# ============================================================
# 데이터 로드
# ============================================================

df_sensor = load_sensor_data()
df_cds = load_cds_data()

if df_sensor.empty and df_cds.empty:
    st.warning("수집된 데이터가 없습니다.")
    st.stop()


# ============================================================
# 사이드바
# ============================================================

st.sidebar.header("Dashboard 설정")

max_rows = max(len(df_sensor), len(df_cds), 1)
min_limit = min(10, max_rows)
max_limit = max(10, min(500, max_rows))

if min_limit == max_limit:
    data_count = max_rows
    st.sidebar.info(f"현재 최대 {max_rows}개의 데이터가 표시됩니다.")
else:
    data_count = st.sidebar.slider(
        "표시할 최근 데이터 개수",
        min_value=min_limit,
        max_value=max_limit,
        value=min(100, max_rows),
    )

df_sensor_view = df_sensor.tail(data_count) if not df_sensor.empty else df_sensor
df_cds_view = df_cds.tail(data_count) if not df_cds.empty else df_cds


# ============================================================
# 1. 온·습도 섹션 (기존 유지)
# ============================================================

st.header("1. 🌡️ 온도 & 💧 습도 모니터링")

if not df_sensor_view.empty:
    latest_s = df_sensor.iloc[-1]
    latest_temp = latest_s["temperature"]
    latest_humi = latest_s["humidity"]
    
    if len(df_sensor) >= 2:
        prev_s = df_sensor.iloc[-2]
        temp_delta = latest_temp - prev_s["temperature"]
        humi_delta = latest_humi - prev_s["humidity"]
    else:
        temp_delta, humi_delta = 0, 0

    # KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재 온도", f"{latest_temp:.1f} °C", f"{temp_delta:+.1f} °C")
    col2.metric("현재 습도", f"{latest_humi:.1f} %", f"{humi_delta:+.1f} %")
    col3.metric("온습도 데이터 건수", f"{len(df_sensor):,} 건")
    col4.metric("최근 측정 시간", latest_s["created_at"].strftime("%H:%M:%S"))

    # 통계
    st.markdown("#### 온·습도 요약 통계")
    st_col1, st_col2, st_col3, st_col4 = st.columns(4)
    st_col1.metric("평균 온도", f"{df_sensor_view['temperature'].mean():.1f} °C")
    st_col2.metric("최고 / 최저 온도", f"{df_sensor_view['temperature'].max():.1f} / {df_sensor_view['temperature'].min():.1f} °C")
    st_col3.metric("평균 습도", f"{df_sensor_view['humidity'].mean():.1f} %")
    st_col4.metric("최고 / 최저 습도", f"{df_sensor_view['humidity'].max():.1f} / {df_sensor_view['humidity'].min():.1f} %")

    # 그래프
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig_temp = px.line(
            df_sensor_view, x="created_at", y="temperature", markers=True,
            title="온도 변화 추이", labels={"created_at": "시간", "temperature": "온도 (°C)"}
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    with g_col2:
        fig_humi = px.line(
            df_sensor_view, x="created_at", y="humidity", markers=True,
            title="습도 변화 추이", labels={"created_at": "시간", "humidity": "습도 (%)"}
        )
        st.plotly_chart(fig_humi, use_container_width=True)
else:
    st.info("온습도 데이터가 없습니다.")

st.divider()


# ============================================================
# 2. 독립된 조도(CDS) 집계 및 그래프 섹션
# ============================================================

st.header("2. 💡 조도(CDS) 모니터링")

if not df_cds_view.empty:
    latest_cds_row = df_cds.iloc[-1]
    latest_cds = latest_cds_row["cds_value"]
    
    if len(df_cds) >= 2:
        prev_cds = df_cds.iloc[-2]["cds_value"]
        cds_delta = latest_cds - prev_cds
    else:
        cds_delta = 0

    # 조도 KPI (변수 충돌 문제 수정)
    cds_col1, cds_col2, cds_col3 = st.columns(3)
    cds_col1.metric("현재 조도", f"{latest_cds:,} ADC", f"{cds_delta:+} ADC")
    cds_col2.metric("조도 데이터 수집 건수", f"{len(df_cds):,} 건")
    cds_col3.metric("최근 측정 시간", latest_cds_row["created_at"].strftime("%H:%M:%S"))

    # 조도 전용 통계
    st.markdown("#### 조도 요약 통계")
    cds_std = df_cds_view["cds_value"].std()
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("평균 조도", f"{df_cds_view['cds_value'].mean():.1f} ADC")
    m_col2.metric("최고 조도", f"{df_cds_view['cds_value'].max():,} ADC")
    m_col3.metric("최저 조도", f"{df_cds_view['cds_value'].min():,} ADC")
    m_col4.metric("표준 편차", f"{cds_std:.2f}" if pd.notnull(cds_std) else "0.00")

    # 조도 그래프 (변화 추이 및 분포)
    cg_col1, cg_col2 = st.columns([2, 1])

    with cg_col1:
        fig_cds_line = px.line(
            df_cds_view,
            x="created_at",
            y="cds_value",
            markers=True,
            title="조도 변화 추이",
            labels={"created_at": "시간", "cds_value": "조도 (ADC)"},
            color_discrete_sequence=["#FF8C00"]
        )
        st.plotly_chart(fig_cds_line, use_container_width=True)

    with cg_col2:
        fig_cds_hist = px.histogram(
            df_cds_view,
            x="cds_value",
            nbins=15,
            title="조도 데이터 분포",
            labels={"cds_value": "조도 (ADC)"},
            color_discrete_sequence=["#FFA500"]
        )
        st.plotly_chart(fig_cds_hist, use_container_width=True)

    # 조도 독립 상세 테이블 & 다운로드
    with st.expander("📋 조도 데이터 상세보기 및 다운로드"):
        cds_display = df_cds_view.sort_values("created_at", ascending=False)
        st.dataframe(cds_display, use_container_width=True, hide_index=True)
        
        csv_cds = cds_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="조도 데이터 CSV 다운로드",
            data=csv_cds,
            file_name="cds_sensor_data.csv",
            mime="text/csv",
        )
else:
    st.info("수집된 조도 데이터가 없습니다.")