import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# 기본 설정
# ============================================================

DB_FILE = r"C:\Users\user\work\middleware\THC\sensor_data.db"

st.set_page_config(
    page_title="온습도 모니터링 대시보드",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ Temperature & Humidity Dashboard")
st.caption("Arduino DHT11 Sensor Real-time Monitoring")


# ============================================================
# SQLite 데이터 읽기
# ============================================================

@st.cache_data(ttl=5)  # 5초 간격 데이터 캐싱
def load_data():
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT 
            id, 
            temperature, 
            humidity, 
            created_at 
        FROM sensor_data
        ORDER BY created_at
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["created_at"] = pd.to_datetime(df["created_at"])
    return df


df = load_data()

if df.empty:
    st.warning("수집된 센서 데이터가 없습니다.")
    st.stop()


# ============================================================
# 공통 그래프 레이아웃 설정 (다크/라이트 모드 자동 대응)
# ============================================================

def apply_chart_style(fig):
    """라이트/다크 모드에 모두 잘 보이는 시인성 높은 스타일 적용"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    # 그리드선 가독성 제어
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128, 128, 128, 0.2)")
    return fig


# ============================================================
# 사이드바
# ============================================================

st.sidebar.header("⚙️ 대시보드 설정")

total_rows = len(df)
min_limit = min(10, total_rows)
max_limit = max(10, min(500, total_rows))

if min_limit == max_limit:
    data_count = total_rows
    st.sidebar.info(f"현재 총 {total_rows}개의 데이터가 표시됩니다.")
else:
    data_count = st.sidebar.slider(
        "표시할 데이터 개수",
        min_value=min_limit,
        max_value=max_limit,
        value=min(100, total_rows),
    )

df_view = df.tail(data_count)


# ============================================================
# 최신 데이터 계산
# ============================================================

latest = df.iloc[-1]
latest_temp = latest["temperature"]
latest_humi = latest["humidity"]
latest_time = latest["created_at"]

if len(df) >= 2:
    previous = df.iloc[-2]
    temp_delta = latest_temp - previous["temperature"]
    humi_delta = latest_humi - previous["humidity"]
else:
    temp_delta = 0.0
    humi_delta = 0.0


# ============================================================
# 현재 상태 KPI (카드 스타일 시각화)
# ============================================================

st.subheader("📍 실시간 센서 상태")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        label="현재 온도",
        value=f"{latest_temp:.1f} °C",
        delta=f"{temp_delta:+.1f} °C",
    )

with m2:
    st.metric(
        label="현재 습도",
        value=f"{latest_humi:.1f} %",
        delta=f"{humi_delta:+.1f} %",
    )

with m3:
    st.metric(
        label="총 누적 데이터",
        value=f"{len(df):,} 건",
    )

with m4:
    st.metric(
        label="최근 측정 시간",
        value=latest_time.strftime("%H:%M:%S"),
    )

st.space(10)


# ============================================================
# 데이터 시각화 (탭 구성으로 시인성 개선)
# ============================================================

tab1, tab2, tab3 = st.tabs(["📈 시계열 트렌드", "📊 통계 및 분포", "📋 상세 데이터"])

# ------------------------------------------------------------
# TAB 1: 시계열 트렌드
# ------------------------------------------------------------
with tab1:
    col_t1, col_t2 = st.columns(2)

    # 고대비 컬러 적용 (온도: Coral Red, 습도: Deep Sky Blue)
    with col_t1:
        fig_temp = px.line(
            df_view,
            x="created_at",
            y="temperature",
            markers=True,
            title="<b>온도 변화 추이</b>",
            color_discrete_sequence=["#FF5733"],
            labels={"created_at": "시간", "temperature": "온도 (°C)"},
        )
        st.plotly_chart(apply_chart_style(fig_temp), use_container_width=True)

    with col_t2:
        fig_humi = px.line(
            df_view,
            x="created_at",
            y="humidity",
            markers=True,
            title="<b>습도 변화 추이</b>",
            color_discrete_sequence=["#00A8E8"],
            labels={"created_at": "시간", "humidity": "습도 (%)"},
        )
        st.plotly_chart(apply_chart_style(fig_humi), use_container_width=True)

    # 복합 그래프 (Plotly 이중 라인으로 명확한 대비 제공)
    st.markdown("#### **온도 및 습도 교차 비교**")
    fig_combined = px.line(
        df_view,
        x="created_at",
        y=["temperature", "humidity"],
        markers=False,
        color_discrete_map={"temperature": "#FF5733", "humidity": "#00A8E8"},
        labels={"created_at": "시간", "value": "측정값", "variable": "구분"},
    )
    st.plotly_chart(apply_chart_style(fig_combined), use_container_width=True)


# ------------------------------------------------------------
# TAB 2: 통계 및 데이터 분포
# ------------------------------------------------------------
with tab2:
    st.markdown("#### **요약 통계**")
    
    temp_std = df_view["temperature"].std()
    humi_std = df_view["humidity"].std()

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("평균 / 최저 온도", f"{df_view['temperature'].mean():.1f} °C", f"최저 {df_view['temperature'].min():.1f} °C")
    s2.metric("최고 온도 / 편차", f"{df_view['temperature'].max():.1f} °C", f"표준편차 {temp_std:.2f}" if pd.notnull(temp_std) else "0.00")
    s3.metric("평균 / 최저 습도", f"{df_view['humidity'].mean():.1f} %", f"최저 {df_view['humidity'].min():.1f} %")
    s4.metric("최고 습도 / 편차", f"{df_view['humidity'].max():.1f} %", f"표준편차 {humi_std:.2f}" if pd.notnull(humi_std) else "0.00")

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        fig_scatter = px.scatter(
            df_view,
            x="temperature",
            y="humidity",
            title="<b>온도 vs 습도 상관관계</b>",
            color_discrete_sequence=["#9B59B6"],
            labels={"temperature": "온도 (°C)", "humidity": "습도 (%)"},
        )
        st.plotly_chart(apply_chart_style(fig_scatter), use_container_width=True)

    with c2:
        fig_temp_hist = px.histogram(
            df_view,
            x="temperature",
            nbins=15,
            title="<b>온도 분포 히스토그램</b>",
            color_discrete_sequence=["#FF5733"],
            labels={"temperature": "온도 (°C)"},
        )
        st.plotly_chart(apply_chart_style(fig_temp_hist), use_container_width=True)

    with c3:
        fig_humi_hist = px.histogram(
            df_view,
            x="humidity",
            nbins=15,
            title="<b>습도 분포 히스토그램</b>",
            color_discrete_sequence=["#00A8E8"],
            labels={"humidity": "습도 (%)"},
        )
        st.plotly_chart(apply_chart_style(fig_humi_hist), use_container_width=True)


# ------------------------------------------------------------
# TAB 3: 상세 데이터 및 다운로드
# ------------------------------------------------------------
with tab3:
    display_df = df_view.sort_values("created_at", ascending=False)

    col_d1, col_d2 = st.columns([4, 1])
    with col_d1:
        st.markdown(f"**최근 {len(display_df)}개 레코드 목록**")
    with col_d2:
        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name="sensor_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", format="%d"),
            "temperature": st.column_config.NumberColumn("온도 (°C)", format="%.1f"),
            "humidity": st.column_config.NumberColumn("습도 (%)", format="%.1f"),
            "created_at": st.column_config.DatetimeColumn("측정 시간", format="YYYY-MM-DD HH:mm:ss"),
        },
    )