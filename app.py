import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
import requests
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

# ══════════════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Seoul ParkMap · 서울 실시간 주차",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,300&family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

:root {
  --bg0:    #060b14;
  --bg1:    #0a1220;
  --bg2:    #0f1c30;
  --bg3:    #162236;
  --border: rgba(0,200,255,0.08);
  --border2:rgba(0,200,255,0.18);
  --cyan:   #00c8ff;
  --cyan2:  #00e5ff;
  --green:  #00ff88;
  --amber:  #ffb300;
  --red:    #ff4757;
  --muted:  #4a6080;
  --text:   #c8dff0;
  --text2:  #7a9ab8;
  --mono:   'JetBrains Mono', monospace;
  --sans:   'DM Sans', 'Noto Sans KR', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
  font-family: var(--sans) !important;
  background: var(--bg0) !important;
  color: var(--text) !important;
}

/* 스크롤바 */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg1); }
::-webkit-scrollbar-thumb { background: rgba(0,200,255,0.2); border-radius: 2px; }

/* 사이드바 */
[data-testid="stSidebar"] {
  background: var(--bg1) !important;
  border-right: 1px solid var(--border2) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] hr { border-color: var(--border2) !important; margin: 12px 0; }
[data-testid="stSidebar"] .stToggle label { font-size: 13px !important; }

/* 메인 패딩 */
.main .block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] + div .block-container { padding: 0 !important; }

/* 탑바 */
.topbar {
  background: linear-gradient(90deg, var(--bg1) 0%, var(--bg2) 100%);
  border-bottom: 1px solid var(--border2);
  padding: 0 28px;
  height: 58px;
  display: flex;
  align-items: center;
  gap: 24px;
  position: sticky;
  top: 0;
  z-index: 999;
}
.topbar-logo {
  font-family: var(--mono);
  font-size: 17px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 2px;
  text-transform: uppercase;
  white-space: nowrap;
}
.topbar-logo span { color: var(--text); font-weight: 300; }
.topbar-sep { width: 1px; height: 24px; background: var(--border2); }
.topbar-time {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text2);
  letter-spacing: 1px;
}
.live-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--green);
  letter-spacing: 1px;
}
.live-dot::before {
  content: '';
  width: 7px; height: 7px;
  background: var(--green);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--green);
  animation: blink 1.4s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 16px; }

/* KPI 띠 */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0;
  border-bottom: 1px solid var(--border);
  background: var(--bg1);
}
.kpi-item {
  padding: 14px 22px;
  border-right: 1px solid var(--border);
  position: relative;
  overflow: hidden;
}
.kpi-item:last-child { border-right: none; }
.kpi-item::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: var(--accent, var(--cyan));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform .4s ease;
}
.kpi-item:hover::after { transform: scaleX(1); }
.kpi-lbl {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 4px;
}
.kpi-val {
  font-family: var(--mono);
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  line-height: 1;
}
.kpi-val span { font-size: 11px; font-weight: 400; color: var(--text2); margin-left: 3px; }
.kpi-sub { font-size: 10px; color: var(--text2); margin-top: 3px; }

/* 탭 네비 */
.nav-strip {
  display: flex;
  gap: 0;
  background: var(--bg1);
  border-bottom: 1px solid var(--border2);
  padding: 0 24px;
}
.nav-btn {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--muted);
  padding: 12px 20px;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .2s;
  white-space: nowrap;
}
.nav-btn:hover { color: var(--text); }
.nav-btn.active { color: var(--cyan); border-bottom-color: var(--cyan); }

/* 본문 래퍼 */
.content-wrap { padding: 20px 24px 40px; }

/* 지도 섹션 */
.map-section {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 16px;
  height: calc(100vh - 200px);
  min-height: 520px;
}
.map-panel {
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}
.map-overlay-top {
  position: absolute;
  top: 12px; left: 12px; right: 12px;
  z-index: 1000;
  display: flex;
  gap: 8px;
  pointer-events: none;
}
.legend-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(6,11,20,0.88);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border2);
  border-radius: 20px;
  padding: 5px 10px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text2);
  letter-spacing: .5px;
  white-space: nowrap;
}
.legend-dot { width: 7px; height: 7px; border-radius: 50%; }

/* 사이드 패널 */
.side-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}
.panel-card {
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 10px;
  padding: 14px 16px;
  flex-shrink: 0;
}
.panel-card-title {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* 구별 바 */
.gu-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.gu-bar-label { font-size: 11px; color: var(--text2); width: 52px; flex-shrink: 0; text-align: right; }
.gu-bar-track { flex: 1; height: 5px; background: var(--bg3); border-radius: 3px; overflow: hidden; }
.gu-bar-fill  { height: 100%; border-radius: 3px; transition: width .6s ease; }
.gu-bar-val   { font-family: var(--mono); font-size: 10px; width: 34px; flex-shrink: 0; text-align: right; }

/* TOP 카드 */
.top-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px solid var(--border);
}
.top-item:last-child { border-bottom: none; }
.top-rank {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  width: 16px;
  flex-shrink: 0;
}
.top-name { font-size: 11px; color: var(--text); flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.top-badge {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
}

/* 통계 차트 래퍼 */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.chart-card {
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 10px;
  padding: 16px 18px;
}
.chart-card-title {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 12px;
}

/* 테이블 */
.tbl-card {
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 14px;
}
.tbl-title {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 12px;
}

/* 검색 / 셀렉트 */
.stTextInput input, .stSelectbox > div > div {
  background: var(--bg2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: var(--sans) !important;
}
.stTextInput input:focus { border-color: var(--cyan) !important; box-shadow: 0 0 0 2px rgba(0,200,255,.1) !important; }

/* 메트릭 */
[data-testid="stMetric"] {
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 10px 14px;
}
[data-testid="stMetricLabel"] { font-size: 10px !important; color: var(--muted) !important; }
[data-testid="stMetricValue"] { font-family: var(--mono) !important; font-size: 20px !important; color: var(--text) !important; }

/* 데이터프레임 */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
[data-testid="stDataFrame"] th { background: var(--bg3) !important; color: var(--text2) !important; font-family: var(--mono) !important; font-size: 10px !important; letter-spacing: 1px !important; }
[data-testid="stDataFrame"] td { font-size: 12px !important; }

/* 버튼 */
.stButton button {
  background: linear-gradient(135deg, rgba(0,200,255,.08) 0%, rgba(0,200,255,.03) 100%) !important;
  border: 1px solid var(--border2) !important;
  color: var(--cyan) !important;
  border-radius: 8px !important;
  font-family: var(--mono) !important;
  font-size: 11px !important;
  letter-spacing: 1px !important;
  transition: all .2s !important;
}
.stButton button:hover {
  background: rgba(0,200,255,.12) !important;
  border-color: var(--cyan) !important;
  box-shadow: 0 0 12px rgba(0,200,255,.15) !important;
}

/* 다운로드 버튼 */
.stDownloadButton button {
  background: transparent !important;
  border: 1px solid var(--border2) !important;
  color: var(--text2) !important;
  border-radius: 6px !important;
  font-size: 11px !important;
}

/* 탭 */
[data-baseweb="tab-list"] {
  background: var(--bg2) !important;
  border-radius: 8px !important;
  padding: 3px !important;
  gap: 2px !important;
}
[data-baseweb="tab"] {
  color: var(--muted) !important;
  border-radius: 6px !important;
  font-family: var(--mono) !important;
  font-size: 11px !important;
  letter-spacing: .5px !important;
}
[aria-selected="true"][data-baseweb="tab"] {
  background: var(--bg3) !important;
  color: var(--cyan) !important;
}

/* 경고 */
[data-testid="stAlert"] {
  background: rgba(255,183,0,.06) !important;
  border: 1px solid rgba(255,183,0,.2) !important;
  border-radius: 8px !important;
}

/* 스피너 */
.stSpinner { color: var(--cyan) !important; }

/* 멀티셀렉트 */
[data-baseweb="multi-select"] { background: var(--bg2) !important; border-color: var(--border2) !important; }
[data-baseweb="tag"] { background: rgba(0,200,255,.1) !important; border-color: var(--border2) !important; }

/* 토글 */
[data-testid="stToggle"] { accent-color: var(--cyan); }

/* 반응형 */
@media (max-width: 768px) {
  .kpi-strip { grid-template-columns: repeat(2,1fr); }
  .map-section { grid-template-columns: 1fr; }
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════════════
try:
    API_KEY = st.secrets["SEOUL_API_KEY"]
except Exception:
    API_KEY = "584a546d737470643333744569725a"

BASE_URL = "http://openAPI.seoul.go.kr:8088"

GU_COORDS = {
    '강남구':(37.5172,127.0473),'강동구':(37.5301,127.1238),'강북구':(37.6396,127.0255),
    '강서구':(37.5509,126.8495),'관악구':(37.4784,126.9516),'광진구':(37.5385,127.0823),
    '구로구':(37.4954,126.8874),'금천구':(37.4602,126.9002),'노원구':(37.6542,127.0568),
    '도봉구':(37.6688,127.0471),'동대문구':(37.5744,127.0396),'동작구':(37.5124,126.9393),
    '마포구':(37.5663,126.9014),'서대문구':(37.5791,126.9368),'서초구':(37.4837,127.0324),
    '성동구':(37.5633,127.0365),'성북구':(37.5894,127.0167),'송파구':(37.5145,127.1059),
    '양천구':(37.5172,126.8664),'영등포구':(37.5264,126.8963),'용산구':(37.5324,126.9906),
    '은평구':(37.6026,126.9291),'종로구':(37.5735,126.9788),'중구':(37.5640,126.9975),
    '중랑구':(37.6063,127.0927),
}


# ══════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════
def fetch_all(service, total_hint=3000):
    rows, start, page_size = [], 1, 1000
    while True:
        end = start + page_size - 1
        url = f"{BASE_URL}/{API_KEY}/json/{service}/{start}/{end}/"
        try:
            res  = requests.get(url, timeout=15)
            data = res.json()
        except Exception as e:
            st.warning(f"API 호출 실패 ({service}): {e}")
            break
        if "RESULT" in data:
            code = data["RESULT"].get("CODE","")
            if code != "INFO-000":
                st.warning(f"API 오류: {data['RESULT'].get('MESSAGE', code)}")
            break
        svc  = data.get(service, {})
        rows.extend(svc.get("row", []))
        if end >= svc.get("list_total_count", 0):
            break
        start += page_size
    return rows


# ══════════════════════════════════════════════════════
# 컬럼 매핑
# ══════════════════════════════════════════════════════
COMMON_MAP = {
    "ADDR":"주소","PKLT_CD":"주차장코드","PKLT_NM":"주차장명",
    "PKLT_TYPE":"주차장 종류","PRK_TYPE_NM":"주차장 종류명",
    "PKLT_KND":"주차장 종류","PKLT_KND_NM":"주차장 종류명",
    "OPER_SE":"운영구분","OPER_SE_NM":"운영구분명","TELNO":"전화번호",
    "TPKCT":"총 주차면","CAPACITY":"총 주차면",
    "NOW_PRK_VHCL_CNT":"현재 주차 차량수","NOW_PRK_VHCL_UPDT_TM":"현재 주차 차량수 업데이트시간",
    "CUR_PARKING":"현재 주차 차량수","CUR_PARKING_TIME":"현재 주차 차량수 업데이트시간",
    "PAY_YN":"유무료구분","PAY_YN_NM":"유무료구분명",
    "CHGD_FREE_SE":"유무료구분","CHGD_FREE_NM":"유무료구분명",
    "PRK_STTS_YN":"유무료구분","PRK_STTS_NM":"유무료구분명",
    "NGHT_PAY_YN":"야간무료개방여부","NGHT_PAY_YN_NM":"야간무료개방여부명",
    "NGHT_FREE_OPN_YN":"야간무료개방여부","NGHT_FREE_OPN_YN_NAME":"야간무료개방여부명",
    "WD_OPER_BGNG_TM":"평일 운영 시작시각(HHMM)","WD_OPER_END_TM":"평일 운영 종료시각(HHMM)",
    "WE_OPER_BGNG_TM":"주말 운영 시작시각(HHMM)","WE_OPER_END_TM":"주말 운영 종료시각(HHMM)",
    "LHLDY_OPER_BGNG_TM":"공휴일 운영 시작시각(HHMM)","LHLDY_OPER_END_TM":"공휴일 운영 종료시각(HHMM)",
    "LHLDY_BGNG":"공휴일 운영 시작시각(HHMM)","LHLDY":"공휴일 운영 종료시각(HHMM)",
    "LAST_DATA_SYNC_TM":"최종데이터 동기화 시간",
    "SAT_CHGD_FREE_SE":"토요일 유,무료 구분","SAT_CHGD_FREE_NM":"토요일 유,무료 구분명",
    "LHLDY_CHGD_FREE_SE":"공휴일 유,무료 구분","LHLDY_CHGD_FREE_SE_NAME":"공휴일 유,무료 구분명",
    "LHLDY_YN":"공휴일 유,무료 구분","LHLDY_NM":"공휴일 유,무료 구분명",
    "BSC_PRK_CRG":"기본 주차 요금","BSC_PRK_HR":"기본 주차 시간(분 단위)",
    "ADD_PRK_CRG":"추가 단위 요금","ADD_PRK_HR":"추가 단위 시간(분 단위)",
    "ADD_CRG":"추가 단위 요금","ADD_UNIT_TM_MNT":"추가 단위 시간(분 단위)",
    "PRK_CRG":"기본 주차 요금","PRK_HM":"기본 주차 시간(분 단위)",
    "BUS_BSC_PRK_CRG":"버스 기본 주차 요금","BUS_BSC_PRK_HR":"버스 기본 주차 시간(분 단위)",
    "BUS_ADD_PRK_HR":"버스 추가 단위 시간(분 단위)","BUS_ADD_PRK_CRG":"버스 추가 단위 요금",
    "BUS_PRK_CRG":"버스 기본 주차 요금","BUS_PRK_HM":"버스 기본 주차 시간(분 단위)",
    "BUS_PRK_ADD_HM":"버스 추가 단위 시간(분 단위)","BUS_PRK_ADD_CRG":"버스 추가 단위 요금",
    "DAY_MAX_CRG":"일 최대 요금","DLY_MAX_CRG":"일 최대 요금",
    "PRD_AMT":"월 정기권 금액","MNTL_CMUT_CRG":"월 정기권 금액",
    "STRT_PKLT_MNG_NO":"노상 주차장 관리그룹번호","CRB_PKLT_MNG_GROUP_NO":"노상 주차장 관리그룹번호",
    "SHRN_PKLT_MNG_NM":"공유 주차장 관리업체명","SHRN_PKLT_MNG_URL":"공유 주차장 관리업체 링크",
    "SHRN_PKLT_YN":"공유 주차장 여부","SHRN_PKLT_ETC":"공유 주차장 기타사항",
    "LAT":"위도","LOT":"경도",
}


# ══════════════════════════════════════════════════════
# 데이터 로드 (5분 캐시)
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S (KST)")

    info_rows = fetch_all("GetParkInfo", 3000)
    if not info_rows:
        st.error("공영주차장 안내 API 호출 실패"); st.stop()
    info = pd.DataFrame(info_rows).rename(columns=COMMON_MAP)

    rt_rows = fetch_all("GetParkingInfo", 300)
    if not rt_rows:
        st.error("실시간 주차대수 API 호출 실패"); st.stop()
    rt = pd.DataFrame(rt_rows).rename(columns=COMMON_MAP)

    # 주차장코드 없으면 주차장명으로 대체
    if "주차장코드" not in info.columns: info["주차장코드"] = info.get("주차장명","")
    if "주차장코드" not in rt.columns:   rt["주차장코드"]   = rt.get("주차장명","")

    # 필수 컬럼 체크
    for req in ["주소","총 주차면"]:
        if req not in info.columns:
            st.error(f"GetParkInfo '{req}' 없음. 실제 컬럼: {info.columns.tolist()}"); st.stop()
    for req in ["주소","총 주차면","현재 주차 차량수"]:
        if req not in rt.columns:
            st.error(f"GetParkingInfo '{req}' 없음. 실제 컬럼: {rt.columns.tolist()}"); st.stop()

    # 구 추출
    info["구"] = info["주소"].str.extract(r"([\w]+구)")
    rt["구"]   = rt["주소"].str.extract(r"([\w]+구)")

    # 숫자 변환
    for col in ["총 주차면","기본 주차 요금","일 최대 요금","월 정기권 금액","위도","경도"]:
        if col in info.columns:
            info[col] = pd.to_numeric(info[col], errors="coerce")
    for col in ["기본 주차 요금","일 최대 요금","월 정기권 금액"]:
        if col in info.columns: info[col] = info[col].fillna(0)
    if "총 주차면" in info.columns: info["총 주차면"] = info["총 주차면"].fillna(0)

    for col in ["총 주차면","현재 주차 차량수","기본 주차 요금","일 최대 요금"]:
        if col in rt.columns:
            rt[col] = pd.to_numeric(rt[col], errors="coerce").fillna(0)

    rt = rt[rt["총 주차면"] > 10].copy()

    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).round(1).clip(0,100)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)
    rt["혼잡도"] = pd.cut(rt["이용률"], bins=[-1,30,70,95,100],
                          labels=["여유","보통","혼잡","만차"]).astype(str)

    # 위경도 조인
    coord_map = info.dropna(subset=["위도","경도"])[["주차장코드","위도","경도"]]
    rt = rt.merge(coord_map, on="주차장코드", how="left")

    rng = np.random.default_rng(42)
    for idx, row in rt[rt["위도"].isna()].iterrows():
        gu = row["구"]
        if gu in GU_COORDS:
            b = GU_COORDS[gu]
            rt.at[idx,"위도"] = b[0] + rng.uniform(-0.018,0.018)
            rt.at[idx,"경도"] = b[1] + rng.uniform(-0.018,0.018)
        else:
            rt.at[idx,"위도"], rt.at[idx,"경도"] = 37.5665, 126.9780

    # 운영시간
    def fmt_t(v):
        try:
            v = int(float(v)); return f"{v//100:02d}:{v%100:02d}"
        except: return "-"
    if "평일 운영 시작시각(HHMM)" in rt.columns:
        rt["평일운영"] = rt.apply(
            lambda r: f"{fmt_t(r.get('평일 운영 시작시각(HHMM)',0))} ~ {fmt_t(r.get('평일 운영 종료시각(HHMM)',2400))}",
            axis=1)
    else:
        rt["평일운영"] = "-"

    if "평일 운영 시작시각(HHMM)" in info.columns:
        info["평일운영"] = info.apply(
            lambda r: f"{fmt_t(r.get('평일 운영 시작시각(HHMM)',0))} ~ {fmt_t(r.get('평일 운영 종료시각(HHMM)',2400))}",
            axis=1)
    else:
        info["평일운영"] = "-"

    # 구별 집계
    gu_rt = rt.groupby("구").agg(
        주차장수=("주차장코드","count"),
        총주차면=("총 주차면","sum"),
        현재차량=("현재 주차 차량수","sum"),
        가용면=("가용면","sum")
    ).reset_index()
    gu_rt["이용률"] = (gu_rt["현재차량"] / gu_rt["총주차면"] * 100).round(1)

    gu_info = info.groupby("구").agg(
        전체주차장수=("주차장코드","count"),
        전체주차면=("총 주차면","sum")
    ).reset_index()

    return info, rt, gu_rt, gu_info, now


# ══════════════════════════════════════════════════════
# 색상 헬퍼
# ══════════════════════════════════════════════════════
def sc(rate):
    if rate >= 95: return "#ff4757","만차","#3d0f14"
    if rate >= 70: return "#ffb300","혼잡","#2d2000"
    if rate >= 30: return "#00c8ff","보통","#002030"
    return "#00ff88","여유","#003020"

def color_util(val):
    try: v = float(val)
    except: return ""
    if v >= 95: return "background:#3d0f14;color:#ff4757;"
    if v >= 70: return "background:#2d2000;color:#ffb300;"
    if v >= 30: return "background:#002030;color:#00c8ff;"
    return "background:#003020;color:#00ff88;"

def style_util(df, col="이용률(%)"):
    s = pd.DataFrame("", index=df.index, columns=df.columns)
    if col in df.columns: s[col] = df[col].map(color_util)
    return s

PLOT_CFG = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,28,48,0.6)",
    font=dict(family="JetBrains Mono, monospace", size=11, color="#4a6080"),
    margin=dict(l=8, r=8, t=32, b=8),
)


# ══════════════════════════════════════════════════════
# Folium 지도
# ══════════════════════════════════════════════════════
def make_map(data, info_data, show_clusters, sel_gu_list):
    m = folium.Map(location=[37.5665,126.9780], zoom_start=11,
                   tiles="CartoDB dark_matter", control_scale=False)
    MiniMap(tile_layer="CartoDB dark_matter", position="bottomright",
            width=110, height=80, zoom_level_offset=-6).add_to(m)

    df = data[data["구"].isin(sel_gu_list)] if sel_gu_list else data.copy()

    target = (MarkerCluster(options={"maxClusterRadius":60,"disableClusteringAtZoom":14})
              if show_clusters else m)
    if show_clusters: target.add_to(m)

    for _, row in df.iterrows():
        try: lat, lng = float(row["위도"]), float(row["경도"])
        except: continue

        rate = float(row.get("이용률",0))
        avail = int(row.get("가용면",0))
        total = int(row.get("총 주차면",0))
        curr  = int(row.get("현재 주차 차량수",0))
        color, status, bg = sc(rate)
        fee   = int(row.get("기본 주차 요금",0))
        mfee  = int(row.get("일 최대 요금",0))
        name  = str(row.get("주차장명",""))
        addr  = str(row.get("주소",""))
        paid  = str(row.get("유무료구분명","-"))
        phone = str(row.get("전화번호","-"))
        kind  = str(row.get("주차장 종류명","-"))
        ops   = str(row.get("평일운영","-"))
        upd   = str(row.get("현재 주차 차량수 업데이트시간","-"))[:16]
        bw    = min(int(rate),100)

        popup_html = f"""
<div style="font-family:'Noto Sans KR',sans-serif;width:272px;background:#060b14;
  border:1px solid {color}44;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,{bg} 0%,#060b14 100%);
    border-bottom:1px solid {color}33;padding:14px 16px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span style="font-family:'JetBrains Mono',monospace;font-size:9px;
        color:{color};letter-spacing:2px;text-transform:uppercase;">{status}</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:20px;
        font-weight:700;color:{color};">{rate:.0f}<span style="font-size:11px">%</span></span>
    </div>
    <div style="font-size:13px;font-weight:600;color:#c8dff0;margin-bottom:2px;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
    <div style="font-size:10px;color:#4a6080;">{addr}</div>
  </div>
  <div style="padding:12px 14px;">
    <div style="background:#0a1220;border-radius:4px;height:4px;margin-bottom:12px;overflow:hidden;">
      <div style="width:{bw}%;height:100%;background:{color};
        box-shadow:0 0 8px {color}88;border-radius:4px;"></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:12px;">
      {"".join(f'<div style="background:#0a1220;border:1px solid #0f1c30;border-radius:6px;padding:8px;text-align:center;"><div style="font-size:9px;color:#4a6080;margin-bottom:3px;letter-spacing:1px;">{l}</div><div style="font-family:\'JetBrains Mono\',monospace;font-size:15px;font-weight:700;color:{cv};">{v}</div></div>'
        for l,v,cv in [("전체",total,"#7a9ab8"),("현재",curr,color),("가용",avail,"#00ff88")])}
    </div>
    <div style="display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:11px;row-gap:5px;">
      <span style="color:#4a6080;">🕐</span><span style="color:#7a9ab8;">{ops}</span>
      <span style="color:#4a6080;">💰</span><span style="color:#7a9ab8;">{f"{fee:,}원/5분" if fee>0 else "무료"}</span>
      <span style="color:#4a6080;">📅</span><span style="color:#7a9ab8;">{f"{mfee:,}원" if mfee>0 else "-"}</span>
      <span style="color:#4a6080;">📞</span><span style="color:#7a9ab8;">{phone if phone not in ("nan","") else "-"}</span>
    </div>
    <div style="margin-top:10px;padding-top:8px;border-top:1px solid #0f1c30;
      display:flex;gap:5px;flex-wrap:wrap;">
      <span style="background:{color}18;color:{color};border:1px solid {color}44;
        border-radius:4px;padding:2px 8px;font-family:'JetBrains Mono',monospace;
        font-size:9px;letter-spacing:1px;">{kind}</span>
      <span style="background:#0a1220;color:#4a6080;border:1px solid #0f1c30;
        border-radius:4px;padding:2px 8px;font-size:9px;">{paid}</span>
      <span style="margin-left:auto;color:#2a3a50;font-family:'JetBrains Mono',monospace;
        font-size:9px;">{upd}</span>
    </div>
  </div>
</div>"""

        icon_html = f"""
<div style="position:relative;width:36px;height:36px;">
  <div style="position:absolute;inset:0;background:{color};border-radius:50% 50% 50% 0;
    transform:rotate(-45deg);border:2px solid {color}66;
    box-shadow:0 0 12px {color}66,0 2px 8px rgba(0,0,0,0.6);"></div>
  <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
      color:#060b14;transform:translateY(-2px);">{"P" if avail>0 else "×"}</span>
  </div>
</div>"""

        folium.Marker(
            location=[lat,lng],
            popup=folium.Popup(popup_html, max_width=290),
            tooltip=f"<b style='font-size:12px'>{name}</b><br><span style='color:{color}'>{rate:.0f}%</span> · 가용 {avail}면",
            icon=folium.DivIcon(html=icon_html, icon_size=(36,36), icon_anchor=(18,36)),
        ).add_to(target)

    # 공영 전체 (회색 소형 핀)
    rt_names = set(data["주차장명"].tolist())
    info_df = info_data.dropna(subset=["위도","경도"]).copy()
    if sel_gu_list: info_df = info_df[info_df["구"].isin(sel_gu_list)]
    info_df = info_df[~info_df["주차장명"].isin(rt_names)]

    gray_target = (MarkerCluster(options={"maxClusterRadius":60,"disableClusteringAtZoom":14})
                   if show_clusters else m)
    if show_clusters: gray_target.add_to(m)

    for _, row in info_df.iterrows():
        try:
            lat, lng = float(row["위도"]), float(row["경도"])
            if not (-90<=lat<=90 and -180<=lng<=180): continue
        except: continue

        name  = str(row.get("주차장명",""))
        addr  = str(row.get("주소",""))
        total = int(row.get("총 주차면",0))
        fee   = int(row.get("기본 주차 요금",0))
        mfee  = int(row.get("일 최대 요금",0))
        paid  = str(row.get("유무료구분명","-"))
        phone = str(row.get("전화번호","-"))
        kind  = str(row.get("주차장 종류명","-"))
        ops   = str(row.get("평일운영","-"))

        gpopup = f"""
<div style="font-family:'Noto Sans KR',sans-serif;width:256px;background:#060b14;
  border:1px solid #162236;border-radius:12px;overflow:hidden;">
  <div style="background:#0a1220;border-bottom:1px solid #162236;padding:12px 14px;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:#2a3a50;
      letter-spacing:2px;margin-bottom:4px;">NO REALTIME DATA</div>
    <div style="font-size:13px;font-weight:600;color:#c8dff0;margin-bottom:2px;">{name}</div>
    <div style="font-size:10px;color:#4a6080;">{addr}</div>
  </div>
  <div style="padding:12px 14px;">
    <div style="background:#0a1220;border:1px solid #162236;border-radius:6px;
      padding:10px;text-align:center;margin-bottom:10px;">
      <div style="font-size:9px;color:#4a6080;letter-spacing:1px;margin-bottom:4px;">CAPACITY</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:22px;
        font-weight:700;color:#7a9ab8;">{total}<span style="font-size:11px">면</span></div>
    </div>
    <div style="display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:11px;">
      <span style="color:#4a6080;">🕐</span><span style="color:#4a6080;">{ops}</span>
      <span style="color:#4a6080;">💰</span><span style="color:#4a6080;">{f"{fee:,}원/5분" if fee>0 else "무료"}</span>
      <span style="color:#4a6080;">📞</span><span style="color:#4a6080;">{phone if phone not in ("nan","") else "-"}</span>
    </div>
    <div style="margin-top:8px;display:flex;gap:5px;flex-wrap:wrap;">
      <span style="background:#0a1220;color:#2a3a50;border:1px solid #162236;
        border-radius:4px;padding:2px 8px;font-size:9px;">{kind}</span>
      <span style="background:#0a1220;color:#2a3a50;border:1px solid #162236;
        border-radius:4px;padding:2px 8px;font-size:9px;">{paid}</span>
    </div>
  </div>
</div>"""

        gicon = """
<div style="position:relative;width:24px;height:24px;">
  <div style="position:absolute;inset:0;background:#162236;border-radius:50% 50% 50% 0;
    transform:rotate(-45deg);border:1px solid #2a3a50;box-shadow:0 1px 4px rgba(0,0,0,0.5);"></div>
  <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:8px;
      color:#4a6080;transform:translateY(-1px);">P</span>
  </div>
</div>"""

        folium.Marker(
            location=[lat,lng],
            popup=folium.Popup(gpopup, max_width=270),
            tooltip=f"<b>{name}</b><br><span style='color:#4a6080'>총 {total}면 · 미연계</span>",
            icon=folium.DivIcon(html=gicon, icon_size=(24,24), icon_anchor=(12,24)),
        ).add_to(gray_target)

    return m


# ══════════════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════════════
with st.spinner("데이터 수신 중..."):
    info, rt, gu_rt, gu_info, last_updated = load_data()

GU_LIST = sorted(info["구"].dropna().unique().tolist())

# 세션 상태 — 현재 페이지
if "page" not in st.session_state:
    st.session_state.page = "map"


# ══════════════════════════════════════════════════════
# 사이드바 — 필터만
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:13px;
      color:#00c8ff;letter-spacing:2px;margin-bottom:4px;">SEOUL PARKMAP</div>
    <div style="font-size:11px;color:#4a6080;margin-bottom:16px;">
      {last_updated}
    </div>""", unsafe_allow_html=True)

    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear(); st.rerun()

    st.markdown("---")
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#4a6080;letter-spacing:2px;margin-bottom:10px;">FILTER</div>', unsafe_allow_html=True)

    sel_gu     = st.multiselect("자치구", GU_LIST, placeholder="전체")
    sel_status = st.multiselect("혼잡도", ["여유","보통","혼잡","만차"], placeholder="전체")
    sel_fee    = st.multiselect("유무료", ["유료","무료"], placeholder="전체")

    st.markdown("---")
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#4a6080;letter-spacing:2px;margin-bottom:10px;">MAP</div>', unsafe_allow_html=True)
    show_clusters = st.toggle("클러스터링", value=True)
    st.markdown("---")
    st.caption("서울 열린데이터 광장 · 5분 갱신")


def filt(df):
    d = df.copy()
    if sel_gu     and "구"           in d.columns: d = d[d["구"].isin(sel_gu)]
    if sel_fee    and "유무료구분명" in d.columns: d = d[d["유무료구분명"].isin(sel_fee)]
    if sel_status and "혼잡도"       in d.columns: d = d[d["혼잡도"].isin(sel_status)]
    return d

fi = filt(info)
fr = filt(rt)
rt_spots = int(fr["총 주차면"].sum())
rt_curr  = int(fr["현재 주차 차량수"].sum())
rt_avail = int(fr["가용면"].sum())
rt_rate  = round(rt_curr/rt_spots*100,1) if rt_spots>0 else 0
_, rt_status, _ = sc(rt_rate)


# ══════════════════════════════════════════════════════
# 탑바
# ══════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <div class="topbar-logo">SEOUL<span> PARKMAP</span></div>
  <div class="topbar-sep"></div>
  <div class="live-dot">LIVE</div>
  <div class="topbar-sep"></div>
  <div class="topbar-time">{last_updated}</div>
  <div class="topbar-right">
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#4a6080;">
      실시간 연계 <b style="color:#00c8ff">{len(fr)}</b>개소 &nbsp;|&nbsp;
      전체 <b style="color:#7a9ab8">{len(fi):,}</b>개소
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# KPI 띠
# ══════════════════════════════════════════════════════
_, ac, _ = sc(rt_rate)
avail_color = "#00ff88" if rt_avail > 500 else "#ffb300" if rt_avail > 100 else "#ff4757"

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-item" style="--accent:#00c8ff">
    <div class="kpi-lbl">공영주차장</div>
    <div class="kpi-val">{len(fi):,}<span>개소</span></div>
    <div class="kpi-sub">서울시 전체</div>
  </div>
  <div class="kpi-item" style="--accent:{avail_color}">
    <div class="kpi-lbl">현재 가용</div>
    <div class="kpi-val" style="color:{avail_color}">{rt_avail:,}<span>면</span></div>
    <div class="kpi-sub">즉시 주차 가능</div>
  </div>
  <div class="kpi-item" style="--accent:{ac}">
    <div class="kpi-lbl">전체 이용률</div>
    <div class="kpi-val" style="color:{ac}">{rt_rate}<span>%</span></div>
    <div class="kpi-sub">{rt_status} · 실시간 기준</div>
  </div>
  <div class="kpi-item" style="--accent:#7a9ab8">
    <div class="kpi-lbl">현재 차량</div>
    <div class="kpi-val">{rt_curr:,}<span>대</span></div>
    <div class="kpi-sub">실시간 연계 {len(fr)}개소</div>
  </div>
  <div class="kpi-item" style="--accent:#00ff88">
    <div class="kpi-lbl">만차 주차장</div>
    <div class="kpi-val" style="color:#ff4757">{int((fr['이용률']>=95).sum())}<span>개소</span></div>
    <div class="kpi-sub">여유 {int((fr['이용률']<30).sum())}개소</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 네비게이션 탭
# ══════════════════════════════════════════════════════
col_nav = st.columns([1,1,1,6])
with col_nav[0]:
    if st.button("🗺️  지도", use_container_width=True):
        st.session_state.page = "map"
with col_nav[1]:
    if st.button("📊  통계", use_container_width=True):
        st.session_state.page = "stats"
with col_nav[2]:
    if st.button("📋  목록", use_container_width=True):
        st.session_state.page = "list"

page = st.session_state.page
st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ① 실시간 지도
# ══════════════════════════════════════════════════════
if page == "map":
    st.markdown('<div class="content-wrap" style="padding-top:0">', unsafe_allow_html=True)

    # 범례
    st.markdown("""
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;padding:0 2px;">
      <div class="legend-pill"><div class="legend-dot" style="background:#00ff88;box-shadow:0 0 4px #00ff88"></div>여유 &lt;30%</div>
      <div class="legend-pill"><div class="legend-dot" style="background:#00c8ff;box-shadow:0 0 4px #00c8ff"></div>보통 30~70%</div>
      <div class="legend-pill"><div class="legend-dot" style="background:#ffb300;box-shadow:0 0 4px #ffb300"></div>혼잡 70~95%</div>
      <div class="legend-pill"><div class="legend-dot" style="background:#ff4757;box-shadow:0 0 4px #ff4757"></div>만차 95%+</div>
      <div class="legend-pill"><div class="legend-dot" style="background:#162236"></div>미연계</div>
      <div class="legend-pill" style="margin-left:auto">📍 핀 클릭 → 상세정보</div>
    </div>
    """, unsafe_allow_html=True)

    map_col, side_col = st.columns([3, 1])

    with map_col:
        m = make_map(fr, fi, show_clusters, sel_gu)
        st_folium(m, width="100%", height=580,
                  returned_objects=[], key="main_map")

    with side_col:
        # 구별 이용률 바
        f_gu = (gu_rt[gu_rt["구"].isin(sel_gu)] if sel_gu else gu_rt.copy())
        f_gu = f_gu.sort_values("이용률", ascending=False)

        bars_html = ""
        for _, row in f_gu.iterrows():
            v = float(row["이용률"])
            c, _, _ = sc(v)
            w = min(v, 100)
            bars_html += f"""
<div class="gu-bar-row">
  <div class="gu-bar-label">{row['구']}</div>
  <div class="gu-bar-track">
    <div class="gu-bar-fill" style="width:{w}%;background:{c};box-shadow:0 0 4px {c}55;"></div>
  </div>
  <div class="gu-bar-val" style="color:{c}">{v:.0f}%</div>
</div>"""

        st.markdown(f"""
        <div class="panel-card" style="margin-bottom:12px">
          <div class="panel-card-title">구별 이용률</div>
          {bars_html}
        </div>
        """, unsafe_allow_html=True)

        # 혼잡 TOP5
        top5 = fr.nlargest(5,"이용률")[["주차장명","이용률","가용면"]]
        top_html = ""
        for i, (_, row) in enumerate(top5.iterrows(), 1):
            v = float(row["이용률"])
            c, s, _ = sc(v)
            top_html += f"""
<div class="top-item">
  <div class="top-rank">{i:02d}</div>
  <div class="top-name">{row['주차장명']}</div>
  <div class="top-badge" style="background:{c}18;color:{c};border:1px solid {c}44;">{v:.0f}%</div>
</div>"""

        st.markdown(f"""
        <div class="panel-card" style="margin-bottom:12px">
          <div class="panel-card-title">🔴 혼잡 TOP 5</div>
          {top_html}
        </div>
        """, unsafe_allow_html=True)

        # 여유 TOP5
        free5 = fr[fr["이용률"]<100].nsmallest(5,"이용률")[["주차장명","이용률","가용면"]]
        free_html = ""
        for i, (_, row) in enumerate(free5.iterrows(), 1):
            v = float(row["이용률"])
            c, _, _ = sc(v)
            free_html += f"""
<div class="top-item">
  <div class="top-rank">{i:02d}</div>
  <div class="top-name">{row['주차장명']}</div>
  <div class="top-badge" style="background:{c}18;color:{c};border:1px solid {c}44;">{int(row['가용면'])}면</div>
</div>"""

        st.markdown(f"""
        <div class="panel-card">
          <div class="panel-card-title">🟢 여유 TOP 5</div>
          {free_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ② 통계 대시보드
# ══════════════════════════════════════════════════════
elif page == "stats":
    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    # 혼잡도 + 종류 차트
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-card-title">혼잡도 분포</div>', unsafe_allow_html=True)
        cnt = fr["혼잡도"].value_counts().reindex(["여유","보통","혼잡","만차"], fill_value=0)
        colors_bar = ["#00ff88","#00c8ff","#ffb300","#ff4757"]
        fig = go.Figure(go.Bar(
            x=cnt.index, y=cnt.values,
            marker_color=colors_bar, marker_line_width=0,
            text=cnt.values, textposition="outside",
            textfont=dict(color="#7a9ab8", family="JetBrains Mono"),
        ))
        fig.update_layout(**PLOT_CFG, height=240, showlegend=False,
                          xaxis=dict(tickfont=dict(color="#7a9ab8",family="JetBrains Mono",size=11),
                                     gridcolor="rgba(0,200,255,0.04)"),
                          yaxis=dict(gridcolor="rgba(0,200,255,0.04)", zeroline=False,
                                     showticklabels=False))
        fig.update_traces(width=0.55)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-card-title">주차장 종류</div>', unsafe_allow_html=True)
        vc = fi["주차장 종류명"].value_counts() if "주차장 종류명" in fi.columns else pd.Series()
        fig2 = go.Figure(go.Pie(
            labels=vc.index, values=vc.values, hole=0.6,
            marker=dict(colors=["#00c8ff","#00ff88","#ffb300","#ff4757","#7a9ab8"],
                        line=dict(color="#060b14", width=2)),
            textinfo="percent", textfont=dict(family="JetBrains Mono", size=10, color="#c8dff0"),
        ))
        fig2.update_layout(**PLOT_CFG, height=240, showlegend=True,
                           legend=dict(font=dict(family="JetBrains Mono",size=10,color="#7a9ab8"),
                                       bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    # 구별 종합
    merged = pd.merge(gu_info, gu_rt, on="구", how="outer").fillna(0)
    merged["실시간이용률"] = merged.apply(
        lambda r: round(r["현재차량"]/r["총주차면"]*100,1) if r["총주차면"]>0 else 0.0, axis=1)
    if sel_gu: merged = merged[merged["구"].isin(sel_gu)]
    merged = merged.sort_values("실시간이용률", ascending=False)
    disp = merged[["구","전체주차장수","전체주차면","주차장수","총주차면","현재차량","가용면","실시간이용률"]].copy()
    disp.columns = ["자치구","전체 주차장","전체 주차면","실시간 연계","연계 주차면","현재 차량","가용 면수","이용률(%)"]

    st.markdown('<div class="tbl-card">', unsafe_allow_html=True)
    st.markdown('<div class="tbl-title">자치구별 종합 현황</div>', unsafe_allow_html=True)
    st.dataframe(
        disp.style.apply(style_util, axis=None)
            .format({"전체 주차장":"{:,.0f}","전체 주차면":"{:,.0f}","실시간 연계":"{:,.0f}",
                     "연계 주차면":"{:,.0f}","현재 차량":"{:,.0f}","가용 면수":"{:,.0f}","이용률(%)":"{:.1f}"}),
        use_container_width=True, height=420, hide_index=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 수평 바 2개
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-card-title">구별 전체 주차면</div>', unsafe_allow_html=True)
        srt = disp.sort_values("전체 주차면", ascending=True)
        fig3 = go.Figure(go.Bar(
            x=srt["전체 주차면"], y=srt["자치구"], orientation="h",
            marker=dict(color=srt["전체 주차면"],
                        colorscale=[[0,"#0a1220"],[0.5,"#0f3a5a"],[1,"#00c8ff"]],
                        line_width=0),
            text=srt["전체 주차면"].map(lambda v: f"{int(v):,}"),
            textposition="outside", textfont=dict(size=9,color="#4a6080",family="JetBrains Mono"),
        ))
        fig3.update_layout(**PLOT_CFG, height=max(320, len(srt)*22+40),
                           xaxis=dict(gridcolor="rgba(0,200,255,0.04)",showticklabels=False,zeroline=False),
                           yaxis=dict(tickfont=dict(size=10,color="#7a9ab8",family="JetBrains Mono"),
                                      gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-card-title">구별 실시간 이용률</div>', unsafe_allow_html=True)
        srt2 = disp.sort_values("이용률(%)", ascending=True)
        fig4 = go.Figure(go.Bar(
            x=srt2["이용률(%)"], y=srt2["자치구"], orientation="h",
            marker_color=[sc(v)[0] for v in srt2["이용률(%)"]],
            marker_line_width=0,
            text=srt2["이용률(%)"].map(lambda v: f"{v:.1f}%"),
            textposition="outside", textfont=dict(size=9,color="#4a6080",family="JetBrains Mono"),
        ))
        fig4.update_layout(**PLOT_CFG, height=max(320, len(srt2)*22+40),
                           xaxis=dict(range=[0,115],gridcolor="rgba(0,200,255,0.04)",
                                      showticklabels=False,zeroline=False),
                           yaxis=dict(tickfont=dict(size=10,color="#7a9ab8",family="JetBrains Mono"),
                                      gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# ③ 주차장 목록
# ══════════════════════════════════════════════════════
elif page == "list":
    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["  🔴  실시간 현황  ","  📁  전체 공영주차장  "])

    with tab1:
        fr2 = filt(rt)
        c1, c2, c3 = st.columns([3,2,1])
        with c1:
            search = st.text_input("", placeholder="🔍  주차장명 검색...", label_visibility="collapsed")
            if search: fr2 = fr2[fr2["주차장명"].str.contains(search, na=False)]
        with c2:
            sort_opt = st.selectbox("", ["이용률 높은 순","이용률 낮은 순","가용면 많은 순","가용면 적은 순"],
                                    label_visibility="collapsed")
        with c3:
            st.download_button("↓ CSV", fr2.to_csv(index=False,encoding="utf-8-sig"),
                               file_name="실시간_주차현황.csv", mime="text/csv",
                               use_container_width=True)

        sm = {"이용률 높은 순":("이용률",False),"이용률 낮은 순":("이용률",True),
              "가용면 많은 순":("가용면",False),"가용면 적은 순":("가용면",True)}
        sc_col, asc_v = sm[sort_opt]
        fr2 = fr2.sort_values(by=sc_col, ascending=asc_v)

        mc1,mc2,mc3,mc4 = st.columns(4)
        mc1.metric("조회",    f"{len(fr2)}개소")
        mc2.metric("총 주차면", f"{int(fr2['총 주차면'].sum()):,}면")
        mc3.metric("현재 차량", f"{int(fr2['현재 주차 차량수'].sum()):,}대")
        mc4.metric("가용면",  f"{int(fr2['가용면'].sum()):,}면")

        cols_want = [
            ("구","구"),("주차장명","주차장명"),("주소","주소"),
            ("총 주차면","전체"),("현재 주차 차량수","현재"),
            ("가용면","가용"),("이용률","이용률(%)"),("혼잡도","혼잡도"),
            ("기본 주차 요금","기본요금(원)"),("일 최대 요금","일최대(원)"),
            ("평일운영","평일운영"),("현재 주차 차량수 업데이트시간","업데이트"),
        ]
        cols_rt  = [c for c,_ in cols_want if c in fr2.columns]
        cols_ren = [r for c,r in cols_want if c in fr2.columns]
        missing  = [c for c,_ in cols_want if c not in fr2.columns]
        if missing: st.caption(f"미포함 컬럼: {missing}")

        disp_rt = fr2[cols_rt].copy()
        disp_rt.columns = cols_ren

        fmt = {k:v for k,v in {"전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}",
                                "이용률(%)":"{:.1f}","기본요금(원)":"{:,.0f}","일최대(원)":"{:,.0f}"
                               }.items() if k in disp_rt.columns}
        st.markdown('<div class="tbl-card">', unsafe_allow_html=True)
        st.dataframe(
            disp_rt.style.apply(style_util, axis=None).format(fmt),
            use_container_width=True, height=520, hide_index=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        fi2 = filt(info)
        c1, c2, c3 = st.columns([3,2,1])
        with c1:
            s2 = st.text_input("", placeholder="🔍  주차장명 검색...", label_visibility="collapsed", key="s2")
            if s2: fi2 = fi2[fi2["주차장명"].str.contains(s2, na=False)]
        with c2:
            so2 = st.selectbox("", ["주차면 많은 순","기본요금 낮은 순","기본요금 높은 순"],
                               label_visibility="collapsed", key="so2")
        with c3:
            st.download_button("↓ CSV", fi2.to_csv(index=False,encoding="utf-8-sig"),
                               file_name="공영주차장_목록.csv", mime="text/csv",
                               use_container_width=True)

        if so2=="주차면 많은 순":    fi2 = fi2.sort_values("총 주차면", ascending=False)
        elif so2=="기본요금 낮은 순": fi2 = fi2.sort_values("기본 주차 요금")
        else:                        fi2 = fi2.sort_values("기본 주차 요금", ascending=False)

        mc1,mc2,mc3 = st.columns(3)
        mc1.metric("조회",    f"{len(fi2):,}개소")
        mc2.metric("총 주차면", f"{int(fi2['총 주차면'].sum()):,}면")
        mc3.metric("유료 비율", f"{round(len(fi2[fi2['유무료구분명']=='유료'])/max(len(fi2),1)*100,1)}%")

        cols_i = ["구","주차장명","주소","주차장 종류명","운영구분명",
                  "총 주차면","유무료구분명","기본 주차 요금","일 최대 요금","월 정기권 금액","전화번호"]
        cols_i2 = [c for c in cols_i if c in fi2.columns]
        disp_i = fi2[cols_i2].copy()
        ren_i = {"주차장 종류명":"종류","운영구분명":"운영구분","유무료구분명":"유무료",
                 "기본 주차 요금":"기본요금(원)","일 최대 요금":"일최대(원)","월 정기권 금액":"월정기권(원)"}
        disp_i = disp_i.rename(columns=ren_i)

        fmt_i = {k:v for k,v in {"총 주차면":"{:,.0f}","기본요금(원)":"{:,.0f}",
                                  "일최대(원)":"{:,.0f}","월정기권(원)":"{:,.0f}"
                                 }.items() if k in disp_i.columns}
        st.markdown('<div class="tbl-card">', unsafe_allow_html=True)
        st.dataframe(disp_i.style.format(fmt_i),
                     use_container_width=True, height=520, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
