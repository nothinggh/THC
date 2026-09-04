import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# 기본 설정 및 모던 고시인성 Custom CSS
# ============================================================

DB_FILE = r"C:\Users\user\work\middleware\THC\sensor_data.db"

st.set_page_config(
    page_title="Environmental Sensor Dashboard",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모던하고 선명한 대시보드 커스텀 스타일
st.markdown("""
    <style>
    /* 메인 배경 및 레이아웃 정의 */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 카드 컴포넌트 스타일 (KPI) */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(0, 229, 255, 0.4);
        transform: translateY(-2px);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.2;
    }
    .metric-delta {
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .delta-plus { color: #00E676; }
    .delta-minus { color: #FF5252; }
    .metric-sub {
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* 탭 디자인 커스텀 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00E5FF !important;
        color: #0E1117 !important;
        border-color: #00E5FF !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 헤더 영역
st.title("🌡️ Environmental Sensor Dashboard")
st.caption("Arduino Sensor Real-time Monitoring • DHT11 • CDS • Sound • Distance")


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
# Plotly 고대비/모던 레이아웃 헬퍼
# ============================================================

def apply_high_contrast_layout(fig, title_text, height=300):
    """다크 모드 최적화 투명 배경 및 고대비 트랙 레이아웃"""
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b>",
            font=dict(size=15, color="#F8FAFC"),
            x=0, y=0.95
        ),
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.07)",
            zerolinecolor="rgba(255, 255, 255, 0.15)",
            tickfont=dict(color="#94A3B8")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.07)",
            zerolinecolor="rgba(255, 255, 255, 0.15)",
            tickfont=dict(color="#94A3B8")
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#CBD5E1"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
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
# TAB 1: 종합 한눈에 보기 (커스텀 KPI + 시인성 강조 트랙)
# ------------------------------------------------------------
with tab_summary:
    st.markdown("### ⚡ 실시간 센서 현황")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    # 1. 온습도 KPI
    with kpi_col1:
        if not df_sensor.empty:
            curr_temp = df_sensor.iloc[-1]["temperature"]
            curr_humi = df_sensor.iloc[-1]["humidity"]
            p_temp = df_sensor.iloc[-2]["temperature"] if len(df_sensor) > 1 else curr_temp
            diff = curr_temp - p_temp
            delta_class = "delta-plus" if diff >= 0 else "delta-minus"
            delta_sign = "+" if diff >= 0 else ""
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🌡️ 온·습도</div>
                    <div class="metric-value">{curr_temp:.1f} <span style="font-size: 1.1rem;">°C</span></div>
                    <div class="metric-delta {delta_class}">{delta_sign}{diff:.1f} °C (전회 대비)</div>
                    <div class="metric-sub">💧 현재 습도: <b>{curr_humi:.1f}%</b></div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("온습도 데이터 없음")

    # 2. 조도 KPI
    with kpi_col2:
        if not df_cds.empty:
            curr_cds = df_cds.iloc[-1]["cds_value"]
            p_cds = df_cds.iloc[-2]["cds_value"] if len(df_cds) > 1 else curr_cds
            diff = curr_cds - p_cds
            delta_class = "delta-plus" if diff >= 0 else "delta-minus"
            delta_sign = "+" if diff >= 0 else ""
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">💡 조도 (CDS)</div>
                    <div class="metric-value">{curr_cds:,} <span style="font-size: 1.1rem;">ADC</span></div>
                    <div class="metric-delta {delta_class}">{delta_sign}{diff} ADC</div>
                    <div class="metric-sub">📊 구간 평균: <b>{df_cds_v['cds_value'].mean():.1f}</b></div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("조도 데이터 없음")

    # 3. 소리 KPI
    with kpi_col3:
        if not df_sound.empty:
            curr_snd = df_sound.iloc[-1]["sound_value"]
            curr_dev = df_sound.iloc[-1]["deviation"]
            p_snd = df_sound.iloc[-2]["sound_value"] if len(df_sound) > 1 else curr_snd
            diff = curr_snd - p_snd
            delta_class = "delta-plus" if diff >= 0 else "delta-minus"
            delta_sign = "+" if diff >= 0 else ""
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🔊 소리 레벨</div>
                    <div class="metric-value">{curr_snd:,}</div>
                    <div class="metric-delta {delta_class}">{delta_sign}{diff}</div>
                    <div class="metric-sub">⚡ 편차(Deviation): <b>{curr_dev:,}</b></div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("소리 데이터 없음")

    # 4. 거리 KPI
    with kpi_col4:
        if not df_distance.empty:
            curr_dist = df_distance.iloc[-1]["distance_cm"]
            p_dist = df_distance.iloc[-2]["distance_cm"] if len(df_distance) > 1 else curr_dist
            diff = curr_dist - p_dist
            delta_class = "delta-plus" if diff >= 0 else "delta-minus"
            delta_sign = "+" if diff >= 0 else ""
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📏 초음파 감지 거리</div>
                    <div class="metric-value">{curr_dist:.1f} <span style="font-size: 1.1rem;">cm</span></div>
                    <div class="metric-delta {delta_class}">{delta_sign}{diff:.1f} cm</div>
                    <div class="metric-sub">🔍 최단 거리: <b>{df_distance_v['distance_cm'].min():.1f} cm</b></div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("거리 데이터 없음")

    st.write("")
    st.markdown("### 📈 실시간 시계열 추이 비교")
    
    # 2x2 고시인성 차트 그리드
    grid_col1, grid_col2 = st.columns(2)

    with grid_col1:
        if not df_sensor_v.empty:
            fig_temp = px.line(
                df_sensor_v, x="created_at", y=["temperature", "humidity"],
                labels={"created_at": "시간", "value": "측정값", "variable": "지표"},
                color_discrete_sequence=["#FF5252", "#00E5FF"]
            )
            fig_temp.update_traces(line=dict(width=2.5))
            fig_temp = apply_high_contrast_layout(fig_temp, "1. 온·습도 추이 (°C / %)")
            st.plotly_chart(fig_temp, use_container_width=True)

        if not df_sound_v.empty:
            fig_snd = go.Figure()
            fig_snd.add_trace(go.Scatter(
                x=df_sound_v["created_at"], y=df_sound_v["sound_value"],
                mode="lines", fill="tozeroy",
                fillcolor="rgba(213, 0, 249, 0.15)",
                line=dict(color="#D500F9", width=2),
                name="소리 크기"
            ))
            fig_snd = apply_high_contrast_layout(fig_snd, "3. 소리 감지 레벨 추이")
            st.plotly_chart(fig_snd, use_container_width=True)

    with grid_col2:
        if not df_cds_v.empty:
            fig_cds = go.Figure()
            fig_cds.add_trace(go.Scatter(
                x=df_cds_v["created_at"], y=df_cds_v["cds_value"],
                mode="lines", fill="tozeroy",
                fillcolor="rgba(255, 171, 0, 0.15)",
                line=dict(color="#FFAB00", width=2),
                name="조도 (ADC)"
            ))
            fig_cds = apply_high_contrast_layout(fig_cds, "2. 조도(CDS) 변화 추이")
            st.plotly_chart(fig_cds, use_container_width=True)

        if not df_distance_v.empty:
            fig_dist = px.line(
                df_distance_v, x="created_at", y="distance_cm",
                labels={"created_at": "시간", "distance_cm": "거리 (cm)"},
                color_discrete_sequence=["#00E676"]
            )
            fig_dist.update_traces(line=dict(width=2.5))
            fig_dist = apply_high_contrast_layout(fig_dist, "4. 초음파 감지 거리 추이 (cm)")
            st.plotly_chart(fig_dist, use_container_width=True)


# ------------------------------------------------------------
# TAB 2: 센서별 상세 분석
# ------------------------------------------------------------
with tab_detail:
    st.markdown("### 🔍 센서 데이터 상세 분석")
    
    sec1, sec2 = st.columns(2)
    with sec1:
        st.markdown("##### 🌡️ 온·습도 분포")
        if not df_sensor_v.empty:
            st.caption(f"평균 온도: `{df_sensor_v['temperature'].mean():.1f} °C` | 평균 습도: `{df_sensor_v['humidity'].mean():.1f} %`")
            fig = px.histogram(df_sensor_v, x="temperature", nbins=15, color_discrete_sequence=["#FF5252"])
            fig = apply_high_contrast_layout(fig, "온도 분포 히스토그램", height=240)
            st.plotly_chart(fig, use_container_width=True)

    with sec2:
        st.markdown("##### 💡 조도(CDS) 분포")
        if not df_cds_v.empty:
            st.caption(f"최대 조도: `{df_cds_v['cds_value'].max():,} ADC` | 최저 조도: `{df_cds_v['cds_value'].min():,} ADC`")
            fig = px.histogram(df_cds_v, x="cds_value", nbins=15, color_discrete_sequence=["#FFAB00"])
            fig = apply_high_contrast_layout(fig, "조도 분포 히스토그램", height=240)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    sec3, sec4 = st.columns(2)
    with sec3:
        st.markdown("##### 🔊 소리 편차 추이")
        if not df_sound_v.empty:
            fig = px.line(df_sound_v, x="created_at", y="deviation", color_discrete_sequence=["#AA00FF"])
            fig = apply_high_contrast_layout(fig, "소리 편차(Deviation) 변동", height=240)
            st.plotly_chart(fig, use_container_width=True)

    with sec4:
        st.markdown("##### 📏 신호 반사 시간")
        if not df_distance_v.empty:
            fig = px.line(df_distance_v, x="created_at", y="duration_us", color_discrete_sequence=["#1DE9B6"])
            fig = apply_high_contrast_layout(fig, "신호 반사 시간(duration_us)", height=240)
            st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# TAB 3: 원본 데이터 및 다운로드
# ------------------------------------------------------------
with tab_data:
    st.markdown("### 📋 센서 데이터셋")
    
    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["온습도", "조도", "소리", "거리"])
    
    with d_tab1:
        st.dataframe(df_sensor_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("📥 온습도 CSV 다운로드", data=df_sensor_v.to_csv(index=False).encode("utf-8-sig"), file_name="sensor_data.csv")
        
    with d_tab2:
        st.dataframe(df_cds_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("📥 조도 CSV 다운로드", data=df_cds_v.to_csv(index=False).encode("utf-8-sig"), file_name="cds_data.csv")

    with d_tab3:
        st.dataframe(df_sound_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("📥 소리 CSV 다운로드", data=df_sound_v.to_csv(index=False).encode("utf-8-sig"), file_name="sound_data.csv")

    with d_tab4:
        st.dataframe(df_distance_v.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("📥 거리 CSV 다운로드", data=df_distance_v.to_csv(index=False).encode("utf-8-sig"), file_name="distance_data.csv")