import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Seoul ParkMap", layout="wide")

st.title("🚗 Seoul ParkMap")
st.markdown("지금 바로, 가장 가까운 주차 공간으로")

# ---------------------------
# Mock 데이터 생성 (기획안 기반)
# ---------------------------
@st.cache_data
def generate_data(n=200):
    gu_list = [
        "강남구", "송파구", "서초구", "마포구", "강서구",
        "노원구", "도봉구", "은평구", "중구", "용산구"
    ]
    
    data = {
        "주차장명": [f"공영주차장_{i}" for i in range(n)],
        "자치구": np.random.choice(gu_list, n),
        "총 주차면": np.random.randint(20, 300, n),
        "현재주차대수": np.random.randint(0, 300, n),
        "기본 주차 요금": np.random.randint(500, 5000, n),
        "일 최대 요금": np.random.randint(5000, 80000, n),
        "위도": np.random.uniform(37.45, 37.65, n),
        "경도": np.random.uniform(126.8, 127.1, n),
        "운영시간": "24시간"
    }
    
    df = pd.DataFrame(data)
    
    # 이용률 계산
    df["이용률(%)"] = (df["현재주차대수"] / df["총 주차면"]) * 100
    
    # 혼잡도 분류 (기획안 기준)
    def get_status(rate):
        if rate < 30:
            return "여유"
        elif rate < 70:
            return "보통"
        elif rate < 95:
            return "혼잡"
        else:
            return "만차"
    
    df["혼잡도"] = df["이용률(%)"].apply(get_status)
    
    return df

df = generate_data()

# ---------------------------
# 사이드 필터 (기획안 SCR-05)
# ---------------------------
st.sidebar.header("🔍 필터")

selected_gu = st.sidebar.multiselect(
    "자치구 선택",
    sorted(df["자치구"].unique()),
    default=list(df["자치구"].unique())
)

selected_status = st.sidebar.multiselect(
    "혼잡도",
    ["여유", "보통", "혼잡", "만차"],
    default=["여유", "보통", "혼잡", "만차"]
)

df = df[
    (df["자치구"].isin(selected_gu)) &
    (df["혼잡도"].isin(selected_status))
]

# ---------------------------
# KPI (SCR-04)
# ---------------------------
st.subheader("📊 전체 현황")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("총 주차장 수", len(df))

with col2:
    st.metric("총 주차면", int(df["총 주차면"].sum()))

with col3:
    st.metric("평균 이용률", f"{df['이용률(%)'].mean():.1f}%")

# ---------------------------
# 지도 (SCR-01)
# ---------------------------
st.subheader("🗺️ 지도")

map_df = df[["위도", "경도"]].copy()
map_df.columns = ["lat", "lon"]

st.map(map_df)

# ---------------------------
# 리스트 뷰 (SCR-03)
# ---------------------------
st.subheader("📋 주차장 리스트")

sort_option = st.selectbox(
    "정렬 기준",
    ["거리순(임시)", "이용률순", "요금순"]
)

if sort_option == "이용률순":
    df = df.sort_values(by="이용률(%)", ascending=False)
elif sort_option == "요금순":
    df = df.sort_values(by="기본 주차 요금")

st.dataframe(
    df[[
        "자치구",
        "주차장명",
        "총 주차면",
        "현재주차대수",
        "이용률(%)",
        "혼잡도",
        "기본 주차 요금",
        "일 최대 요금"
    ]],
    use_container_width=True
)

# ---------------------------
# 상세 정보 (SCR-02 느낌)
# ---------------------------
st.subheader("📍 주차장 상세")

selected = st.selectbox("주차장 선택", df["주차장명"])

detail = df[df["주차장명"] == selected].iloc[0]

st.write(f"### {detail['주차장명']}")
st.write(f"자치구: {detail['자치구']}")
st.write(f"혼잡도: {detail['혼잡도']}")
st.write(f"이용률: {detail['이용률(%)']:.1f}%")
st.write(f"총 주차면: {int(detail['총 주차면'])}")
st.write(f"현재 주차: {int(detail['현재주차대수'])}")
st.write(f"기본 요금: {int(detail['기본 주차 요금'])}원")
st.write(f"일 최대 요금: {int(detail['일 최대 요금'])}원")
st.write(f"운영시간: {detail['운영시간']}")

# ---------------------------
# 대시보드 (SCR-04 확장)
# ---------------------------
st.subheader("📊 통계")

col1, col2 = st.columns(2)

with col1:
    st.write("자치구별 주차장 수")
    st.bar_chart(df["자치구"].value_counts())

with col2:
    st.write("혼잡도 분포")
    st.bar_chart(df["혼잡도"].value_counts())
