import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="서울 공영주차장 분석 대시보드", layout="wide")

# ==============================
# 데이터 로드
# ==============================
@st.cache_data
def load_data():
    df_info = pd.read_csv("parking_info.csv", encoding="cp949")
    df_live = pd.read_csv("parking_live.csv", encoding="cp949")

    df_info.columns = df_info.columns.str.strip()
    df_live.columns = df_live.columns.str.strip()

    # 병합
    df = pd.merge(df_live, df_info, on="주차장코드", how="left")

    # 숫자 처리
    df["총 주차면"] = pd.to_numeric(df["총 주차면"], errors="coerce")
    df["현재 주차 차량수"] = pd.to_numeric(df["현재 주차 차량수"], errors="coerce")

    # ------------------------------
    # ⭐ 데이터 품질 반영 (보고서 기반)
    # ------------------------------
    df = df[df["총 주차면"] > 10]

    # 파생 변수
    df["주차가능대수"] = df["총 주차면"] - df["현재 주차 차량수"]
    df["이용률"] = df["현재 주차 차량수"] / df["총 주차면"]

    # ------------------------------
    # ⭐ 혼잡 기준 (보고서 기준)
    # ------------------------------
    def status(rate):
        if rate >= 0.95:
            return "만차"
        elif rate >= 0.7:
            return "혼잡"
        elif rate >= 0.3:
            return "보통"
        else:
            return "여유"

    df["상태"] = df["이용률"].apply(status)

    # 좌표 처리
    lat_col = [c for c in df.columns if "위도" in c][0]
    lon_col = [c for c in df.columns if "경도" in c][0]

    df["lat"] = pd.to_numeric(df[lat_col], errors="coerce")
    df["lon"] = pd.to_numeric(df[lon_col], errors="coerce")

    df = df.dropna(subset=["lat", "lon"])

    return df


df = load_data()

# ==============================
# 헤더
# ==============================
st.title("🚗 서울시 공영주차장 실시간 분석 대시보드")

st.info("""
📌 본 서비스는 공영주차장 데이터 분석 보고서를 기반으로 제작되었습니다.
실시간 데이터는 일부 주차장에만 제공됩니다.
""")

# ==============================
# KPI
# ==============================
col1, col2, col3 = st.columns(3)

col1.metric("주차장 수", len(df))
col2.metric("평균 이용률", f"{df['이용률'].mean()*100:.1f}%")
col3.metric("총 가용 주차면", int(df["주차가능대수"].sum()))

# ==============================
# 지도 시각화
# ==============================
st.subheader("📍 주차장 위치 및 혼잡도")

def get_color(status):
    if status == "여유":
        return [0, 200, 0]
    elif status == "보통":
        return [255, 200, 0]
    elif status == "혼잡":
        return [255, 100, 0]
    else:
        return [255, 0, 0]

df["color"] = df["상태"].apply(get_color)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position='[lon, lat]',
    get_fill_color='color',
    get_radius=80,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=df["lat"].mean(),
    longitude=df["lon"].mean(),
    zoom=11
)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# ==============================
# 자치구 분석 ⭐
# ==============================
st.subheader("📊 자치구별 이용률")

district_col = [c for c in df.columns if "구" in c][0]

district_summary = df.groupby(district_col).agg({
    "현재 주차 차량수": "sum",
    "총 주차면": "sum"
})

district_summary["이용률"] = (
    district_summary["현재 주차 차량수"] /
    district_summary["총 주차면"]
)

st.bar_chart(district_summary["이용률"])

# ==============================
# 추천 기능
# ==============================
st.subheader("⭐ 여유 주차장 TOP 5")

top5 = df.sort_values(
    by=["주차가능대수", "이용률"],
    ascending=[False, True]
).head(5)

st.dataframe(top5[[
    "주차장명",
    "주차가능대수",
    "이용률",
    "상태"
]])

# ==============================
# 테이블
# ==============================
st.subheader("📋 전체 주차장 현황")

st.dataframe(
    df[[
        "주차장명",
        "주차가능대수",
        "이용률",
        "상태"
    ]].sort_values(by="주차가능대수", ascending=False),
    use_container_width=True
)
info_file = st.file_uploader("주차장 정보 CSV 업로드")
live_file = st.file_uploader("실시간 CSV 업로드")

if info_file and live_file:
    df_info = pd.read_csv(info_file, encoding="cp949")
    df_live = pd.read_csv(live_file, encoding="cp949")
else:
    st.stop()
