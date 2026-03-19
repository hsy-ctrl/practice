import streamlit as st
import pandas as pd

st.set_page_config(page_title="서울시 주차장 대시보드", layout="wide")

# ==============================
# 데이터 로드
# ==============================
@st.cache_data
def load_data():
    df_info = pd.read_csv("서울시 공영주차장 안내 정보.csv")
    df_live = pd.read_csv("서울시 시영주차장 실시간 주차대수 정보.csv")

    # 컬럼명 정리 (필요시 수정)
    df_info.columns = df_info.columns.str.strip()
    df_live.columns = df_live.columns.str.strip()

    # 병합 (주차장코드 기준)
    df = pd.merge(df_live, df_info, on="주차장코드", how="left")

    # 파생 변수 생성
    df["주차가능대수"] = df["총 주차면"] - df["현재 주차 차량수"]
    df["가용률"] = df["주차가능대수"] / df["총 주차면"]

    # 상태 분류
    def status(x):
        if x > 0.7:
            return "여유"
        elif x > 0.3:
            return "보통"
        else:
            return "혼잡"

    df["상태"] = df["가용률"].apply(status)

    return df

df = load_data()

# ==============================
# 사이드바 필터
# ==============================
st.sidebar.header("🔍 필터")

district = st.sidebar.selectbox(
    "자치구 선택",
    ["전체"] + sorted(df["구"].dropna().unique().tolist())
)

status_filter = st.sidebar.multiselect(
    "혼잡도 선택",
    ["여유", "보통", "혼잡"],
    default=["여유", "보통", "혼잡"]
)

# 필터 적용
filtered_df = df.copy()

if district != "전체":
    filtered_df = filtered_df[filtered_df["구"] == district]

filtered_df = filtered_df[filtered_df["상태"].isin(status_filter)]

# ==============================
# 메인 화면
# ==============================
st.title("🚗 서울시 실시간 공영주차장 대시보드")

# KPI
col1, col2, col3 = st.columns(3)

col1.metric("총 주차장 수", len(filtered_df))
col2.metric("평균 가용률", f"{filtered_df['가용률'].mean():.2f}")
col3.metric("총 여유 주차면", int(filtered_df["주차가능대수"].sum()))

# ==============================
# 테이블
# ==============================
st.subheader("📋 주차장 현황")

st.dataframe(
    filtered_df[[
        "주차장명",
        "구",
        "총 주차면",
        "현재 주차 차량수",
        "주차가능대수",
        "가용률",
        "상태"
    ]].sort_values(by="주차가능대수", ascending=False),
    use_container_width=True
)

# ==============================
# 추천 기능 (간단 버전)
# ==============================
st.subheader("⭐ 추천 주차장 TOP 5")

top5 = filtered_df.sort_values(
    by=["가용률", "주차가능대수"],
    ascending=False
).head(5)

st.table(top5[[
    "주차장명",
    "구",
    "주차가능대수",
    "가용률",
    "상태"
]])

# ==============================
# 시각화
# ==============================
st.subheader("📊 가용률 분포")

st.bar_chart(filtered_df["상태"].value_counts())
