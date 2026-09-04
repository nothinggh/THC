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
st.caption("Arduino Sensor Monitoring (DHT11, CDS, Sound, Distance)")


# ============================================================
# SQLite 데이터 읽기
# ============================================================

def load_sensor_data():
    """온도 및 습도 데이터 로드"""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT id, temperature, humidity, created_at FROM sensor_data ORDER BY created_at"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def load_cds_data():
    """조도(CDS) 데이터 로드"""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT id, timestamp AS created_at, cds_value FROM cds_log ORDER BY timestamp"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def load_sound_data():
    """소리 센서(Sound) 데이터 로드"""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT id, timestamp AS created_at, sound_value, deviation FROM sound_log ORDER BY timestamp"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def load_distance_data():
    """초음파 거리 센서(Distance) 데이터 로드"""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT id, timestamp AS created_at, duration_us, distance_cm FROM distance_logs ORDER BY timestamp"
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
df_sound = load_sound_data()
df_distance = load_distance_data()

if df_sensor.empty and df_cds.empty and df_sound.empty and df_distance.empty:
    st.warning("수집된 데이터가 없습니다.")
    st.stop()


# ============================================================
# 사이드바
# ============================================================

st.sidebar.header("Dashboard 설정")

max_rows = max(len(df_sensor), len(df_cds), len(df_sound), len(df_distance), 1)
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
df_sound_view = df_sound.tail(data_count) if not df_sound.empty else df_sound
df_distance_view = df_distance.tail(data_count) if not df_distance.empty else df_distance


# ============================================================
# 1. 온·습도 섹션
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재 온도", f"{latest_temp:.1f} °C", f"{temp_delta:+.1f} °C")
    col2.metric("현재 습도", f"{latest_humi:.1f} %", f"{humi_delta:+.1f} %")
    col3.metric("데이터 건수", f"{len(df_sensor):,} 건")
    col4.metric("최근 측정 시간", latest_s["created_at"].strftime("%H:%M:%S"))

    st.markdown("#### 온·습도 요약 통계")
    st_col1, st_col2, st_col3, st_col4 = st.columns(4)
    st_col1.metric("평균 온도", f"{df_sensor_view['temperature'].mean():.1f} °C")
    st_col2.metric("최고 / 최저 온도", f"{df_sensor_view['temperature'].max():.1f} / {df_sensor_view['temperature'].min():.1f} °C")
    st_col3.metric("평균 습도", f"{df_sensor_view['humidity'].mean():.1f} %")
    st_col4.metric("최고 / 최저 습도", f"{df_sensor_view['humidity'].max():.1f} / {df_sensor_view['humidity'].min():.1f} %")

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
# 2. 조도(CDS) 섹션
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

    cds_col1, cds_col2, cds_col3 = st.columns(3)
    cds_col1.metric("현재 조도", f"{latest_cds:,} ADC", f"{cds_delta:+} ADC")
    cds_col2.metric("데이터 건수", f"{len(df_cds):,} 건")
    cds_col3.metric("최근 측정 시간", latest_cds_row["created_at"].strftime("%H:%M:%S"))

    st.markdown("#### 조도 요약 통계")
    cds_std = df_cds_view["cds_value"].std()
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("평균 조도", f"{df_cds_view['cds_value'].mean():.1f} ADC")
    m_col2.metric("최고 조도", f"{df_cds_view['cds_value'].max():,} ADC")
    m_col3.metric("최저 조도", f"{df_cds_view['cds_value'].min():,} ADC")
    m_col4.metric("표준 편차", f"{cds_std:.2f}" if pd.notnull(cds_std) else "0.00")

    cg_col1, cg_col2 = st.columns([2, 1])
    with cg_col1:
        fig_cds_line = px.line(
            df_cds_view, x="created_at", y="cds_value", markers=True,
            title="조도 변화 추이", labels={"created_at": "시간", "cds_value": "조도 (ADC)"},
            color_discrete_sequence=["#FF8C00"]
        )
        st.plotly_chart(fig_cds_line, use_container_width=True)

    with cg_col2:
        fig_cds_hist = px.histogram(
            df_cds_view, x="cds_value", nbins=15, title="조도 데이터 분포",
            labels={"cds_value": "조도 (ADC)"}, color_discrete_sequence=["#FFA500"]
        )
        st.plotly_chart(fig_cds_hist, use_container_width=True)

    with st.expander("📋 조도 데이터 상세보기 및 다운로드"):
        cds_display = df_cds_view.sort_values("created_at", ascending=False)
        st.dataframe(cds_display, use_container_width=True, hide_index=True)
        csv_cds = cds_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button("조도 CSV 다운로드", data=csv_cds, file_name="cds_sensor_data.csv", mime="text/csv")
else:
    st.info("수집된 조도 데이터가 없습니다.")

st.divider()


# ============================================================
# 3. 소리(Sound) 모니터링 섹션 (새로 추가)
# ============================================================

st.header("3. 🔊 소리(Sound) 모니터링")

if not df_sound_view.empty:
    latest_sound_row = df_sound.iloc[-1]
    latest_sound = latest_sound_row["sound_value"]
    latest_dev = latest_sound_row["deviation"]

    if len(df_sound) >= 2:
        prev_sound = df_sound.iloc[-2]["sound_value"]
        sound_delta = latest_sound - prev_sound
    else:
        sound_delta = 0

    snd_col1, snd_col2, snd_col3, snd_col4 = st.columns(4)
    snd_col1.metric("현재 소리 크기", f"{latest_sound:,}", f"{sound_delta:+}")
    snd_col2.metric("현재 편차(Deviation)", f"{latest_dev:,}")
    snd_col3.metric("데이터 건수", f"{len(df_sound):,} 건")
    snd_col4.metric("최근 측정 시간", latest_sound_row["created_at"].strftime("%H:%M:%S"))

    st.markdown("#### 소리 요약 통계")
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    s_col1.metric("평균 소리 크기", f"{df_sound_view['sound_value'].mean():.1f}")
    s_col2.metric("최대 편차", f"{df_sound_view['deviation'].max():,}")
    s_col3.metric("최고 소리 크기", f"{df_sound_view['sound_value'].max():,}")
    s_col4.metric("최저 소리 크기", f"{df_sound_view['sound_value'].min():,}")

    sg_col1, sg_col2 = st.columns(2)
    with sg_col1:
        fig_sound = px.line(
            df_sound_view, x="created_at", y="sound_value", markers=True,
            title="소리 크기 변화 추이", labels={"created_at": "시간", "sound_value": "소리 크기"},
            color_discrete_sequence=["#9370DB"]
        )
        st.plotly_chart(fig_sound, use_container_width=True)

    with sg_col2:
        fig_dev = px.line(
            df_sound_view, x="created_at", y="deviation", markers=True,
            title="소리 편차 추이", labels={"created_at": "시간", "deviation": "편차"},
            color_discrete_sequence=["#BA55D3"]
        )
        st.plotly_chart(fig_dev, use_container_width=True)

    with st.expander("📋 소리 데이터 상세보기 및 다운로드"):
        sound_display = df_sound_view.sort_values("created_at", ascending=False)
        st.dataframe(sound_display, use_container_width=True, hide_index=True)
        csv_sound = sound_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button("소리 CSV 다운로드", data=csv_sound, file_name="sound_sensor_data.csv", mime="text/csv")
else:
    st.info("수집된 소리 데이터가 없습니다.")

st.divider()


# ============================================================
# 4. 거리(Distance) 모니터링 섹션 (새로 추가)
# ============================================================

st.header("4. 📏 초음파 거리(Distance) 모니터링")

if not df_distance_view.empty:
    latest_dist_row = df_distance.iloc[-1]
    latest_dist = latest_dist_row["distance_cm"]
    latest_dur = latest_dist_row["duration_us"]

    if len(df_distance) >= 2:
        prev_dist = df_distance.iloc[-2]["distance_cm"]
        dist_delta = latest_dist - prev_dist
    else:
        dist_delta = 0

    dist_col1, dist_col2, dist_col3, dist_col4 = st.columns(4)
    dist_col1.metric("현재 거리", f"{latest_dist:.1f} cm", f"{dist_delta:+.1f} cm")
    dist_col2.metric("신호 시간(Duration)", f"{latest_dur:.1f} µs")
    dist_col3.metric("데이터 건수", f"{len(df_distance):,} 건")
    dist_col4.metric("최근 측정 시간", latest_dist_row["created_at"].strftime("%H:%M:%S"))

    st.markdown("#### 거리 요약 통계")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    d_col1.metric("평균 거리", f"{df_distance_view['distance_cm'].mean():.1f} cm")
    d_col2.metric("최장 거리", f"{df_distance_view['distance_cm'].max():.1f} cm")
    d_col3.metric("최단 거리", f"{df_distance_view['distance_cm'].min():.1f} cm")
    d_col4.metric("평균 신호 시간", f"{df_distance_view['duration_us'].mean():.1f} µs")

    dg_col1, dg_col2 = st.columns(2)
    with dg_col1:
        fig_dist = px.line(
            df_distance_view, x="created_at", y="distance_cm", markers=True,
            title="거리 변화 추이", labels={"created_at": "시간", "distance_cm": "거리 (cm)"},
            color_discrete_sequence=["#00FA9A"]
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with dg_col2:
        fig_dur = px.line(
            df_distance_view, x="created_at", y="duration_us", markers=True,
            title="초음파 반사 시간 추이", labels={"created_at": "시간", "duration_us": "시간 (µs)"},
            color_discrete_sequence=["#20B2AA"]
        )
        st.plotly_chart(fig_dur, use_container_width=True)

    with st.expander("📋 거리 데이터 상세보기 및 다운로드"):
        dist_display = df_distance_view.sort_values("created_at", ascending=False)
        st.dataframe(dist_display, use_container_width=True, hide_index=True)
        csv_dist = dist_display.to_csv(index=False).encode("utf-8-sig")
        st.download_button("거리 CSV 다운로드", data=csv_dist, file_name="distance_sensor_data.csv", mime="text/csv")
else:
    st.info("수집된 거리 데이터가 없습니다.")