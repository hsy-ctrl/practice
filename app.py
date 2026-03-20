import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import st_folium
from pathlib import Path

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

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] .stMarkdown h3 { color: #58a6ff !important; }
[data-testid="stSidebar"] hr { border-color: #30363d !important; }

/* 헤더 */
.park-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.park-title { font-size: 28px; font-weight: 700; color: #f0f6fc; letter-spacing: -0.5px; }
.park-title span { color: #58a6ff; }
.park-subtitle { font-size: 13px; color: #8b949e; margin-top: 3px; }
.park-badge {
    font-size: 11px; font-weight: 600;
    background: rgba(88,166,255,0.1);
    color: #58a6ff;
    border: 1px solid rgba(88,166,255,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    white-space: nowrap;
}

/* KPI 카드 */
.kpi-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 16px; }
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 14px 16px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s;
}
.kpi-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: var(--kc);
}
.kpi-card:hover { border-color: #58a6ff; }
.kpi-lbl { font-size:10px; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }
.kpi-val { font-size:24px; font-weight:700; color:#f0f6fc; line-height:1; }
.kpi-sub { font-size:11px; color:#8b949e; margin-top:4px; }

/* 범례 */
.legend-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
.legend-item { display:flex; align-items:center; gap:6px; font-size:12px; color:#c9d1d9; }
.legend-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

/* 상세 패널 */
.detail-panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 20px;
    height: 100%;
}
.detail-title { font-size:16px; font-weight:600; color:#f0f6fc; margin-bottom:4px; }
.detail-addr  { font-size:12px; color:#8b949e; margin-bottom:16px; }
.gauge-wrap   { margin:12px 0; }
.gauge-label  { display:flex; justify-content:space-between; font-size:12px; color:#8b949e; margin-bottom:4px; }
.gauge-track  { background:#21262d; border-radius:4px; height:8px; overflow:hidden; }
.gauge-fill   { height:100%; border-radius:4px; transition: width .4s; }
.info-grid    { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:14px; }
.info-box     { background:#21262d; border-radius:8px; padding:10px 12px; }
.info-box-lbl { font-size:10px; color:#8b949e; text-transform:uppercase; letter-spacing:.8px; margin-bottom:3px; }
.info-box-val { font-size:15px; font-weight:600; color:#f0f6fc; }
.status-badge { display:inline-block; border-radius:6px; padding:3px 10px; font-size:12px; font-weight:600; }

/* 탭 */
[data-baseweb="tab-list"] { background: #161b22 !important; border-radius:10px; gap:4px; }
[data-baseweb="tab"] { color:#8b949e !important; border-radius:8px !important; }
[aria-selected="true"][data-baseweb="tab"] { background:#21262d !important; color:#58a6ff !important; }

/* 구별 테이블 */
.gu-table { width:100%; border-collapse:collapse; font-size:13px; }
.gu-table th { background:#21262d; color:#8b949e; font-weight:500; padding:8px 12px; text-align:left; border-bottom:1px solid #30363d; }
.gu-table td { padding:8px 12px; border-bottom:1px solid #21262d; color:#c9d1d9; }
.gu-table tr:hover td { background:#1c2128; }

/* dataframe 다크 */
[data-testid="stDataFrame"] { background:#161b22 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# CSV 경로
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent

def find_csv(name):
    for n in [name, name.replace("_", " ")]:
        p = BASE_DIR / n
        if p.exists():
            return p
    return None

INFO_CSV = find_csv("서울시_공영주차장_안내_정보.csv")
RT_CSV   = find_csv("서울시_시영주차장_실시간_주차대수_정보.csv")

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
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    if INFO_CSV is None or RT_CSV is None:
        st.error("CSV 파일을 app.py와 같은 폴더에 넣어주세요.")
        st.stop()

    info = pd.read_csv(INFO_CSV, encoding="euc-kr")
    rt   = pd.read_csv(RT_CSV,   encoding="euc-kr")

    info["구"] = info["주소"].str.extract(r"([\w]+구)")
    rt["구"]   = rt["주소"].str.extract(r"([\w]+구)")

    for col in ["총 주차면","기본 주차 요금","기본 주차 시간(분 단위)",
                "추가 단위 요금","추가 단위 시간(분 단위)","일 최대 요금","월 정기권 금액","위도","경도"]:
        if col in info.columns:
            info[col] = pd.to_numeric(info[col], errors="coerce")

    # 실시간 — 이상치 제거
    rt = rt[rt["총 주차면"] > 10].copy()
    for col in ["기본 주차 요금","일 최대 요금"]:
        if col in rt.columns:
            rt[col] = pd.to_numeric(rt[col], errors="coerce").fillna(0)

    rt["이용률"] = (rt["현재 주차 차량수"] / rt["총 주차면"] * 100).round(1).clip(0, 100)
    rt["가용면"] = (rt["총 주차면"] - rt["현재 주차 차량수"]).clip(lower=0)
    rt["혼잡도"] = pd.cut(
        rt["이용률"], bins=[-1,30,70,95,100],
        labels=["여유","보통","혼잡","만차"]
    ).astype(str)

    # 실시간 데이터에 구별 좌표 랜덤 배치 (위경도 없으므로)
    rng = np.random.default_rng(42)
    lats, lngs = [], []
    for _, row in rt.iterrows():
        gu = row["구"]
        if gu in GU_COORDS:
            blat, blng = GU_COORDS[gu]
            lats.append(blat + rng.uniform(-0.018, 0.018))
            lngs.append(blng + rng.uniform(-0.018, 0.018))
        else:
            lats.append(37.5665)
            lngs.append(126.9780)
    rt["위도"] = lats
    rt["경도"] = lngs

    # 운영시간 포맷
    def fmt_time(v):
        try:
            v = int(v)
            if v == 0 or v == 2400: return "00:00"
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

    return info, rt, gu_rt, gu_info


info, rt, gu_rt, gu_info = load_data()

GU_LIST     = sorted(info["구"].dropna().unique().tolist())
UPDATE_TIME = rt["현재 주차 차량수 업데이트시간"].iloc[0] if len(rt) > 0 else "-"


# ─────────────────────────────────────────
# 색상 헬퍼
# ─────────────────────────────────────────
def status_color(rate):
    if rate >= 95: return "#f85149", "만차"
    if rate >= 70: return "#e3b341", "혼잡"
    if rate >= 30: return "#388bfd", "보통"
    return "#3fb950", "여유"

def color_utilization(val):
    try:
        v = float(val)
    except: return ""
    if v >= 95: return "background-color:#3d1a1a; color:#f85149;"
    if v >= 70: return "background-color:#2d2200; color:#e3b341;"
    if v >= 30: return "background-color:#0d2340; color:#388bfd;"
    return "background-color:#0d2d1a; color:#3fb950;"

def style_util(df, col="이용률(%)"):
    s = pd.DataFrame("", index=df.index, columns=df.columns)
    if col in df.columns:
        s[col] = df[col].map(color_utilization)
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

    if show_clusters:
        cluster = MarkerCluster(
            options={"maxClusterRadius": 50, "disableClusteringAtZoom": 14}
        )
        cluster.add_to(m)
        target = cluster
    else:
        target = m

    for _, row in df.iterrows():
        try:
            lat, lng = float(row["위도"]), float(row["경도"])
        except: continue

        rate = float(row.get("이용률", 0))
        avail = int(row.get("가용면", 0))
        total = int(row.get("총 주차면", 0))
        curr  = int(row.get("현재 주차 차량수", 0))
        color, status = status_color(rate)
        fee   = int(row.get("기본 주차 요금", 0))
        max_fee = int(row.get("일 최대 요금", 0))
        ops   = row.get("평일운영", "-")
        name  = row.get("주차장명", "")
        addr  = row.get("주소", "")
        paid  = row.get("유무료구분명", "-")
        phone = row.get("전화번호", "-")
        gu    = row.get("구", "-")
        kind  = row.get("주차장 종류명", "-")

        # 게이지 바 HTML
        bar_w = min(int(rate), 100)
        popup_html = f"""
<div style="font-family:'Noto Sans KR',sans-serif; width:280px; background:#161b22;
     border-radius:12px; padding:0; overflow:hidden; border:1px solid #30363d;">

  <div style="background:{color}22; border-bottom:2px solid {color};
       padding:14px 16px;">
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
      <div style="color:#8b949e;">🕐 운영시간</div>
      <div style="color:#c9d1d9; text-align:right;">{ops}</div>
      <div style="color:#8b949e;">💰 기본요금</div>
      <div style="color:#c9d1d9; text-align:right;">{f'{fee:,}원/5분' if fee > 0 else '무료'}</div>
      <div style="color:#8b949e;">📅 일 최대</div>
      <div style="color:#c9d1d9; text-align:right;">{f'{max_fee:,}원' if max_fee > 0 else '-'}</div>
      <div style="color:#8b949e;">📞 전화</div>
      <div style="color:#c9d1d9; text-align:right;">{str(phone) if str(phone) != 'nan' else '-'}</div>
    </div>

    <div style="margin-top:10px; display:flex; gap:6px;">
      <span style="background:{color}22; color:{color}; border:1px solid {color}44;
            border-radius:6px; padding:3px 8px; font-size:11px; font-weight:600;">{status}</span>
      <span style="background:#21262d; color:#8b949e;
            border-radius:6px; padding:3px 8px; font-size:11px;">{kind}</span>
      <span style="background:#21262d; color:#8b949e;
            border-radius:6px; padding:3px 8px; font-size:11px;">{paid}</span>
    </div>
  </div>
</div>
"""
        # 마커 아이콘 (DivIcon)
        icon_html = f"""
<div style="
  width:34px; height:34px;
  background:{color};
  border-radius:50% 50% 50% 0;
  transform:rotate(-45deg);
  border:2px solid rgba(255,255,255,0.3);
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 2px 8px rgba(0,0,0,0.5);
">
  <div style="transform:rotate(45deg); font-size:9px; font-weight:700;
       color:white; text-shadow:0 1px 2px rgba(0,0,0,0.5);">
    {'P' if avail > 0 else '×'}
  </div>
</div>"""

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=300, parse_html=False),
            tooltip=f"<b>{name}</b><br>이용률 {rate:.0f}% | 가용 {avail}면",
            icon=folium.DivIcon(html=icon_html, icon_size=(34,34), icon_anchor=(17,34)),
        ).add_to(target)

    return m


# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🅿️ Seoul ParkMap")
    st.caption(f"📡 {UPDATE_TIME[:16]} 기준")
    st.markdown("---")

    page = st.radio(
        "메뉴",
        ["🗺️ 실시간 지도", "📊 통계 대시보드", "📋 주차장 목록"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**🔍 필터**")

    sel_gu = st.multiselect("자치구", GU_LIST, placeholder="전체 자치구")

    sel_status = st.multiselect(
        "혼잡도",
        ["여유","보통","혼잡","만차"],
        placeholder="전체",
    )

    sel_fee = st.multiselect("유무료", ["유료","무료"], placeholder="전체")

    if "🗺️" in page:
        st.markdown("---")
        st.markdown("**🗺️ 지도 설정**")
        show_clusters = st.toggle("마커 클러스터링", value=True)

    st.markdown("---")
    st.caption("출처: 서울 열린데이터 광장")


def filt(df):
    d = df.copy()
    if sel_gu   and "구"           in d.columns: d = d[d["구"].isin(sel_gu)]
    if sel_fee  and "유무료구분명" in d.columns: d = d[d["유무료구분명"].isin(sel_fee)]
    if sel_status and "혼잡도"     in d.columns: d = d[d["혼잡도"].isin(sel_status)]
    return d


# ─────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────
fi = filt(info)
fr = filt(rt)

rt_spots = int(fr["총 주차면"].sum())
rt_curr  = int(fr["현재 주차 차량수"].sum())
rt_avail = int(fr["가용면"].sum())
rt_rate  = round(rt_curr / rt_spots * 100, 1) if rt_spots > 0 else 0
_, status_label = status_color(rt_rate)

st.markdown(f"""
<div class="park-header">
  <div style="flex:1">
    <div class="park-title">🅿️ Seoul <span>ParkMap</span></div>
    <div class="park-subtitle">서울시 공영주차장 실시간 현황 · {UPDATE_TIME[:16]}</div>
  </div>
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


# ─────────────────────────────────────────
# ① 실시간 지도
# ─────────────────────────────────────────
if "🗺️" in page:

    # 범례
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
        map_data = st_folium(
            m,
            width="100%",
            height=560,
            returned_objects=["last_object_clicked_popup"],
            key="main_map",
        )

    with stat_col:
        # 구별 이용률 미니 차트
        st.markdown("#### 구별 이용률")
        f_gu = gu_rt[gu_rt["구"].isin(sel_gu)] if sel_gu else gu_rt.copy()
        f_gu_s = f_gu.sort_values("이용률", ascending=True)

        bar_colors = [status_color(v)[0] for v in f_gu_s["이용률"]]
        fig = go.Figure(go.Bar(
            x=f_gu_s["이용률"], y=f_gu_s["구"], orientation="h",
            marker_color=bar_colors, marker_line_width=0,
            text=f_gu_s["이용률"].map(lambda v: f"{v:.0f}%"),
            textposition="outside",
            textfont=dict(size=10, color="#8b949e"),
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22,27,34,0.8)",
            font=dict(family="Noto Sans KR", size=11, color="#8b949e"),
            margin=dict(l=0, r=40, t=10, b=10),
            height=min(540, len(f_gu_s) * 26 + 20),
            xaxis=dict(range=[0,120], gridcolor="#21262d", showticklabels=False, zeroline=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11, color="#c9d1d9")),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 혼잡 TOP5 / 여유 TOP5
    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🔴 혼잡 주차장 TOP 5")
        top_busy = fr.nlargest(5, "이용률")[["주차장명","구","총 주차면","현재 주차 차량수","이용률","가용면"]]
        top_busy.columns = ["주차장명","구","전체","현재","이용률(%)","가용"]
        st.dataframe(
            top_busy.style
                .apply(style_util, axis=None)
                .format({"이용률(%)":"{:.1f}","전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}"}),
            use_container_width=True, hide_index=True, height=210,
        )

    with col_b:
        st.markdown("#### 🟢 여유 주차장 TOP 5")
        top_free = fr.nsmallest(5, "이용률")[["주차장명","구","총 주차면","현재 주차 차량수","이용률","가용면"]]
        top_free.columns = ["주차장명","구","전체","현재","이용률(%)","가용"]
        st.dataframe(
            top_free.style
                .apply(style_util, axis=None)
                .format({"이용률(%)":"{:.1f}","전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}"}),
            use_container_width=True, hide_index=True, height=210,
        )


# ─────────────────────────────────────────
# ② 통계 대시보드
# ─────────────────────────────────────────
elif "📊" in page:

    col1, col2 = st.columns(2)

    PLOT_CFG = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22,27,34,0.8)",
        font=dict(family="Noto Sans KR", size=12, color="#8b949e"),
        margin=dict(l=10, r=10, t=40, b=10),
    )

    with col1:
        st.markdown("#### 혼잡도 분포")
        cnt = fr["혼잡도"].value_counts().reindex(["여유","보통","혼잡","만차"], fill_value=0)
        colors = ["#3fb950","#388bfd","#e3b341","#f85149"]
        fig = go.Figure(go.Bar(
            x=cnt.index, y=cnt.values,
            marker_color=colors, marker_line_width=0,
            text=cnt.values, textposition="outside",
            textfont=dict(color="#c9d1d9"),
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
            textinfo="label+percent",
            textfont=dict(size=12),
        ))
        fig2.update_layout(**PLOT_CFG, height=260, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # 구별 종합 현황
    st.markdown("#### 자치구별 종합 현황")
    merged = pd.merge(gu_info, gu_rt, on="구", how="outer").fillna(0)
    merged["실시간이용률"] = merged.apply(
        lambda r: round(r["현재차량"] / r["총주차면"] * 100, 1) if r["총주차면"] > 0 else 0.0, axis=1
    )
    if sel_gu:
        merged = merged[merged["구"].isin(sel_gu)]
    merged = merged.sort_values("실시간이용률", ascending=False)

    disp = merged[["구","전체주차장수","전체주차면","주차장수","총주차면","현재차량","가용면","실시간이용률"]].copy()
    disp.columns = ["자치구","전체 주차장","전체 주차면","실시간 연계","연계 주차면","현재 차량","가용 면수","이용률(%)"]
    st.dataframe(
        disp.style
            .apply(style_util, axis=None)
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
            marker=dict(
                color=srt["전체 주차면"],
                colorscale=[[0,"#1c2128"],[1,"#388bfd"]],
            ),
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
            if search:
                fr2 = fr2[fr2["주차장명"].str.contains(search, na=False)]
        with c2:
            sort_opt = st.selectbox("정렬", ["이용률 높은 순","이용률 낮은 순","가용면 많은 순"], label_visibility="collapsed")

        sm = {"이용률 높은 순":("이용률",False),"이용률 낮은 순":("이용률",True),"가용면 많은 순":("가용면",False)}
        sc, asc = sm[sort_opt]
        fr2 = fr2.sort_values(sc, ascending=asc)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("조회 주차장", f"{len(fr2)}개소")
        mc2.metric("총 주차면",   f"{int(fr2['총 주차면'].sum()):,}면")
        mc3.metric("현재 차량",   f"{int(fr2['현재 주차 차량수'].sum()):,}대")
        mc4.metric("가용 면수",   f"{int(fr2['가용면'].sum()):,}면")

        cols_rt = ["구","주차장명","주소","총 주차면","현재 주차 차량수",
                   "가용면","이용률","혼잡도","기본 주차 요금","일 최대 요금","평일운영"]
        disp_rt = fr2[cols_rt].copy()
        disp_rt.columns = ["구","주차장명","주소","전체","현재","가용","이용률(%)","혼잡도","기본요금(원)","일최대(원)","평일운영"]

        st.dataframe(
            disp_rt.style
                .apply(style_util, axis=None)
                .format({"전체":"{:,.0f}","현재":"{:,.0f}","가용":"{:,.0f}",
                         "이용률(%)":"{:.1f}","기본요금(원)":"{:,.0f}","일최대(원)":"{:,.0f}"}),
            use_container_width=True, height=480, hide_index=True,
        )
        st.download_button("📥 CSV 다운로드", fr2.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="실시간_주차현황.csv", mime="text/csv")

    with tab2:
        fi2 = filt(info)

        c1, c2 = st.columns([2,1])
        with c1:
            search2 = st.text_input("🔍 주차장명 검색", placeholder="예: 세종로, 종로...", label_visibility="collapsed", key="s2")
            if search2:
                fi2 = fi2[fi2["주차장명"].str.contains(search2, na=False)]
        with c2:
            sort_opt2 = st.selectbox("정렬", ["주차면 많은 순","기본요금 낮은 순","기본요금 높은 순"], label_visibility="collapsed", key="s2s")

        if sort_opt2 == "주차면 많은 순":   fi2 = fi2.sort_values("총 주차면", ascending=False)
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
            disp_info.style.format({
                "총 주차면":"{:,.0f}","기본요금(원)":"{:,.0f}",
                "일최대(원)":"{:,.0f}","월정기권(원)":"{:,.0f}",
            }),
            use_container_width=True, height=480, hide_index=True,
        )
        st.download_button("📥 CSV 다운로드", fi2.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="공영주차장_전체목록.csv", mime="text/csv")
