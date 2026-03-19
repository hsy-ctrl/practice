import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="환경·보건 정책 의사결정 시스템",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# 글로벌 스타일 (다크 사이버펑크 테마)
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

/* 전체 배경 */
.stApp {
    background-color: #0a0e1a;
    color: #e8eaf0;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: #0f1629;
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] * {
    color: #e8eaf0 !important;
}

/* 슬라이더 색상 */
[data-testid="stSlider"] > div > div > div > div {
    background-color: #00d4b4 !important;
}

/* 헤더 */
.main-header {
    padding: 8px 0 20px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 24px;
}
.main-title {
    font-size: 28px;
    font-weight: 700;
    color: #e8eaf0;
    letter-spacing: -0.5px;
    line-height: 1.2;
}
.main-title span { color: #00d4b4; }
.main-subtitle {
    font-size: 13px;
    color: #8892a4;
    margin-top: 6px;
}
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    background: rgba(0,212,180,0.12);
    color: #00d4b4;
    border: 1px solid rgba(0,212,180,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    margin-top: 8px;
}

/* KPI 카드 */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}
.kpi-card {
    background: #0f1629;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
}
.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #8892a4;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 24px;
    font-weight: 700;
    color: #e8eaf0;
    line-height: 1;
}
.kpi-delta-pos {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #00d4b4;
    margin-top: 4px;
}
.kpi-delta-neg {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #ff6b6b;
    margin-top: 4px;
}

/* 패널 타이틀 */
.panel-title {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #8892a4;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}

/* 정책 해석 박스 */
.interp-good {
    background: rgba(0,212,180,0.08);
    border: 1px solid rgba(0,212,180,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 13px;
    color: #e8eaf0;
    line-height: 1.6;
}
.interp-warn {
    background: rgba(245,166,35,0.08);
    border: 1px solid rgba(245,166,35,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 13px;
    color: #e8eaf0;
    line-height: 1.6;
}
.interp-bad {
    background: rgba(255,107,107,0.08);
    border: 1px solid rgba(255,107,107,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 13px;
    color: #e8eaf0;
    line-height: 1.6;
}

/* 사이드바 섹션 타이틀 */
.sidebar-section {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #8892a4;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding-bottom: 8px;
    margin: 20px 0 12px;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 공통 Plotly 레이아웃 설정
# ──────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,22,41,0.6)",
    font=dict(family="DM Mono, monospace", color="#8892a4", size=10),
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
)

# ──────────────────────────────────────────
# 데이터 생성
# ──────────────────────────────────────────
np.random.seed(42)
n = 100

data = pd.DataFrame({
    "SOx":        np.random.uniform(0.01, 0.05, n),
    "NOx":        np.random.uniform(0.02, 0.08, n),
    "Car_Usage":  np.random.uniform(30, 80, n),
    "Pop_Density":np.random.uniform(2000, 15000, n),
})
data["Lung_Disease"] = (
    100 + data["NOx"] * 1800 + data["SOx"] * 800
    + np.random.normal(0, 10, n)
)

# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-title" style="font-size:18px;">⚙️ 정책 설정</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">시뮬레이션 파라미터</div>', unsafe_allow_html=True)
    car = st.slider("🚗 자가용 감소율 (%)", 0, 60, 20, step=1)
    nox = st.slider("🌫 NOx 저감율 (%)", 0, 60, 20, step=1)
    thresh = st.slider("⚠️ 고위험 임계값", 140, 220, 180, step=5)

    st.markdown('<div class="sidebar-section">정책 전략</div>', unsafe_allow_html=True)
    policy_type = st.selectbox(
        "전략 선택",
        ["단일 정책", "교통 중심", "통합 정책"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-section">데이터</div>', unsafe_allow_html=True)
    show_table = st.checkbox("원본 데이터 표시", value=False)

# ──────────────────────────────────────────
# 시나리오 계산
# ──────────────────────────────────────────
scenario = data.copy()
_car, _nox = car, nox

if policy_type == "교통 중심":
    _car *= 1.5
elif policy_type == "통합 정책":
    _car *= 1.3
    _nox *= 1.3

scenario["Car_Usage"] *= (1 - _car / 100)
scenario["NOx"]       *= (1 - (_car * 0.3) / 100)
scenario["NOx"]       *= (1 - _nox / 100)
scenario["Lung_Disease"] = 100 + scenario["NOx"] * 1800 + scenario["SOx"] * 800

before_avg  = data["Lung_Disease"].mean()
after_avg   = scenario["Lung_Disease"].mean()
change_pct  = ((before_avg - after_avg) / before_avg) * 100
hr_before   = (data["Lung_Disease"] > thresh).sum()
hr_after    = (scenario["Lung_Disease"] > thresh).sum()

# ──────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div class="main-title">🌍 환경·보건 정책<br><span>의사결정 시스템</span></div>
  <div class="main-subtitle">NOx·SOx 오염 감축이 폐질환 발생에 미치는 정책 시나리오 분석</div>
  <div class="badge">LIVE SIM · v2.0</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# KPI 카드
# ──────────────────────────────────────────
delta_avg  = after_avg - before_avg
delta_hr   = hr_after - hr_before

st.markdown(f"""
<div class="kpi-container">
  <div class="kpi-card" style="--accent:#8892a4">
    <div class="kpi-label">기존 평균</div>
    <div class="kpi-value">{before_avg:.1f}</div>
  </div>
  <div class="kpi-card" style="--accent:#00d4b4">
    <div class="kpi-label">정책 후 평균</div>
    <div class="kpi-value">{after_avg:.1f}</div>
    <div class="{'kpi-delta-pos' if delta_avg <= 0 else 'kpi-delta-neg'}">{delta_avg:+.1f}</div>
  </div>
  <div class="kpi-card" style="--accent:#f5a623">
    <div class="kpi-label">개선율</div>
    <div class="kpi-value">{change_pct:.2f}%</div>
  </div>
  <div class="kpi-card" style="--accent:{'#00d4b4' if hr_after < hr_before else '#ff6b6b'}">
    <div class="kpi-label">고위험 지역</div>
    <div class="kpi-value">{hr_after}</div>
    <div class="{'kpi-delta-pos' if delta_hr <= 0 else 'kpi-delta-neg'}">{delta_hr:+d}</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────
# 1. 분포 비교  +  2. 리스크 구간
# ──────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown('<div class="panel-title">정책 전후 — 폐질환 지수 분포</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(
        x=data["Lung_Disease"], name="이전",
        opacity=0.55, nbinsx=16,
        marker_color="#8892a4",
    ))
    fig1.add_trace(go.Histogram(
        x=scenario["Lung_Disease"], name="이후",
        opacity=0.65, nbinsx=16,
        marker_color="#00d4b4",
    ))
    fig1.update_layout(
        **PLOT_LAYOUT,
        barmode="overlay",
        height=260,
        legend=dict(font=dict(color="#8892a4", size=10), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown('<div class="panel-title">리스크 구간 분포</div>', unsafe_allow_html=True)
    low  = (scenario["Lung_Disease"] <= 140).sum()
    med  = ((scenario["Lung_Disease"] > 140) & (scenario["Lung_Disease"] <= thresh)).sum()
    high = (scenario["Lung_Disease"] > thresh).sum()

    fig2 = go.Figure(go.Bar(
        x=["저위험", "중위험", "고위험"],
        y=[low, med, high],
        marker_color=["#00d4b4", "#f5a623", "#ff6b6b"],
        marker_line_width=0,
    ))
    fig2.update_layout(**PLOT_LAYOUT, height=260, showlegend=False)
    fig2.update_traces(width=0.5)
    st.plotly_chart(fig2, use_container_width=True)

# ──────────────────────────────────────────
# 3. 민감도 분석  +  4. 버블 산점도
# ──────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="panel-title">NOx ↔ 폐질환 민감도</div>', unsafe_allow_html=True)
    xs  = np.linspace(0.02, 0.08, 60)
    ys  = 100 + xs * 1800
    cur = scenario["NOx"].mean()

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color="#4a90e2", width=2),
        fill="tozeroy", fillcolor="rgba(74,144,226,0.08)",
        name="예측 곡선",
    ))
    fig3.add_trace(go.Scatter(
        x=[cur], y=[100 + cur * 1800],
        mode="markers",
        marker=dict(color="#f5a623", size=10, symbol="circle"),
        name="현재 NOx",
    ))
    fig3.update_layout(**PLOT_LAYOUT, height=240,
        legend=dict(font=dict(color="#8892a4", size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis_title="NOx 농도", yaxis_title="폐질환 지수",
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown('<div class="panel-title">다변수 영향 분석 — NOx × 폐질환 × 인구밀도</div>', unsafe_allow_html=True)
    colors = scenario["Lung_Disease"].apply(
        lambda v: "#ff6b6b" if v > thresh else ("#f5a623" if v > 140 else "#00d4b4")
    )
    fig4 = go.Figure(go.Scatter(
        x=scenario["NOx"],
        y=scenario["Lung_Disease"],
        mode="markers",
        marker=dict(
            size=scenario["Pop_Density"] / 1000,
            color=colors,
            opacity=0.65,
            line=dict(width=0),
        ),
        text=scenario["SOx"].map(lambda v: f"SOx: {v:.3f}"),
        hovertemplate="NOx: %{x:.4f}<br>폐질환: %{y:.1f}<br>%{text}<extra></extra>",
    ))
    fig4.update_layout(**PLOT_LAYOUT, height=240,
        xaxis_title="NOx 농도", yaxis_title="폐질환 지수",
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ──────────────────────────────────────────
# 5. 정책 해석
# ──────────────────────────────────────────
if change_pct > 15:
    css_cls = "interp-good"
    icon, headline = "✅", "강력한 정책 효과"
elif change_pct > 5:
    css_cls = "interp-warn"
    icon, headline = "⚠️", "중간 수준 효과"
else:
    css_cls = "interp-bad"
    icon, headline = "❌", "효과 미미"

st.markdown(f"""
<div class="{css_cls}">
  {icon} <strong>{headline}</strong> — 폐질환 평균 <strong>{change_pct:.2f}%</strong> 감소.
  고위험 지역 <strong>{hr_before}곳 → {hr_after}곳</strong> (임계값 {thresh} 기준).<br>
  <span style="font-size:12px;opacity:.75">
    NOx 저감이 주요 기여 요인 · 자가용 정책은 간접 효과 중심 · 정책 전략: <strong>{policy_type}</strong>
  </span>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 6. 원본 데이터 (선택)
# ──────────────────────────────────────────
if show_table:
    st.markdown("---")
    st.markdown('<div class="panel-title">시나리오 데이터</div>', unsafe_allow_html=True)
    st.dataframe(
        scenario.style.background_gradient(subset=["Lung_Disease"], cmap="RdYlGn_r"),
        use_container_width=True,
        height=300,
    )
    st.download_button(
        "📥 CSV 다운로드",
        scenario.to_csv(index=False),
        file_name="policy_simulation.csv",
        mime="text/csv",
    )
