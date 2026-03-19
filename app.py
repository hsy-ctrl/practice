import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="환경 정책 의사결정 대시보드", layout="wide")

# ---------------------------
# UI 스타일
# ---------------------------
st.markdown("""
<style>
.big-title {font-size:34px; font-weight:700;}
.kpi-box {padding:10px; border-radius:10px; background-color:#F4F6F6;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">🌍 환경-보건 정책 의사결정 시스템</p>', unsafe_allow_html=True)

# ---------------------------
# 데이터 생성
# ---------------------------
np.random.seed(42)
n = 100

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
# 사이드바 (정책 설정)
# ---------------------------
st.sidebar.header("⚙️ 정책 시뮬레이션")

car = st.sidebar.slider("🚗 자가용 감소 (%)", 0, 60, 20)
nox = st.sidebar.slider("🌫 NOx 저감 (%)", 0, 60, 20)
policy_type = st.sidebar.selectbox("정책 전략", ["단일 정책", "교통 중심", "통합 정책"])

scenario = data.copy()

if policy_type == "교통 중심":
    car *= 1.5
elif policy_type == "통합 정책":
    car *= 1.3
    nox *= 1.3

# 적용
scenario["Car_Usage"] *= (1 - car / 100)
scenario["NOx"] *= (1 - (car * 0.3) / 100)
scenario["NOx"] *= (1 - nox / 100)

scenario["Lung_Disease"] = (
    100 + scenario["NOx"] * 1800 + scenario["SOx"] * 800
)

# ---------------------------
# KPI
# ---------------------------
before = data["Lung_Disease"].mean()
after = scenario["Lung_Disease"].mean()
change = ((before - after) / before) * 100

high_risk_before = (data["Lung_Disease"] > 180).sum()
high_risk_after = (scenario["Lung_Disease"] > 180).sum()

# ---------------------------
# KPI 출력
# ---------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("기존 평균", f"{before:.1f}")
col2.metric("정책 후", f"{after:.1f}", f"{after-before:.1f}")
col3.metric("개선율", f"{change:.2f}%")
col4.metric("고위험 지역 감소", f"{high_risk_after}", f"{high_risk_after - high_risk_before}")

st.markdown("---")

# ---------------------------
# 1. 분포 비교
# ---------------------------
st.subheader("📊 정책 전후 분포 변화")

fig1 = go.Figure()

fig1.add_trace(go.Histogram(x=data["Lung_Disease"], name="기존", opacity=0.6))
fig1.add_trace(go.Histogram(x=scenario["Lung_Disease"], name="정책", opacity=0.6))

fig1.update_layout(barmode="overlay")

st.plotly_chart(fig1, use_container_width=True)

# ---------------------------
# 2. 민감도 분석
# ---------------------------
st.subheader("📈 정책 민감도 분석 (NOx vs 폐질환)")

x_vals = np.linspace(0.02, 0.08, 50)
y_vals = 100 + x_vals * 1800

fig2 = px.line(x=x_vals, y=y_vals, labels={"x": "NOx", "y": "폐질환"})
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# 3. 리스크 구간 분석
# ---------------------------
st.subheader("🚨 고위험 구간 분석")

scenario["Risk"] = pd.cut(
    scenario["Lung_Disease"],
    bins=[0, 140, 180, 300],
    labels=["Low", "Medium", "High"]
)

risk_count = scenario["Risk"].value_counts().reset_index()

fig3 = px.bar(
    risk_count,
    x="Risk",
    y="count",
    title="리스크 구간 분포"
)

st.plotly_chart(fig3, use_container_width=True)

# ---------------------------
# 4. 다변수 관계
# ---------------------------
st.subheader("🌐 다변수 영향 분석")

fig4 = px.scatter(
    scenario,
    x="NOx",
    y="Lung_Disease",
    size="Car_Usage",
    color="Pop_Density",
    hover_data=["SOx"]
)

st.plotly_chart(fig4, use_container_width=True)

# ---------------------------
# 5. 자동 정책 해석
# ---------------------------
st.subheader("🧠 정책 해석")

if change > 15:
    st.success("강력한 정책 효과: 통합 정책이 매우 효과적입니다.")
elif change > 5:
    st.warning("중간 수준 효과: 추가 정책 필요")
else:
    st.error("효과 미미: 구조적 접근 필요")

st.markdown(f"""
- 평균 폐질환 감소율: **{change:.2f}%**
- NOx 감소가 주요 기여 요인
- 자가용 정책은 간접 효과 중심
""")

# ---------------------------
# 6. 데이터
# ---------------------------
st.subheader("📋 데이터")

st.dataframe(scenario)

st.download_button(
    "CSV 다운로드",
    scenario.to_csv(index=False),
    file_name="policy_simulation.csv"
)
