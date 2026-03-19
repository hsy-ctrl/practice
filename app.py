import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="환경 보건 정책 분석 대시보드",
    layout="wide"
)

# ---------------------------
# 0. 스타일
# ---------------------------
st.markdown("""
    <style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
    }
    .kpi {
        font-size: 24px;
        font-weight: bold;
        color: #2E86C1;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🌍 환경-보건 통합 분석 대시보드</p>', unsafe_allow_html=True)
st.markdown("NOx 매개효과 기반 정책 시뮬레이션")

# ---------------------------
# 1. 데이터 생성
# ---------------------------
np.random.seed(42)
n = 50

data = pd.DataFrame({
    "SOx": np.random.uniform(0.01, 0.05, n),
    "NOx": np.random.uniform(0.02, 0.08, n),
    "Car_Usage": np.random.uniform(30, 80, n),
    "Pop_Density": np.random.uniform(2000, 15000, n)
})

data["Lung_Disease"] = (
    100
    + data["NOx"] * 1800
    + data["SOx"] * 800
    + np.random.normal(0, 10, n)
)

# ---------------------------
# 2. 사이드바 (정책)
# ---------------------------
st.sidebar.header("📊 정책 시나리오")

car_reduction = st.sidebar.slider("자가용 이용률 감소 (%)", 0, 50, 10)
nox_reduction = st.sidebar.slider("NOx 저감 기술 (%)", 0, 50, 10)

scenario_data = data.copy()

scenario_data["Car_Usage"] *= (1 - car_reduction / 100)
scenario_data["NOx"] *= (1 - (car_reduction * 0.3) / 100)
scenario_data["NOx"] *= (1 - nox_reduction / 100)

scenario_data["Lung_Disease"] = (
    100
    + scenario_data["NOx"] * 1800
    + scenario_data["SOx"] * 800
)

# ---------------------------
# KPI 계산
# ---------------------------
before = data["Lung_Disease"].mean()
after = scenario_data["Lung_Disease"].mean()
reduction = ((before - after) / before) * 100

# ---------------------------
# 탭 구성
# ---------------------------
tab1, tab2, tab3 = st.tabs(["📊 대시보드", "📈 분석", "📋 데이터"])

# ---------------------------
# TAB 1: 대시보드
# ---------------------------
with tab1:
    st.subheader("📊 정책 효과 요약")

    col1, col2, col3 = st.columns(3)

    col1.metric("기존 폐질환 지수", f"{before:.1f}")
    col2.metric("정책 적용 후", f"{after:.1f}", f"{after-before:.1f}")
    col3.metric("개선율 (%)", f"{reduction:.2f}%")

    st.markdown("---")

    st.subheader("📉 폐질환 분포 변화")

    combined = pd.concat([
        data.assign(Type="기존"),
        scenario_data.assign(Type="정책 적용")
    ])

    fig = px.histogram(
        combined,
        x="Lung_Disease",
        color="Type",
        barmode="overlay",
        nbins=20,
        opacity=0.6
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# TAB 2: 분석
# ---------------------------
with tab2:
    st.subheader("📈 NOx vs 폐질환 관계")

    fig2 = px.scatter(
        data,
        x="NOx",
        y="Lung_Disease",
        size="Car_Usage",
        color="Pop_Density",
        title="NOx가 폐질환에 미치는 영향"
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🧠 핵심 인사이트")

    corr = data["NOx"].corr(data["Lung_Disease"])

    st.markdown(f"""
    - NOx와 폐질환 상관계수: **{corr:.2f}**
    - 자가용 이용률은 NOx를 매개로 간접 영향
    - 정책 효과는 교통 + 환경 동시 개입 시 극대화
    """)

# ---------------------------
# TAB 3: 데이터
# ---------------------------
with tab3:
    st.subheader("📋 데이터 테이블")

    st.dataframe(scenario_data)

    st.download_button(
        "CSV 다운로드",
        scenario_data.to_csv(index=False),
        file_name="environment_health_data.csv"
    )
