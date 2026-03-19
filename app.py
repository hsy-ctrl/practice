import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="서울 주차장 대시보드", layout="wide")

# ==============================
# 데이터 로드
# ==============================
@st.cache_data
def load_data():
    try:
        df_info = pd.read_csv("parking_info.csv", encoding="cp949")
        df_live = pd.read_csv("parking_live.csv", encoding="cp949")
    except Exception as e:
        st.error(f"파일 로딩 실패: {e}")
        st.stop()

    # 컬럼 공백 제거
    df_info.columns = df_info.columns.str.strip()
    df_live.columns = df_live.columns.str.strip()

    # 병합
    df = pd.merge(df_live, df_info, on="주차장코드", how="left")

    # 숫자 처리
    df["총 주차면"] = pd.to_numeric(df["총 주차면"], errors="coerce")
    df["현재 주차 차량수"] = pd.to_numeric(df["현재 주차 차량수"], errors="coerce")

    # 파생 변수
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

    # 좌표 자동 탐색
    lat_col = [c for c in df.columns if "위도" in c][0]
    lon_col = [c for c in df.columns if "경도" in c][0]

    df["lat"] = pd.to_numeric(df[lat_col], errors="coerce")
    df["lon"] = pd.to_numeric(df[lon_col], errors="coerce")

    df = df.dropna(subset=["lat", "lon"])

    return df


df = load_data()

# ==============================
# 사이드바 필터
# ==============================
st.sidebar.title("🔍 필터")

district_col = [c for c in df.columns if "구" in c][0]

district = st.sidebar.selectbox(
    "자치구 선택",
    ["전체"] + sorted(df[district_col].dropna().unique().tolist())
)

status_filter = st.sidebar.multiselect(
    "혼잡도",
    ["여유", "보통", "혼잡"],
    default=["여유", "보통", "혼잡"]
)

# 필터 적용
filtered_df = df.copy()

if district != "전체":
    filtered_df = filtered_df[filtered_df[district_col] == district]

filtered_df = filtered_df[filtered_df["상태"].isin(status_filter)]

# ==============================
# 메인 KPI
# ==============================
st.title("🚗 서울시 실시간 공영주차장 현황")

col1, col2, col3 = st.columns(3)

col1.metric("총 주차장", len(filtered_df))
col2.metric("평균 가용률", f"{filtered_df['가용률'].mean():.2f}")
col3.metric("총 여유 주차면", int(filtered_df["주차가능대수"].sum()))

# ==============================
# 지도 시각화 ⭐⭐⭐
# ==============================
st.subheader("📍 지도")

def get_color(status):
    if status == "여유":
        return [0, 200, 0]
    elif status == "보통":
        return [255, 200, 0]
    else:
        return [255, 0, 0]

filtered_df["color"] = filtered_df["상태"].apply(get_color)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position='[lon, lat]',
    get_fill_color='color',
    get_radius=80,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=filtered_df["lat"].mean(),
    longitude=filtered_df["lon"].mean(),
    zoom=11
)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# ==============================
# 추천 기능 ⭐
# ==============================
st.subheader("⭐ 추천 주차장 TOP 5")

top5 = filtered_df.sort_values(
    by=["가용률", "주차가능대수"],
    ascending=False
).head(5)

st.dataframe(
    top5[[
        "주차장명",
        "주차가능대수",
        "가용률",
        "상태"
    ]],
    use_container_width=True
)

# ==============================
# 전체 테이블
# ==============================
st.subheader("📋 전체 주차장 현황")

st.dataframe(
    filtered_df[[
        "주차장명",
        "주차가능대수",
        "가용률",
        "상태"
    ]].sort_values(by="주차가능대수", ascending=False),
    use_container_width=True
)
