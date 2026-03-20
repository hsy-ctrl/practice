import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
import requests
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))  # 한국 표준시 (UTC+9)

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="서울 주차맵",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Noto Sans KR', sans-serif !important; }
.stApp { background: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"] { background: #161b22 !important; border-right: 1px solid #30363d; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] .stMarkdown h3 { color: #58a6ff !important; }
[data-testid="stSidebar"] hr { border-color: #30363d !important; }
.park-header { background: #161b22; border: 1px solid #30363d; border-radius: 16px; padding: 20px 28px; margin-bottom: 20px; display: flex; align-items: center; gap: 20px; }
.park-title { font-size: 28px; font-weight: 700; color: #f0f6fc; letter-spacing: -0.5px; }
.park-title span { color: #58a6ff; }
.park-subtitle { font-size: 13px; color: #8b949e; margin-top: 3px; }
.park-badge { font-size: 11px; font-weight: 600; background: rgba(88,166,255,0.1); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); border-radius: 20px; padding: 4px 12px; white-space: nowrap; }
.live-badge { font-size: 11px; font-weight: 600; background: rgba(63,185,80,0.1); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); border-radius: 20px; padding: 4px 12px; white-space: nowrap; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
.kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 16px; }
.kpi-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 14px 16px; position: relative; overflow: hidden; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background: var(--kc); }
.kpi-lbl { font-size:10px; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }
.kpi-val { font-size:24px; font-weight:700; color:#f0f6fc; line-height:1; }
.kpi-sub { font-size:11px; color:#8b949e; margin-top:4px; }
.legend-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.legend-item { display:flex; align-items:center; gap:6px; font-size:12px; color:#c9d1d9; }
.legend-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.error-box { background:#21262d; border:1px solid #f85149; border-radius:12px; padding:20px; text-align:center; color:#f85149; }
[data-baseweb="tab-list"] { background: #161b22 !important; border-radius:10px; gap:4px; }
[data-baseweb="tab"] { color:#8b949e !important; border-radius:8px !important; }
[aria-selected="true"][data-baseweb="tab"] { background:#21262d !important; color:#58a6ff !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# API 설정
# ─────────────────────────────────────────
# Streamlit Cloud: Settings > Secrets 에서 SEOUL_API_KEY 설정
# 로컬: st.secrets 대신 직접 문자열로 테스트 가능
try:
    API_KEY = st.secrets["SEOUL_API_KEY"]
except Exception:
    API_KEY = "584a546d737470643333744569725a"  # 발급받은 키 직접 입력 (로컬용)

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


# ─────────────────────────────────────────
# API 호출 함수
# ─────────────────────────────────────────
def fetch_all(service: str, total_hint: int = 3000) -> list:
    """서울 Open API 전체 데이터 페이지네이션 호출"""
    rows = []
    page_size = 1000
    start = 1
    while True:
        end = start + page_size - 1
        url = f"{BASE_URL}/{API_KEY}/json/{service}/{start}/{end}/"
        try:
            res = requests.get(url, timeout=15)
            data = res.json()
        except Exception as e:
            st.warning(f"API 호출 실패 ({service}): {e}")
            break

        # 에러 응답 처리
        if "RESULT" in data:
            code = data["RESULT"].get("CODE", "")
            if code != "INFO-000":
                st.warning(f"API 오류: {data['RESULT'].get('MESSAGE', code)}")
            break

        svc_data = data.get(service, {})
        chunk = svc_data.get("row", [])
        rows.extend(chunk)

        total = svc_data.get("list_total_count", 0)
        if end >= total:
            break
        start += page_size

    return rows


# ─────────────────────────────────────────
# 데이터 로드 — ttl=300 (5분마다 자동 갱신)
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S (KST)")

    # ① 공영주차장 안내 정보 (GetParkInfo)
    info_rows = fetch_all("GetParkInfo", total_hint=3000)
    if not info_rows:
        st.error("공영주차장 안내 API 호출 실패. 인증키와 네트워크를 확인하세요.")
        st.stop()
    info = pd.DataFrame(info_rows)

    # ② 시영주차장 실시간 주차대수 (GetParkingInfo)
    rt_rows = fetch_all("GetParkingInfo", total_hint=300)
    if not rt_rows:
        st.error("실시간 주차대수 API 호출 실패.")
        st.stop()
    rt = pd.DataFrame(rt_rows)

    # ── 실제 API 컬럼명 → 한글 통일 ─────────────────
    # GetParkInfo 실제 확인 컬럼: ADDR, PKLT_CD, OPER_SE, OPER_SE_NM,
    #   SAT_CHGD_FREE_SE, SAT_CHGD_FREE_NM, LAT 가 영문
    #   나머지는 이미 한글로 내려옴
    COMMON_MAP = {
        # ── GetParkInfo / GetParkingInfo 실제 확인된 영문 컬럼 전체 ──
        # 주소/식별
        "ADDR":                  "주소",
        "PKLT_CD":               "주차장코드",
        "PKLT_NM":               "주차장명",
        # 종류/운영
        "PKLT_TYPE":             "주차장 종류",
        "PRK_TYPE_NM":           "주차장 종류명",
        "PKLT_KND":              "주차장 종류",
        "PKLT_KND_NM":           "주차장 종류명",
        "OPER_SE":               "운영구분",
        "OPER_SE_NM":            "운영구분명",
        "TELNO":                 "전화번호",
        # 주차면
        "TPKCT":                 "총 주차면",
        "CAPACITY":              "총 주차면",
        # 실시간 현황
        "NOW_PRK_VHCL_CNT":      "현재 주차 차량수",
        "NOW_PRK_VHCL_UPDT_TM":  "현재 주차 차량수 업데이트시간",
        "CUR_PARKING":           "현재 주차 차량수",
        "CUR_PARKING_TIME":      "현재 주차 차량수 업데이트시간",
        # 유무료
        "PAY_YN":                "유무료구분",
        "PAY_YN_NM":             "유무료구분명",
        "CHGD_FREE_SE":          "유무료구분",
        "CHGD_FREE_NM":          "유무료구분명",
        "PRK_STTS_YN":           "유무료구분",
        "PRK_STTS_NM":           "유무료구분명",
        # 야간
        "NGHT_PAY_YN":           "야간무료개방여부",
        "NGHT_PAY_YN_NM":        "야간무료개방여부명",
        "NGHT_FREE_OPN_YN":      "야간무료개방여부",
        "NGHT_FREE_OPN_YN_NAME": "야간무료개방여부명",
        # 운영시간
        "WD_OPER_BGNG_TM":       "평일 운영 시작시각(HHMM)",
        "WD_OPER_END_TM":        "평일 운영 종료시각(HHMM)",
        "WE_OPER_BGNG_TM":       "주말 운영 시작시각(HHMM)",
        "WE_OPER_END_TM":        "주말 운영 종료시각(HHMM)",
        "LHLDY_OPER_BGNG_TM":    "공휴일 운영 시작시각(HHMM)",
        "LHLDY_OPER_END_TM":     "공휴일 운영 종료시각(HHMM)",
        "LHLDY_BGNG":            "공휴일 운영 시작시각(HHMM)",
        "LHLDY":                 "공휴일 운영 종료시각(HHMM)",
        "LAST_DATA_SYNC_TM":     "최종데이터 동기화 시간",
        # 토요일/공휴일 유무료
        "SAT_CHGD_FREE_SE":      "토요일 유,무료 구분",
        "SAT_CHGD_FREE_NM":      "토요일 유,무료 구분명",
        "LHLDY_CHGD_FREE_SE":    "공휴일 유,무료 구분",
        "LHLDY_CHGD_FREE_SE_NAME":"공휴일 유,무료 구분명",
        "LHLDY_YN":              "공휴일 유,무료 구분",
        "LHLDY_NM":              "공휴일 유,무료 구분명",
        # 요금
        "BSC_PRK_CRG":           "기본 주차 요금",
        "BSC_PRK_HR":            "기본 주차 시간(분 단위)",
        "ADD_PRK_CRG":           "추가 단위 요금",
        "ADD_PRK_HR":            "추가 단위 시간(분 단위)",
        "ADD_CRG":               "추가 단위 요금",
        "ADD_UNIT_TM_MNT":       "추가 단위 시간(분 단위)",
        "PRK_CRG":               "기본 주차 요금",
        "PRK_HM":                "기본 주차 시간(분 단위)",
        "BUS_BSC_PRK_CRG":       "버스 기본 주차 요금",
        "BUS_BSC_PRK_HR":        "버스 기본 주차 시간(분 단위)",
        "BUS_ADD_PRK_HR":        "버스 추가 단위 시간(분 단위)",
        "BUS_ADD_PRK_CRG":       "버스 추가 단위 요금",
        "BUS_PRK_CRG":           "버스 기본 주차 요금",
        "BUS_PRK_HM":            "버스 기본 주차 시간(분 단위)",
        "BUS_PRK_ADD_HM":        "버스 추가 단위 시간(분 단위)",
        "BUS_PRK_ADD_CRG":       "버스 추가 단위 요금",
        "DAY_MAX_CRG":           "일 최대 요금",
        "DLY_MAX_CRG":           "일 최대 요금",
        "PRD_AMT":               "월 정기권 금액",
        "MNTL_CMUT_CRG":         "월 정기권 금액",
        # 노상
        "STRT_PKLT_MNG_NO":      "노상 주차장 관리그룹번호",
        "CRB_PKLT_MNG_GROUP_NO": "노상 주차장 관리그룹번호",
        # 공유주차장
        "SHRN_PKLT_MNG_NM":      "공유 주차장 관리업체명",
        "SHRN_PKLT_MNG_URL":     "공유 주차장 관리업체 링크",
        "SHRN_PKLT_YN":          "공유 주차장 여부",
        "SHRN_PKLT_ETC":         "공유 주차장 기타사항",
        # 좌표
        "LAT":                   "위도",
        "LOT":                   "경도",
    }
    INFO_COL_MAP = COMMON_MAP
    RT_COL_MAP   = COMMON_MAP
    info = info.rename(columns=INFO_COL_MAP)
    rt   = rt.rename(columns=RT_COL_MAP)

    # 주차장코드가 없으면 주차장명을 코드 대신 사용
    if "주차장코드" not in info.columns:
        info["주차장코드"] = info["주차장명"]
    if "주차장코드" not in rt.columns:
        rt["주차장코드"] = rt["주차장명"]

    # 필수 컬럼 체크 — 없으면 실제 컬럼명 출력
    for req in ["주소", "총 주차면"]:
        if req not in info.columns:
            st.error(f"공영주차장 API 응답에 '{req}' 컬럼 없음\n\n실제 컬럼: {info.columns.tolist()}")
            st.stop()
    for req in ["주소", "총 주차면", "현재 주차 차량수"]:
        if req not in rt.columns:
            st.error(f"실시간 API 응답에 '{req}' 컬럼 없음\n\n실제 컬럼: {rt.columns.tolist()}")
            st.stop()

    # ── 전처리 ────────────────────────────────────────
    info["구"] = info["주소"].str.extract(r"([\w]+구)")
    rt["구"]   = rt["주소"].str.extract(r"([\w]+구)")

    # 숫자 컬럼 변환
    for col in ["총 주차면","기본 주차 요금","기본 주차 시간(분 단위)",
                "추가 단위 요금","추가 단위 시간(분 단위)",
                "일 최대 요금","월 정기권 금액","위도","경도"]:
        if col in info.columns:
            info[col] = pd.to_numeric(info[col], errors="coerce")
    for col in ["기본 주차 요금","일 최대 요금","월 정기권 금액"]:
        if col in info.columns:
            info[col] = info[col].fillna(0)
    if "총 주차면" in info.columns:
        info["총 주차면"] = info["총 주차면"].fillna(0)

    for col in ["총 주차면","현재 주차 차량수","기본 주차 요금","일 최대 요금"]:
        if col in rt.columns:
            rt[col] = pd.to_numeric(rt[col], errors="coerce").fillna(0)

    # 이상치 제거 (총 주차면 10 이하)
    rt = rt[rt["총 주차면"] > 10].copy()

    # 파생 컬럼
    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).round(1).clip(0, 100)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)
    rt["혼잡도"] = pd.cut(
        rt["이용률"], bins=[-1,30,70,95,100],
        labels=["여유","보통","혼잡","만차"]
    ).astype(str)

    # 실시간 위경도: info에서 주차장명 기준 조인 → 없으면 구별 랜덤 배치
    coord_map = info.dropna(subset=["위도","경도"])[["주차장코드","위도","경도"]]
    rt = rt.merge(coord_map, on="주차장코드", how="left")

    rng = np.random.default_rng(42)
    for idx, row in rt[rt["위도"].isna()].iterrows():
        gu = row["구"]
        if gu in GU_COORDS:
            blat, blng = GU_COORDS[gu]
            rt.at[idx, "위도"] = blat + rng.uniform(-0.018, 0.018)
            rt.at[idx, "경도"] = blng + rng.uniform(-0.018, 0.018)
        else:
            rt.at[idx, "위도"] = 37.5665
            rt.at[idx, "경도"] = 126.9780

    # 운영시간 포맷
    def fmt_time(v):
        try:
            v = int(float(v))
            return f"{v//100:02d}:{v%100:02d}"
        except: return "-"

    rt["평일운영"] = rt.apply(
        lambda r: f"{fmt_time(r.get('평일 운영 시작시각(HHMM)',0))} ~ {fmt_time(r.get('평일 운영 종료시각(HHMM)',2400))}",
        axis=1
    )

    # 구별 집계
    gu_rt = (
        rt.groupby("구")
        .agg(주차장수=("주차장코드","count"),
             총주차면=("총 주차면","sum"),
             현재차량=("현재 주차 차량수","sum"),
             가용면=("가용면","sum"))
        .reset_index()
    )
    gu_rt["이용률"] = (gu_rt["현재차량"] / gu_rt["총주차면"] * 100).round(1)

    gu_info = (
        info.groupby("구")
        .agg(전체주차장수=("주차장코드","count"),
             전체주차면=("총 주차면","sum"))
        .reset_index()
    )

    return info, rt, gu_rt, gu_info, now


# ─────────────────────────────────────────
# 색상 & 스타일 헬퍼
# ─────────────────────────────────────────
def status_color(rate):
    if rate >= 95: return "#f85149", "만차"
    if rate >= 70: return "#e3b341", "혼잡"
    if rate >= 30: return "#388bfd", "보통"
    return "#3fb950", "여유"

def color_util(val):
    try: v = float(val)
    except: return ""
    if v >= 95: return "background-color:#3d1a1a; color:#f85149;"
    if v >= 70: return "background-color:#2d2200; color:#e3b341;"
    if v >= 30: return "background-color:#0d2340; color:#388bfd;"
    return "background-color:#0d2d1a; color:#3fb950;"

def style_util(df, col="이용률(%)"):
    s = pd.DataFrame("", index=df.index, columns=df.columns)
    if col in df.columns:
        s[col] = df[col].map(color_util)
    return s


# ─────────────────────────────────────────
# Folium 지도 생성
# ─────────────────────────────────────────
def make_map(data, show_clusters, sel_gu_list):
    m = folium.Map(
        location=[37.5665, 126.9780],
        zoom_start=11,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    MiniMap(tile_layer="CartoDB dark_matter", position="bottomright", width=120, height=90).add_to(m)

    df = data.copy()
    if sel_gu_list:
        df = df[df["구"].isin(sel_gu_list)]

    target = MarkerCluster(options={"maxClusterRadius":50,"disableClusteringAtZoom":14}) if show_clusters else m
    if show_clusters:
        target.add_to(m)

    for _, row in df.iterrows():
        try:
            lat, lng = float(row["위도"]), float(row["경도"])
        except: continue

        rate   = float(row.get("이용률", 0))
        avail  = int(row.get("가용면", 0))
        total  = int(row.get("총 주차면", 0))
        curr   = int(row.get("현재 주차 차량수", 0))
        color, status = status_color(rate)
        fee    = int(row.get("기본 주차 요금", 0))
        max_fee= int(row.get("일 최대 요금", 0))
        ops    = row.get("평일운영", "-")
        name   = str(row.get("주차장명", ""))
        addr   = str(row.get("주소", ""))
        paid   = str(row.get("유무료구분명", "-"))
        phone  = str(row.get("전화번호", "-"))
        kind   = str(row.get("주차장 종류명", "-"))
        upd    = str(row.get("현재 주차 차량수 업데이트시간", "-"))[:16]

        bar_w = min(int(rate), 100)
        popup_html = f"""
<div style="font-family:'Noto Sans KR',sans-serif; width:280px; background:#161b22;
     border-radius:12px; overflow:hidden; border:1px solid #30363d;">
  <div style="background:{color}22; border-bottom:2px solid {color}; padding:14px 16px;">
    <div style="font-size:14px; font-weight:700; color:#f0f6fc; margin-bottom:2px;">{name}</div>
    <div style="font-size:11px; color:#8b949e;">{addr}</div>
  </div>
  <div style="padding:14px 16px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="font-size:11px; color:#8b949e;">이용률</span>
      <span style="font-size:20px; font-weight:700; color:{color};">{rate:.0f}%</span>
    </div>
    <div style="background:#21262d; border-radius:4px; height:6px; margin-bottom:12px; overflow:hidden;">
      <div style="width:{bar_w}%; height:100%; background:{color}; border-radius:4px;"></div>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-bottom:12px;">
      <div style="background:#21262d; border-radius:8px; padding:8px; text-align:center;">
        <div style="font-size:10px; color:#8b949e; margin-bottom:2px;">전체</div>
        <div style="font-size:16px; font-weight:700; color:#f0f6fc;">{total}</div>
      </div>
      <div style="background:#21262d; border-radius:8px; padding:8px; text-align:center;">
        <div style="font-size:10px; color:#8b949e; margin-bottom:2px;">현재</div>
        <div style="font-size:16px; font-weight:700; color:{color};">{curr}</div>
      </div>
      <div style="background:#21262d; border-radius:8px; padding:8px; text-align:center;">
        <div style="font-size:10px; color:#8b949e; margin-bottom:2px;">가용</div>
        <div style="font-size:16px; font-weight:700; color:#3fb950;">{avail}</div>
      </div>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:12px;">
      <div style="color:#8b949e;">🕐 운영시간</div><div style="color:#c9d1d9; text-align:right;">{ops}</div>
      <div style="color:#8b949e;">💰 기본요금</div><div style="color:#c9d1d9; text-align:right;">{f'{fee:,}원/5분' if fee > 0 else '무료'}</div>
      <div style="color:#8b949e;">📅 일 최대</div><div style="color:#c9d1d9; text-align:right;">{f'{max_fee:,}원' if max_fee > 0 else '-'}</div>
      <div style="color:#8b949e;">📞 전화</div><div style="color:#c9d1d9; text-align:right;">{phone if phone != 'nan' else '-'}</div>
      <div style="color:#8b949e;">🔄 갱신</div><div style="color:#8b949e; text-align:right; font-size:10px;">{upd}</div>
    </div>
    <div style="margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;">
      <span style="background:{color}22; color:{color}; border:1px solid {color}44; border-radius:6px; padding:3px 8px; font-size:11px; font-weight:600;">{status}</span>
      <span style="background:#21262d; color:#8b949e; border-radius:6px; padding:3px 8px; font-size:11px;">{kind}</span>
      <span style="background:#21262d; color:#8b949e; border-radius:6px; padding:3px 8px; font-size:11px;">{paid}</span>
    </div>
  </div>
</div>"""

        icon_html = f"""
<div style="width:34px;height:34px;background:{color};border-radius:50% 50% 50% 0;
  transform:rotate(-45deg);border:2px solid rgba(255,255,255,0.3);
  display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.5);">
  <div style="transform:rotate(45deg);font-size:9px;font-weight:700;color:white;">
    {'P' if avail > 0 else '×'}
  </div>
</div>"""

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>{name}</b><br>이용률 {rate:.0f}% | 가용 {avail}면",
            icon=folium.DivIcon(html=icon_html, icon_size=(34,34), icon_anchor=(17,34)),
        ).add_to(target)

    return m


# ─────────────────────────────────────────
# 데이터 로드 실행
# ─────────────────────────────────────────
with st.spinner("🔄 서울시 실시간 데이터 불러오는 중..."):
    info, rt, gu_rt, gu_info, last_updated = load_data()

GU_LIST = sorted(info["구"].dropna().unique().tolist())


# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🅿️ Seoul ParkMap")
    st.markdown(f"🟢 **LIVE** · {last_updated[11:16]} 기준")
    st.caption("5분마다 자동 갱신")
    st.markdown("---")

    page = st.radio(
        "메뉴",
        ["🗺️ 실시간 지도", "📊 통계 대시보드", "📋 주차장 목록"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**🔍 필터**")
    sel_gu     = st.multiselect("자치구",  GU_LIST,              placeholder="전체 자치구")
    sel_status = st.multiselect("혼잡도",  ["여유","보통","혼잡","만차"], placeholder="전체")
    sel_fee    = st.multiselect("유무료",  ["유료","무료"],       placeholder="전체")

    if "🗺️" in page:
        st.markdown("---")
        st.markdown("**🗺️ 지도 설정**")
        show_clusters = st.toggle("마커 클러스터링", value=True)

    st.markdown("---")
    if st.button("🔄 지금 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("출처: 서울 열린데이터 광장")


def filt(df):
    d = df.copy()
    if sel_gu     and "구"           in d.columns: d = d[d["구"].isin(sel_gu)]
    if sel_fee    and "유무료구분명" in d.columns: d = d[d["유무료구분명"].isin(sel_fee)]
    if sel_status and "혼잡도"       in d.columns: d = d[d["혼잡도"].isin(sel_status)]
    return d


# ─────────────────────────────────────────
# 헤더 + KPI
# ─────────────────────────────────────────
fi = filt(info)
fr = filt(rt)

rt_spots = int(fr["총 주차면"].sum())
rt_curr  = int(fr["현재 주차 차량수"].sum())
rt_avail = int(fr["가용면"].sum())
rt_rate  = round(rt_curr / rt_spots * 100, 1) if rt_spots > 0 else 0

st.markdown(f"""
<div class="park-header">
  <div style="flex:1">
    <div class="park-title">🅿️ Seoul <span>ParkMap</span></div>
    <div class="park-subtitle">서울시 공영주차장 실시간 현황 · 갱신: {last_updated}</div>
  </div>
  <div class="live-badge">● LIVE</div>
  <div class="park-badge">실시간 {len(fr)}개소 연계</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card" style="--kc:#388bfd">
    <div class="kpi-lbl">총 공영주차장</div>
    <div class="kpi-val">{len(fi):,}</div>
    <div class="kpi-sub">개소</div>
  </div>
  <div class="kpi-card" style="--kc:#3fb950">
    <div class="kpi-lbl">현재 가용 면수</div>
    <div class="kpi-val">{rt_avail:,}</div>
    <div class="kpi-sub">면 여유</div>
  </div>
  <div class="kpi-card" style="--kc:#e3b341">
    <div class="kpi-lbl">전체 이용률</div>
    <div class="kpi-val">{rt_rate}%</div>
    <div class="kpi-sub">실시간 연계 기준</div>
  </div>
  <div class="kpi-card" style="--kc:#f85149">
    <div class="kpi-lbl">현재 주차 차량</div>
    <div class="kpi-val">{rt_curr:,}</div>
    <div class="kpi-sub">대</div>
  </div>
</div>
""", unsafe_allow_html=True)


PLOT_CFG = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22,27,34,0.8)",
    font=dict(family="Noto Sans KR", size=12, color="#8b949e"),
    margin=dict(l=10, r=10, t=40, b=10),
)


# ─────────────────────────────────────────
# ① 실시간 지도
# ─────────────────────────────────────────
if "🗺️" in page:
    st.markdown("""
    <div class="legend-row">
      <div class="legend-item"><div class="legend-dot" style="background:#3fb950"></div>여유 (30% 미만)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#388bfd"></div>보통 (30~70%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#e3b341"></div>혼잡 (70~95%)</div>
      <div class="legend-item"><div class="legend-dot" style="background:#f85149"></div>만차 (95% 이상)</div>
      <div class="legend-item" style="margin-left:auto; color:#8b949e; font-size:11px;">📍 핀 클릭 시 상세 정보</div>
    </div>
    """, unsafe_allow_html=True)

    map_col, stat_col = st.columns([3, 1])

    with map_col:
        m = make_map(fr, show_clusters, sel_gu)
        st_folium(m, width="100%", height=560, returned_objects=[], key="main_map")

    with stat_col:
        st.markdown("#### 구별 이용률")
        f_gu_s = (gu_rt[gu_rt["구"].isin(sel_gu)] if sel_gu else gu_rt.copy()).sort_values("이용률", ascending=True)
        fig = go.Figure(go.Bar(
            x=f_gu_s["이용률"], y=f_gu_s["구"], orientation="h",
            marker_color=[status_color(v)[0] for v in f_gu_s["이용률"]],
            marker_line_width=0,
            text=f_gu_s["이용률"].map(lambda v: f"{v:.0f}%"),
            textposition="outside", textfont=dict(size=10, color="#8b949e"),
        ))
        fig.update_layout(
            **PLOT_CFG,
            height=min(540, len(f_gu_s)*26+20),
            xaxis=dict(range=[0,120], gridcolor="#21262d", showticklabels=False, zeroline=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11, color="#c9d1d9")),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🔴 혼잡 주차장 TOP 5")
        top_busy = fr.nlargest(5, "이용률")[["주차장명","구","총 주차면","현재 주차 차량수","이용률","가용면"]].copy()
        top_busy.columns = ["주차장명","구","전체","현재","이용률(%)","가용"]
        st.dataframe(
            top_busy.style.apply(style_util, axis=None)
                .format({"이용률(%)":"{:.1f}","전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}"}),
            use_container_width=True, hide_index=True, height=210,
        )

    with col_b:
        st.markdown("#### 🟢 여유 주차장 TOP 5")
        top_free = fr[fr["이용률"] < 100].nsmallest(5, "이용률")[["주차장명","구","총 주차면","현재 주차 차량수","이용률","가용면"]].copy()
        top_free.columns = ["주차장명","구","전체","현재","이용률(%)","가용"]
        st.dataframe(
            top_free.style.apply(style_util, axis=None)
                .format({"이용률(%)":"{:.1f}","전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}"}),
            use_container_width=True, hide_index=True, height=210,
        )


# ─────────────────────────────────────────
# ② 통계 대시보드
# ─────────────────────────────────────────
elif "📊" in page:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 혼잡도 분포")
        cnt = fr["혼잡도"].value_counts().reindex(["여유","보통","혼잡","만차"], fill_value=0)
        fig = go.Figure(go.Bar(
            x=cnt.index, y=cnt.values,
            marker_color=["#3fb950","#388bfd","#e3b341","#f85149"],
            marker_line_width=0,
            text=cnt.values, textposition="outside", textfont=dict(color="#c9d1d9"),
        ))
        fig.update_layout(**PLOT_CFG, height=260, showlegend=False,
                          yaxis=dict(gridcolor="#21262d", zeroline=False),
                          xaxis=dict(tickfont=dict(color="#c9d1d9")))
        fig.update_traces(width=0.5)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown("#### 주차장 종류 비율")
        vc = fi["주차장 종류명"].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=vc.index, values=vc.values, hole=0.5,
            marker=dict(colors=["#388bfd","#3fb950","#e3b341","#f85149","#bc8cff"]),
            textinfo="label+percent", textfont=dict(size=12),
        ))
        fig2.update_layout(**PLOT_CFG, height=260, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("#### 자치구별 종합 현황")
    merged = pd.merge(gu_info, gu_rt, on="구", how="outer").fillna(0)
    merged["실시간이용률"] = merged.apply(
        lambda r: round(r["현재차량"]/r["총주차면"]*100, 1) if r["총주차면"] > 0 else 0.0, axis=1
    )
    if sel_gu:
        merged = merged[merged["구"].isin(sel_gu)]
    merged = merged.sort_values("실시간이용률", ascending=False)

    disp = merged[["구","전체주차장수","전체주차면","주차장수","총주차면","현재차량","가용면","실시간이용률"]].copy()
    disp.columns = ["자치구","전체 주차장","전체 주차면","실시간 연계","연계 주차면","현재 차량","가용 면수","이용률(%)"]
    st.dataframe(
        disp.style.apply(style_util, axis=None)
            .format({"전체 주차장":"{:,.0f}","전체 주차면":"{:,.0f}","실시간 연계":"{:,.0f}",
                     "연계 주차면":"{:,.0f}","현재 차량":"{:,.0f}","가용 면수":"{:,.0f}","이용률(%)":"{:.1f}"}),
        use_container_width=True, height=460, hide_index=True,
    )

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### 구별 전체 주차면 순위")
        srt = disp.sort_values("전체 주차면", ascending=True)
        fig3 = go.Figure(go.Bar(
            x=srt["전체 주차면"], y=srt["자치구"], orientation="h",
            marker=dict(color=srt["전체 주차면"], colorscale=[[0,"#1c2128"],[1,"#388bfd"]]),
            marker_line_width=0,
            text=srt["전체 주차면"].map(lambda v: f"{int(v):,}"), textposition="outside",
            textfont=dict(size=10, color="#8b949e"),
        ))
        fig3.update_layout(**PLOT_CFG, height=max(340, len(srt)*26+40),
                           xaxis=dict(gridcolor="#21262d", showticklabels=False, zeroline=False),
                           yaxis=dict(tickfont=dict(size=11, color="#c9d1d9")))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col4:
        st.markdown("#### 구별 실시간 이용률")
        srt2 = disp.sort_values("이용률(%)", ascending=True)
        fig4 = go.Figure(go.Bar(
            x=srt2["이용률(%)"], y=srt2["자치구"], orientation="h",
            marker_color=[status_color(v)[0] for v in srt2["이용률(%)"]],
            marker_line_width=0,
            text=srt2["이용률(%)"].map(lambda v: f"{v:.1f}%"), textposition="outside",
            textfont=dict(size=10, color="#8b949e"),
        ))
        fig4.update_layout(**PLOT_CFG, height=max(340, len(srt2)*26+40),
                           xaxis=dict(range=[0,115], gridcolor="#21262d", showticklabels=False, zeroline=False),
                           yaxis=dict(tickfont=dict(size=11, color="#c9d1d9")))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────
# ③ 주차장 목록
# ─────────────────────────────────────────
elif "📋" in page:
    tab1, tab2 = st.tabs(["🔴 실시간 현황 (시영)", "📁 전체 공영주차장"])

    with tab1:
        fr2 = filt(rt)
        c1, c2 = st.columns([2,1])
        with c1:
            search = st.text_input("🔍 주차장명 검색", placeholder="예: 세종로, 종로...", label_visibility="collapsed")
            if search: fr2 = fr2[fr2["주차장명"].str.contains(search, na=False)]
        with c2:
            sort_opt = st.selectbox("정렬", ["이용률 높은 순","이용률 낮은 순","가용면 많은 순"], label_visibility="collapsed")
        sm = {"이용률 높은 순":("이용률",False),"이용률 낮은 순":("이용률",True),"가용면 많은 순":("가용면",False)}
        sc, asc = sm[sort_opt]
        fr2 = fr2.sort_values(by=sc, ascending=asc)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("조회 주차장", f"{len(fr2)}개소")
        mc2.metric("총 주차면",   f"{int(fr2['총 주차면'].sum()):,}면")
        mc3.metric("현재 차량",   f"{int(fr2['현재 주차 차량수'].sum()):,}대")
        mc4.metric("가용 면수",   f"{int(fr2['가용면'].sum()):,}면")

        # 원하는 컬럼과 표시명 쌍으로 관리 — 없는 컬럼은 자동 제외
        cols_want = [
            ("구",                          "구"),
            ("주차장명",                    "주차장명"),
            ("주소",                        "주소"),
            ("총 주차면",                   "전체"),
            ("현재 주차 차량수",            "현재"),
            ("가용면",                      "가용"),
            ("이용률",                      "이용률(%)"),
            ("혼잡도",                      "혼잡도"),
            ("기본 주차 요금",              "기본요금(원)"),
            ("일 최대 요금",                "일최대(원)"),
            ("평일운영",                    "평일운영"),
            ("현재 주차 차량수 업데이트시간","업데이트"),
        ]
        # 실제 존재하는 컬럼만 선택
        cols_rt  = [c for c, _ in cols_want if c in fr2.columns]
        cols_ren = [r for c, r in cols_want if c in fr2.columns]
        # 디버그: 빠진 컬럼 경고
        missing = [c for c, _ in cols_want if c not in fr2.columns]
        if missing:
            st.warning(f"실시간 데이터에 없는 컬럼(자동 제외): {missing}\n실제 컬럼: {fr2.columns.tolist()}")
        disp_rt = fr2[cols_rt].copy()
        disp_rt.columns = cols_ren
        st.dataframe(
            disp_rt.style.apply(style_util, axis=None)
                .format({k: v for k, v in {
                    "전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}",
                    "이용률(%)":"{:.1f}","기본요금(원)":"{:,.0f}","일최대(원)":"{:,.0f}"
                }.items() if k in disp_rt.columns}),
            use_container_width=True, height=480, hide_index=True,
        )
        st.download_button("📥 CSV 다운로드", fr2.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="실시간_주차현황.csv", mime="text/csv")

    with tab2:
        fi2 = filt(info)
        c1, c2 = st.columns([2,1])
        with c1:
            search2 = st.text_input("🔍 주차장명 검색", placeholder="예: 세종로, 종로...", label_visibility="collapsed", key="s2")
            if search2: fi2 = fi2[fi2["주차장명"].str.contains(search2, na=False)]
        with c2:
            sort_opt2 = st.selectbox("정렬", ["주차면 많은 순","기본요금 낮은 순","기본요금 높은 순"], label_visibility="collapsed", key="s2s")
        if sort_opt2 == "주차면 많은 순":    fi2 = fi2.sort_values("총 주차면", ascending=False)
        elif sort_opt2 == "기본요금 낮은 순": fi2 = fi2.sort_values("기본 주차 요금")
        else:                               fi2 = fi2.sort_values("기본 주차 요금", ascending=False)

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("조회 주차장", f"{len(fi2):,}개소")
        mc2.metric("총 주차면",   f"{int(fi2['총 주차면'].sum()):,}면")
        mc3.metric("유료 비율",   f"{round(len(fi2[fi2['유무료구분명']=='유료'])/max(len(fi2),1)*100,1)}%")

        cols_info = ["구","주차장명","주소","주차장 종류명","운영구분명",
                     "총 주차면","유무료구분명","기본 주차 요금","일 최대 요금","월 정기권 금액","전화번호"]
        disp_info = fi2[cols_info].copy()
        disp_info.columns = ["구","주차장명","주소","종류","운영구분","총 주차면","유무료","기본요금(원)","일최대(원)","월정기권(원)","전화번호"]
        st.dataframe(
            disp_info.style.format({"총 주차면":"{:,.0f}","기본요금(원)":"{:,.0f}","일최대(원)":"{:,.0f}","월정기권(원)":"{:,.0f}"}),
            use_container_width=True, height=480, hide_index=True,
        )
        st.download_button("📥 CSV 다운로드", fi2.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="공영주차장_전체목록.csv", mime="text/csv")
