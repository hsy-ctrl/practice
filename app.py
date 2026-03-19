import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="서울 주차장 대시보드", layout="wide")

# ==============================
# 데이터 로드 (에러 방지 강화)
# ==============================
@st.cache_data
def load_data():
    try:
        df_info = pd.read_csv("parking_info.csv", encoding="cp949")
        df_live = pd.read_csv("parking_live.csv", encoding="cp949")
    except:
        st.error("CSV 파일을 찾을 수 없습니다. 파일명을 확인하세요.")
        st.stop()

    df_info.columns = df_info.columns.str.strip()
    df_live.columns = df_live.columns.str.strip()

    # 병합
    df = pd.merge(df_live, df_info, on="주차장코드", how="left")

    # 숫자 변환
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

    # 좌표 컬럼 정리 (컬럼명 다를 수 있음 대비)
    lat_cols = [c for c in df.columns if "위도" in c]
    lon_cols = [c for c in df.columns if "경도" in c]

    if lat_cols and lon_cols:
        df["lat"] = pd.to_numeric(df[lat_cols[0]], errors="coerce")
        df["lon"] = pd.to_numeric(df[lon_cols[0]], errors="coerce")
    else:
        st.error("위도/경도 컬럼이 없습니다.")
        st.stop()

    # 결측 제거
    df = df.dropna(subset=["lat", "lon"])

    return df


df = load_data()

# ==============================
# 사이드바
# ==============================
st.sidebar.title("필터")

district_col = [c for c in df.columns if "구" in c]

if district_col:
    district = st.sidebar.selectbox(
        "자치구 선택",
        ["전체"] + sorted(df[district_col[0]].dropna().unique().tolist())
    )

    if district != "전체":
        df = df[df[district_col[0]] == district]

# ==============================
# KPI
# ==============================
st.title("🚗 서울시 실시간 주차 현황")

col1, col2, col3 = st.columns(3)

col1.metric("총 주차장", len(df))
col2.metric("평균 가용률", f"{df['가용률'].mean():.2f}")
col3.metric("총 여유 주차면", int(df["주차가능대수"].sum()))

# ==============================
# 지도 시각화 ⭐⭐⭐
# ==============================

def get_color(status):
    if status == "여유":
        return [0, 200, 0]
    elif status == "보통":
        return [255, 200, 0]
    else:
        return [255, 0, 0]

df["color"] = df["상태"].apply(get_color)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position='[lon, lat]',
    get_fill_color='color',
    get_radius=80,
    pickable=True
)

view_state = pdk.ViewState(
    latitude=df["lat"].mean(),
    longitude=df["lon"].mean(),
    zoom=11
)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# ==============================
# 추천 기능 ⭐
# ==============================
st.subheader("⭐ 추천 주차장 TOP 5")

top5 = df.sort_values(
    by=["가용률", "주차가능대수"],
    ascending=False
).head(5)

st.dataframe(top5[[
    "주차장명",
    "주차가능대수",
    "가용률",
    "상태"
]])

# ==============================
# 테이블
# ==============================
st.subheader("📋 전체 데이터")

st.dataframe(df.head(100))
