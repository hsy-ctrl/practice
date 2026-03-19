import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="환경 보건 분석 대시보드", layout="wide")

st.title("🌍 대기오염-보건 영향 분석 대시보드")
st.markdown("NOx, SOx, 자가용 이용률과 폐질환 간 관계 분석")

# ---------------------------
# 1. 데이터 생성 (보고서 기반 가상 데이터)
# ---------------------------
np.random.seed(42)

n = 50

data = pd.DataFrame({
    "SOx": np.random.uniform(0.01, 0.05, n),
    "NOx": np.random.uniform(0.02, 0.08, n),
    "Car_Usage": np.random.uniform(30, 80, n),
    "Pop_Density": np.random.uniform(2000, 15000, n)
})

# 폐질환 생성 (보고서 기반 관계 반영)
data["Lung_Disease"] = (
    100
    + data["NOx"] * 1800   # 핵심 영향
    + data["SOx"] * 800
    + np.random.normal(0, 10, n)
)

# ---------------------------
# 2. 사이드바 (정책 시나리오)
# ---------------------------
st.sidebar.header("📊 정책 시나리오 설정")

car_reduction = st.sidebar.slider("자가용 이용률 감소 (%)", 0, 50, 0)
nox_reduction = st.sidebar.slider("NOx 저감 기술 (%)", 0, 50, 0)

# 정책 반영
scenario_data = data.copy()
scenario_data["Car_Usage"] *= (1 - car_reduction / 100)

# Car → NOx 간접 영향 반영
scenario_data["NOx"] *= (1 - (car_reduction * 0.3) / 100)

# 직접 NOx 저감
scenario_data["NOx"] *= (1 - nox_reduction / 100)

# 폐질환 재계산
scenario_data["Lung_Disease"] = (
    100
    + scenario_data["NOx"] * 1800
    + scenario_data["SOx"] * 800
)

# ---------------------------
# 3. 상관관계 시각화
# ---------------------------
st.subheader("📈 NOx vs 폐질환")

fig, ax = plt.subplots()
ax.scatter(data["NOx"], data["Lung_Disease"], label="기존", alpha=0.7)
ax.scatter(scenario_data["NOx"], scenario_data["Lung_Disease"], label="정책 적용", alpha=0.7)
ax.set_xlabel("NOx 농도")
ax.set_ylabel("폐질환 지수")
ax.legend()

st.pyplot(fig)

# ---------------------------
# 4. 요약 지표
# ---------------------------
st.subheader("📊 정책 효과 요약")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "기존 평균 폐질환",
        round(data["Lung_Disease"].mean(), 2)
    )

with col2:
    st.metric(
        "정책 적용 후",
        round(scenario_data["Lung_Disease"].mean(), 2),
        delta=round(scenario_data["Lung_Disease"].mean() - data["Lung_Disease"].mean(), 2)
    )

# ---------------------------
# 5. 인사이트 출력
# ---------------------------
st.subheader("🧠 분석 인사이트")

corr = data["NOx"].corr(data["Lung_Disease"])

st.write(f"- NOx와 폐질환 상관계수: **{corr:.2f}**")
st.write("- 자가용 이용률 감소는 NOx 감소를 통해 간접적으로 건강 개선에 기여")
st.write("- 단순 정화 기술보다 교통 정책 병행이 효과적")

# ---------------------------
# 6. 데이터 테이블
# ---------------------------
st.subheader("📋 데이터 확인")
st.dataframe(scenario_data)
