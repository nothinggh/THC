import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# 기본 설정 및 고시인성 Custom CSS
# ============================================================

DB_FILE = r"C:\Users\user\work\middleware\THC\sensor_data.db"

st.set_page_config(
    page_title="Environmental Sensor Dashboard",
    page_icon="🌡️",
    layout="wide",
)

# 화이트/블랙 배경 모두에서 잘 보이는 Universal Contrast CSS
st.markdown("""
    <style>
    /* Metric 카드 스타일링: 반투명 배경 + 명확한 테두리 */
    div[data-testid="stMetric"] {
        background-color: rgba(127, 127, 127, 0.08) !important;
        border: 1px solid rgba(127, 127, 127, 0.3) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Metric 라벨 & 값 글자 강제 강조 */
    div[data-testid="stMetricLabel"] {
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
    }
    
    /* 탭 메뉴 시인성 강화 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌡️ Environmental Sensor Dashboard")
st.caption("Arduino Sensor Monitoring (DHT11, CDS, Sound, Distance)")


# ============================================================
# SQLite 데이터 읽기
# ============================================================

@st.cache_data(ttl=2)
def load_all_sensor_data():
    conn = sqlite3.connect(DB_FILE)
    
    # 1. 온습도
    df_sensor = pd.read_sql_query("SELECT id, temperature, humidity, created_at FROM sensor_data ORDER BY created_at", conn)
    if not df_sensor.empty:
        df_sensor["created_at"] = pd.to_datetime(df_sensor["created_at"])
        
    # 2. 조도(CDS)
    df_cds = pd.read_sql_query("SELECT id, timestamp AS created_at, cds_value FROM cds_log ORDER BY timestamp", conn)
    if not df_cds.empty:
        df_cds["created_at"] = pd.to_datetime(df_cds["created_at"])
        
    # 3. 소리
    df_sound = pd.read_sql_query("SELECT id, timestamp AS created_at, sound_value, deviation FROM sound_log ORDER BY timestamp", conn)
    if not df_sound.empty:
        df_sound["created_at"] = pd.to_datetime(df_sound["created_at"])
        
    # 4. 거리
    df_distance = pd.read_sql_query("SELECT id, timestamp AS created_at, duration_us, distance_cm FROM distance_logs ORDER BY timestamp", conn)
    if not df_distance.empty:
        df_distance["created_at"] = pd.to_datetime(df_distance["created_at"])
        
    conn.close()
    return df_sensor, df_cds, df_sound, df_distance


# 데이터 로드
df_sensor, df_cds, df_sound, df_distance = load_all_sensor_data()

if df_sensor.empty and df_cds.empty and df_sound.empty and df_distance.empty:
    st.warning("수집된 데이터가 없습니다. DB 연결을 확인해주세요.")
    st.stop()


# ============================================================
# Plotly 공통 고시인성 레이아웃 헬퍼
# ============================================================

def apply_high_contrast_layout(fig, title_text, height=290):
    """라이트/다크 모드 공통 투명 및 고대비 스타일 적용"""
    fig.update_layout(
        title=dict(text=f"<b>{title_text}</b>", font=dict(size=14)),
        height=height,
        margin=dict(l=25, r=20, t=40, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(127, 127, 127, 0.2)",
            zerolinecolor="rgba(127, 127, 127, 0.3)"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(127, 127, 127, 0.2)",
            zerolinecolor="rgba(127, 127, 127, 0.3)"
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig


# ============================================================
# 사이드바 설정
# ============================================================

st.sidebar.header("⚙️ 대시보드 설정")

max_rows = max(len(df_sensor), len(df_cds), len(df_sound), len(df_distance), 1)
min_limit = min(10, max_rows)
max_limit = max(10, min(1000, max_rows))

data_count = st.sidebar.slider(
    "표시할 최근 데이터 개수",
    min_value=min_limit,
    max_value=max_limit,
    value=min(100, max_rows)
)

if st.sidebar.button("🔄 데이터 즉시 새로고침", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# View 데이터프레임
df_sensor_v = df_sensor.tail(data_count) if not df_sensor.empty else df_sensor
df_cds_v = df_cds.tail(data_count) if not df_cds.empty else df_cds
df_sound_v = df_sound.tail(data_count) if not df_sound.empty else df_sound
df_distance_v = df_distance.tail(data_count) if not df_distance.empty else df_distance


# ============================================================
# 메인 대시보드 탭 구성
# ============================================================

tab_summary, tab_detail, tab_data = st.tabs(["📊 종합 한눈에 보기", "🔍 센서별 상세 분석", "📋 원본 데이터 및 다운로드"])


# ------------------------------------------------------------
# TAB 1: 종합 한눈에 보기 (High Visibility 2x2 Dashboard)
# ------------------------------------------------------------
with tab_summary:
    st.subheader("⚡ 실시간 주요 센서 현황")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    # 1. 온습도 KPI
    with kpi_col1:
        if not df_sensor.empty:
            curr_temp = df_sensor.iloc[-1]["temperature"]
            curr_humi = df_sensor.iloc[-1]["humidity"]
            p_temp = df_sensor.iloc[-2]["temperature"] if len(df_sensor) > 1 else curr_temp
            st.metric("🌡️ 현재 온도", f"{curr_temp:.1f} °C", f"{curr_temp - p_temp:+.1f} °C")
            st.caption(f"💧 습도: **{curr_humi:.1f}%**")
        else:
            st.metric("🌡️ 온습도", "N/A")
            
    # 2. 조도 KPI
    with kpi_col2:
        if not df_cds.empty:
            curr_cds = df_cds.iloc[-1]["cds_value"]
            p_cds = df_cds.iloc[-2]["cds_value"] if len(df_cds) > 1 else curr_cds
            st.metric("💡 현재 조도", f"{curr_cds:,} ADC", f"{curr_cds - p_cds:+} ADC")
            st.caption(f"평균: **{df_cds_v['cds_value'].mean():.1f} ADC**")
        else:
            st.metric("💡 조도", "N/A")

    # 3. 소리 KPI
    with kpi_col3:
        if not df_sound.empty:
            curr_snd = df_sound.iloc[-1]["sound_value"]
            curr_dev = df_sound.iloc[-1]["deviation"]
            p_snd = df_sound.iloc[-2]["sound_value"] if len(df_sound) > 1 else curr_snd
            st.metric("🔊 소리 크기", f"{curr_snd:,}", f"{curr_snd - p_snd:+}")
            st.caption(f"편차(Deviation): **{curr_dev:,}**")
        else:
            st.metric("🔊 소리", "N/A")

    # 4. 거리 KPI
    with kpi_col4:
        if not df_distance.empty:
            curr_dist = df_distance.iloc[-1]["distance_cm"]
            p_dist = df_distance.iloc[-2]["distance_cm"] if len(df_distance) > 1 else curr_dist
            st.metric("📏 감지 거리", f"{curr_dist:.1f} cm", f"{curr_dist - p_dist:+.1f} cm")
            st.caption(f"최단 거리: **{df_distance_v['distance_cm'].min():.1f} cm**")
        else:
            st.metric("📏 거리", "N/A")

    st.divider()

    # 2x2 고시인성 대시보드 차트 배치
    st.subheader("📈 센서별 실시간 추이 비교")
    grid_col1, grid_col2 = st.columns(2)

    with grid_col1:
        if not df_sensor_v.empty:
            fig_temp = px.line(
                df_sensor_v, x="created_at", y=["temperature", "humidity"],
                labels={"created_at": "시간", "value": "측정값", "variable": "항목"},
                color_discrete_sequence=["#FF5252", "#00E5FF"]  # Coral Red, Bright Cyan
            )
            fig_temp = apply_high_contrast_layout(fig_temp, "1. 온·습도 추이 (°C / %)")
            st.plotly_chart(fig_temp, use_container_width=True)

        if not df_sound_v.empty:
            fig_snd = px.line(
                df_sound_v, x="created_at", y="sound_value",
                labels={"created_at": "시간", "sound_value": "소리 크기"},
                color_discrete_sequence=["#D500F9"]  # Neon Purple
            )
            fig_snd = apply_high_contrast_layout(fig_snd, "3. 소리 크기 추이")
            st.plotly_chart(fig_snd, use_container_width=True)

    with grid_col2:
        if not df_cds_v.empty:
            fig_cds = px.line(
                df_cds_v, x="created_at", y="cds_value",
                labels={"created_at": "시간", "cds_value": "조도 (ADC)"},
                color_discrete_sequence=["#FFAB00"]  # Amber Yellow
            )
            fig_cds = apply_high_contrast_layout(fig_cds, "2. 조도 추이 (ADC)")
            st.plotly_chart(fig_cds, use_container_width=True)

        if not df_distance_v.empty:
            fig_dist = px.line(
                df_distance_v, x="created_at", y="distance_cm",
                labels={"created_at": "시간", "distance_cm": "거리 (cm)"},
                color_discrete_sequence=["#00E676"]  # Bright Mint
            )
            fig_dist = apply_high_contrast_layout(fig_dist, "4. 초음파 감지 거리 추이 (cm)")
            st.plotly_chart(fig_dist, use_container_width=True)


# ------------------------------------------------------------
# TAB 2: 센서별 상세 분석
# ------------------------------------------------------------
with tab_detail:
    st.subheader("🔍 센서별 상세 지표 및 분포")
    
    sec1, sec2 = st.columns(2)
    with sec1:
        st.markdown("### 🌡️ 온·습도 상세")
        if not df_sensor_v.empty:
            st.write(f"**평균 온도:** `{df_sensor_v['temperature'].mean():.1f} °C` | **평균 습도:** `{df_sensor_v['humidity'].mean():.1f} %`")
            fig = px.histogram(df_sensor_v, x="temperature", nbins=15, color_discrete_sequence=["#FF5252"])
            fig = apply_high_contrast_layout(fig, "온도 분포 히스토그램", height=240)
            st.plotly_chart(fig, use_container_width=True)

    with sec2:
        st.markdown("### 💡 조도 상세")
        if not df_cds_v.empty:
            st.write(f"**최대 조도:** `{df_cds_v['cds_value'].max():,} ADC` | **최저 조도:** `{df_cds_v['cds_value'].min():,} ADC`")
            fig = px.histogram(df_cds_v, x="cds_value", nbins=15, color_discrete_sequence=["#FFAB00"])
            fig = apply_high_contrast_layout(fig, "조도 분포 히스토그램", height=240)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    sec3, sec4 = st.columns(2)
    with sec3:
        st.markdown("### 🔊 소리 편차 상세")
        if not df_sound_v.empty:
            fig = px.line(df_sound_v, x="created_at", y="deviation", color_discrete_sequence=["#AA00FF"])
            fig = apply_high_contrast_layout(fig, "소리 편차(Deviation) 추이", height=240)
            st.plotly_chart(fig, use_container_width=True)

    with sec4:
        st.markdown("### 📏 초음파 신호 시간 상세")
        if not df_distance_v.empty:
            fig = px.line(df_distance_v, x="created_at", y="duration_us", color_discrete_sequence=["#1DE9B6"])
            fig = apply_high_contrast_layout(fig, "신호 반사 시간(duration_us) 추이", height=240)
            st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# TAB 3: 원본 데이터 및 다운로드
# ------------------------------------------------------------
with tab_data:
    st.subheader("📋 수집 데이터 통합 조회 및 다운로드")
    
    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["온습도", "조도", "소리", "거리"])
    
    with d_tab1:
        st.dataframe(df_sensor_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("온습도 CSV 다운로드", data=df_sensor_v.to_csv(index=False).encode("utf-8-sig"), file_name="sensor_data.csv")
        
    with d_tab2:
        st.dataframe(df_cds_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("조도 CSV 다운로드", data=df_cds_v.to_csv(index=False).encode("utf-8-sig"), file_name="cds_data.csv")

    with d_tab3:
        st.dataframe(df_sound_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("소리 CSV 다운로드", data=df_sound_v.to_csv(index=False).encode("utf-8-sig"), file_name="sound_data.csv")

    with d_tab4:
        st.dataframe(df_distance_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("거리 CSV 다운로드", data=df_distance_v.to_csv(index=False).encode("utf-8-sig"), file_name="distance_data.csv")