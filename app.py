import streamlit as st
import pandas as pd

st.set_page_config(page_title="서울 공영주차장 현황", layout="wide")

st.title("🚗 서울 공영주차장 간단 조회")
st.markdown("구별 주차장 수 및 실시간 주차 대수 확인")

# -------------------------
# 데이터 로드
# -------------------------
@st.cache_data
def load_data():
    info = pd.read_csv("서울시 공영주차장 안내 정보.csv", encoding="cp949")
    realtime = pd.read_csv("서울시 시영주차장 실시간 주차대수 정보.csv", encoding="cp949")
    return info, realtime

info_df, realtime_df = load_data()

# -------------------------
# 데이터 전처리 (컬럼명은 실제 파일에 맞게 수정 필요)
# -------------------------
# 예시 컬럼명 (필요시 수정!)
# info_df: 주차장명, 자치구, 총주차면수
# realtime_df: 주차장명, 현재주차대수, 주차가능대수

# 컬럼명 정리 (혹시 모를 공백 제거)
info_df.columns = info_df.columns.str.strip()
realtime_df.columns = realtime_df.columns.str.strip()

# 병합
df = pd.merge(info_df, realtime_df, on="주차장명", how="left")

# -------------------------
# 사이드바 필터
# -------------------------
gu_list = sorted(df["자치구"].dropna().unique())
selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + gu_list)

if selected_gu != "전체":
    df = df[df["자치구"] == selected_gu]

# -------------------------
# KPI
# -------------------------
total_parking = len(df)
total_capacity = df["총주차면수"].sum()
total_available = df["주차가능대수"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("주차장 개수", f"{total_parking} 개")
col2.metric("총 주차면", f"{int(total_capacity)} 면")
col3.metric("현재 이용 가능", f"{int(total_available)} 면")

# -------------------------
# 구별 집계
# -------------------------
st.subheader("📊 자치구별 주차장 수")

gu_summary = (
    df.groupby("자치구")
    .agg(
        주차장수=("주차장명", "count"),
        총면수=("총주차면수", "sum"),
        가능면수=("주차가능대수", "sum"),
    )
    .reset_index()
)

st.dataframe(gu_summary, use_container_width=True)

# -------------------------
# 상세 테이블
# -------------------------
st.subheader("📋 주차장 상세 정보")
st.dataframe(df.head(100), use_container_width=True)
