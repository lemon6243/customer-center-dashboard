# -*- coding: utf-8 -*-
"""
예스코 도시가스 고객센터 성과 대시보드 (Streamlit Application)
- AI Studio React 프리뷰와 100% 동일한 고급 카드, 레이더 차트, 지표 테이블, 슬라이더 디자인 구현
"""
import streamlit as st
import pandas as pd
import json
import os
import math
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 테마
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="예스코 고객센터 성과 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 럭셔리 비즈니스 UI (AI Studio 디자인과 100% 동일한 컬러 및 카드 스타일)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Banner Header */
    .yesco-header-banner {
        background: linear-gradient(135deg, #0B4EA2 0%, #073874 100%);
        color: white;
        padding: 20px 26px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(11, 78, 162, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .header-title-box h1 {
        margin: 0;
        font-size: 21px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF !important;
    }
    .header-title-box p {
        margin: 4px 0 0 0;
        font-size: 12px;
        color: #DBEAFE !important;
        opacity: 0.95;
    }
    .header-badge-box {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .badge-pill-header {
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #FFFFFF !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    
    /* Notice Banner */
    .banner-notice {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 18px;
        color: #1E3A8A;
        font-size: 12.5px;
        line-height: 1.6;
    }
    
    /* Center Detail Header Card */
    .center-header-card {
        background: #FFFFFF;
        border: 1px solid #DCE3EA;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 14px;
    }
    
    .center-stat-pill {
        padding: 8px 14px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        background: #F8FAFC;
        text-align: center;
        min-width: 100px;
    }
    .center-stat-pill.primary {
        background: #EFF6FF;
        border-color: #BFDBFE;
    }
    .center-stat-pill .label {
        font-size: 10px;
        font-weight: 600;
        color: #5E6C84;
        margin-bottom: 2px;
    }
    .center-stat-pill .val {
        font-size: 16px;
        font-weight: 800;
        color: #0B4EA2;
    }
    
    /* KPI Card Boxes */
    .studio-card {
        background: #FFFFFF;
        border: 1px solid #DCE3EA;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 16px;
    }
    .studio-card-title {
        font-size: 14px;
        font-weight: 700;
        color: #172B4D;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .studio-card-desc {
        font-size: 11.5px;
        color: #5E6C84;
        margin-bottom: 14px;
    }
    
    /* Custom Table Style */
    .kpi-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .kpi-table th {
        background: #F8FAFC;
        color: #5E6C84;
        font-weight: 700;
        padding: 9px 12px;
        border-top: 1px solid #DCE3EA;
        border-bottom: 1px solid #DCE3EA;
        text-align: left;
    }
    .kpi-table td {
        padding: 9px 12px;
        border-bottom: 1px solid #EEF2F6;
        color: #1E293B;
    }
    .kpi-table tr.total-row {
        background: #F8FAFC;
        font-weight: 800;
    }
    .kpi-table tr.total-row td {
        border-top: 2px solid #CBD5E1;
        border-bottom: 2px solid #CBD5E1;
        color: #0B4EA2;
    }
    
    /* Simulator Summary Bar */
    .sim-result-bar {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    
    /* Metric Grid Cards for Home */
    .metric-grid-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        border-left: 4px solid #0B4EA2;
        margin-bottom: 14px;
    }
    .metric-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748B;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 11px;
        margin-top: 4px;
        font-weight: 600;
    }
    
    /* Insight Cards */
    .insight-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0B4EA2;
    }
    .insight-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .insight-title {
        font-size: 13px;
        font-weight: 700;
        color: #0F172A;
    }
    .insight-body {
        font-size: 12px;
        color: #475569;
        line-height: 1.5;
    }
    .insight-pill {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 12px;
    }
    .insight-success { border-left-color: #10B981; }
    .insight-success .insight-pill { background: #DCFCE7; color: #15803D; }
    .insight-warning { border-left-color: #F59E0B; }
    .insight-warning .insight-pill { background: #FEF3C7; color: #B45309; }
    .insight-info { border-left-color: #3B82F6; }
    .insight-info .insight-pill { background: #DBEAFE; color: #1D4ED8; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 처리 및 점수 산출 로직
# -----------------------------------------------------------------------------
def normalize_date_string(val):
    if val is None or pd.isna(val):
        return '2026-08-01'
    if isinstance(val, (int, float)):
        if 30000 < val < 70000:
            dt = datetime(1899, 12, 30) + timedelta(days=float(val))
            return dt.strftime('%Y-%m-%d')
        s = str(int(val))
        if len(s) == 6:
            return f"{s[:4]}-{s[4:6]}-01"
        return s
    s = str(val).strip()
    if s.isdigit() and len(s) == 5:
        dt = datetime(1899, 12, 30) + timedelta(days=float(s))
        return dt.strftime('%Y-%m-%d')
    if len(s) >= 7 and s[:4].isdigit():
        parts = s.replace('/', '-').replace('.', '-').split('-')
        y = parts[0]
        m = parts[1].zfill(2)
        d = parts[2].zfill(2) if len(parts) > 2 else '01'
        return f"{y}-{m}-{d}"
    return '2026-08-01'

def calc_contract_score(contract_rate):
    if contract_rate >= 80:
        return 50.0
    elif contract_rate >= 75:
        return 40.0
    elif contract_rate >= 70:
        return 30.0
    elif contract_rate >= 60:
        return 20.0
    else:
        return 10.0

def predict_half_end_score(total_score, cur_month, safety_score, non_cum_score, key_score):
    month_in_half = cur_month if cur_month <= 6 else cur_month - 6
    if month_in_half >= 6:
        return total_score
    rem_months = 6 - month_in_half
    rem_safety_gain = max(0.0, 550.0 - safety_score)
    step_safety = rem_safety_gain / rem_months if rem_months > 0 else 0.0
    rem_key_gain = max(0.0, 100.0 - key_score)
    step_key = rem_key_gain / rem_months if rem_months > 0 else 0.0
    sim_pred = total_score + (step_safety * rem_months * 0.95) + (step_key * rem_months * 0.95)
    return min(1000.0, sim_pred)

@st.cache_data
def load_all_records():
    json_path = os.path.join(os.path.dirname(__file__), 'src', 'data', 'latest_data.json')
    if not os.path.exists(json_path):
        json_path = 'src/data/latest_data.json'
    if not os.path.exists(json_path):
        st.error("데이터 파일(src/data/latest_data.json)을 찾을 수 없습니다.")
        st.stop()
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    df = pd.DataFrame(raw_data)
    df['정규평가월'] = df['평가월'].apply(normalize_date_string)
    df['평가연월'] = df['정규평가월'].str.slice(0, 7)
    df['연도'] = df['정규평가월'].apply(lambda x: int(x[:4]))
    df['월'] = df['정규평가월'].apply(lambda x: int(x[5:7]))
    df['반기'] = df['월'].apply(lambda m: '상반기' if m <= 6 else '하반기')
    df['반기월차'] = df['월'].apply(lambda m: m if m <= 6 else m - 6)

    # 점수 산출
    df['안전점검실점검율'] = pd.to_numeric(df.get('안전점검실점검율', 0), errors='coerce').fillna(0)
    df['중점고객안전점검율'] = pd.to_numeric(df.get('중점고객안전점검율', 0), errors='coerce').fillna(0)
    df['사용계약율'] = pd.to_numeric(df.get('사용계약율', 0), errors='coerce').fillna(0)
    df['상담응대율'] = pd.to_numeric(df.get('상담응대율', 0), errors='coerce').fillna(0)
    df['상담기여도'] = pd.to_numeric(df.get('상담기여도', 0), errors='coerce').fillna(0)
    df['고객서비스만족도'] = pd.to_numeric(df.get('고객서비스만족도', 0), errors='coerce').fillna(0)

    df['안전점검_점수'] = (df['안전점검실점검율'] / 100.0) * 550.0
    df['중점고객_점수'] = (df['중점고객안전점검율'] / 100.0) * 100.0
    df['사용계약_점수'] = df['사용계약율'].apply(calc_contract_score)
    df['상담응대_점수'] = (df['상담응대율'] / 100.0) * 100.0
    df['상담기여_점수'] = (df['상담기여도'] / 100.0) * 100.0
    df['만족도_점수'] = df['고객서비스만족도']

    df['총점'] = (
        df['안전점검_점수'] +
        df['중점고객_점수'] +
        df['사용계약_점수'] +
        df['상담응대_점수'] +
        df['상담기여_점수'] +
        df['만족도_점수']
    )

    # 반기말 예상 점수
    def calc_pred(row):
        non_cum = row['사용계약_점수'] + row['상담응대_점수'] + row['상담기여_점수'] + row['만족도_점수']
        return predict_half_end_score(row['총점'], row['월'], row['안전점검_점수'], non_cum, row['중점고객_점수'])

    df['예상반기총점'] = df.apply(calc_pred, axis=1)

    # 911점 도달 판정
    def get_status(pred):
        if pred >= 911.0:
            return '정상궤도'
        elif pred >= 905.0:
            return '주의'
        else:
            return '위험'
    df['도달판정'] = df['예상반기총점'].apply(get_status)

    return df

df_all = load_all_records()

# 전년 동월 및 전년 반기말 매핑
def map_prior_year_data(df):
    prior_map_same_month = {}
    prior_map_half_end = {}
    for _, r in df.iterrows():
        c_name = r['센터명']
        y = r['연도']
        m = r['월']
        key_sm = f"{c_name}_{y}_{m}"
        prior_map_same_month[key_sm] = r['총점']
        if m in [6, 12]:
            half = '상반기' if m == 6 else '하반기'
            key_he = f"{c_name}_{y}_{half}"
            prior_map_half_end[key_he] = r['총점']

    yoy_diffs = []
    prev_totals = []
    prev_half_ends = []
    for _, r in df.iterrows():
        c_name = r['센터명']
        prev_y = r['연도'] - 1
        m = r['월']
        half = r['반기']
        key_sm = f"{c_name}_{prev_y}_{m}"
        key_he = f"{c_name}_{prev_y}_{half}"
        prev_sc = prior_map_same_month.get(key_sm, None)
        prev_totals.append(prev_sc)
        if prev_sc is not None:
            yoy_diffs.append(r['총점'] - prev_sc)
        else:
            yoy_diffs.append(None)
        prev_he = prior_map_half_end.get(key_he, None)
        prev_half_ends.append(prev_he)

    df['전년동월_총점'] = prev_totals
    df['전년동월대비_증감'] = yoy_diffs
    df['전년반기말_총점'] = prev_half_ends
    return df

df_all = map_prior_year_data(df_all)

# -----------------------------------------------------------------------------
# 3. 사이드바 네비게이션 및 평가월 선택 (최신월 자동 디폴트)
# -----------------------------------------------------------------------------
all_months = sorted(list(df_all['평가연월'].unique()))
latest_month = all_months[-1] if all_months else "2026-08"

# 사이드바 상단 로고 및 브랜딩
st.sidebar.markdown("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:18px; padding-bottom:12px; border-bottom:1px solid #E2E8F0;">
    <div style="background:#0B4EA2; color:white; width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:16px;">
        Y
    </div>
    <div>
        <div style="font-size:14px; font-weight:800; color:#0B4EA2; line-height:1.2;">예스코 고객센터</div>
        <div style="font-size:11px; color:#64748B;">성과 평가 관리 시스템</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 최신월 기본 선택
default_idx = len(all_months) - 1
month_display_map = {m: f"{m} (★최신)" if m == latest_month else m for m in all_months}

selected_month = st.sidebar.selectbox(
    "📅 평가월 선택",
    options=all_months,
    index=default_idx,
    format_func=lambda m: month_display_map.get(m, m)
)

# 현재 선택된 월 데이터 필터링
cur_df = df_all[df_all['평가연월'] == selected_month].copy()
if cur_df.empty:
    cur_df = df_all.copy()

cur_year = cur_df['연도'].iloc[0]
cur_month = cur_df['월'].iloc[0]
half_name = "상반기" if cur_month <= 6 else "하반기"
month_in_half = cur_month if cur_month <= 6 else cur_month - 6
target_end_text = "6월말" if cur_month <= 6 else "12월말"
progress_pct = int((month_in_half / 6) * 100)
benchmark_safety = (month_in_half / 6) * 100.0

# 네비게이션 메뉴 (AI Studio 사이드바 메뉴 100% 동일)
menu = st.sidebar.radio(
    "메인 메뉴",
    ["🏠 홈", "📊 성과 분석", "🎯 센터 진단", "⚠️ 위험 관리", "🌡️ KPI 히트맵", "🔬 심화 분석", "📑 반기 보고"]
)

# 사이드바 데이터 상태 표시
st.sidebar.markdown(f"""
<div style="background:white; border:1px solid #E2E8F0; border-radius:10px; padding:12px; margin-top:16px;">
    <div style="font-size:12px; font-weight:700; color:#1E293B; margin-bottom:6px;">📊 데이터 현황</div>
    <div style="font-size:11px; color:#64748B; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>평가월:</span> <strong>{selected_month}</strong>
    </div>
    <div style="font-size:11px; color:#64748B; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>평가 센터:</span> <strong>{len(cur_df)}개소</strong>
    </div>
    <div style="font-size:11px; color:#64748B; display:flex; justify-content:space-between;">
        <span>진척률:</span> <strong>{half_name} {month_in_half}/6개월 ({progress_pct}%)</strong>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 4. 공통 상단 헤더 배너
# =============================================================================
st.markdown(f"""
<div class="yesco-header-banner">
    <div class="header-title-box">
        <h1>예스코 고객센터 성과 대시보드</h1>
        <p>도시가스 고객센터 월별 KPI 성과, 반기 마감({target_end_text} 911점) 전망 및 전년 동월 대비 진단 분석</p>
    </div>
    <div class="header-badge-box">
        <span class="badge-pill-header">📅 {cur_year}년 {cur_month}월 ({half_name} {month_in_half}/6개월차)</span>
        <span class="badge-pill-header" style="background:#FFFFFF; color:#0B4EA2;">목표: {target_end_text} 911점</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# PAGE 1: 🏠 홈
# =============================================================================
if menu == "🏠 홈":
    avg_safety = cur_df['안전점검실점검율'].mean()
    avg_key = cur_df['중점고객안전점검율'].mean()
    total_centers = len(cur_df)
    avg_score = cur_df['총점'].mean()
    
    valid_yoy = cur_df['전년동월_총점'].dropna()
    prev_avg = valid_yoy.mean() if not valid_yoy.empty else None
    yoy_diff = (avg_score - prev_avg) if prev_avg is not None else None
    
    on_track_count = len(cur_df[cur_df['예상반기총점'] >= 911.0])
    on_track_rate = (on_track_count / total_centers * 100) if total_centers > 0 else 0
    lag_centers = cur_df[(cur_df['전년동월대비_증감'] < -10) | (cur_df['예상반기총점'] < 905) | (cur_df['안전점검실점검율'] < benchmark_safety - 3)]

    # 종합 진단 현황 배너
    st.markdown(f"""
    <div class="banner-notice">
        <strong>💡 고객센터 종합 진단 현황 ({month_in_half}개월차)</strong><br/>
        현재 <strong>{month_in_half}개월차 기준 평균 실점검율은 {avg_safety:.1f}%</strong>(중점안전점검 {avg_key:.1f}%)입니다. 계획 대비 양호하게 추진 중이며,
        전년 동월 및 <strong>{target_end_text} 911점 달성 목표선</strong>을 기준으로 센터별 진척 페이스를 종합 모니터링하고 있습니다.
    </div>
    """, unsafe_allow_html=True)

    # 4대 핵심 지표 카드
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        yoy_str = f"전년 동월({prev_avg:.1f}점) 대비 {'+' if yoy_diff >= 0 else ''}{yoy_diff:.1f}점" if yoy_diff is not None else f"{half_name} {month_in_half}개월차"
        st.markdown(f"""
        <div class="metric-grid-card" style="border-left-color: #0B4EA2;">
            <div class="metric-title"><span>전체 센터 평균 총점</span> <span>📊</span></div>
            <div class="metric-value">{avg_score:.1f}점</div>
            <div class="metric-sub" style="color: {'#16A34A' if (yoy_diff or 0) >= 0 else '#DC2626'};">{yoy_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-grid-card" style="border-left-color: #10B981;">
            <div class="metric-title"><span>{target_end_text} 911점 예상 달성률</span> <span>🎯</span></div>
            <div class="metric-value">{on_track_rate:.1f}%</div>
            <div class="metric-sub" style="color: #059669;">총 {total_centers}개소 중 {on_track_count}개소 정상 궤도</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-grid-card" style="border-left-color: #F59E0B;">
            <div class="metric-title"><span>누적 지연 / 중점 코칭 센터</span> <span>⚠️</span></div>
            <div class="metric-value">{len(lag_centers)}개소</div>
            <div class="metric-sub" style="color: #D97706;">전년비 지연 및 911점 미달 위험</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        safety_status = "계획대비 양호" if avg_safety >= benchmark_safety - 3 else "관리 필요"
        st.markdown(f"""
        <div class="metric-grid-card" style="border-left-color: #6366F1;">
            <div class="metric-title"><span>안전점검 평균 실점검율</span> <span>⏱️</span></div>
            <div class="metric-value">{avg_safety:.1f}%</div>
            <div class="metric-sub" style="color: #4F46E5;">계획({benchmark_safety:.1f}%) 대비 {safety_status}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 5대 핵심 인사이트 카드
    st.markdown("### 💡 핵심 인사이트 및 자동 진단")
    if on_track_count >= total_centers * 0.8:
        st.markdown(f"""
        <div class="insight-card insight-success">
            <div class="insight-header">
                <span class="insight-title">🎯 {target_end_text} 911점 도달 정상 궤도 ({on_track_count}개소)</span>
                <span class="insight-pill">911점 궤도 정상</span>
            </div>
            <div class="insight-body">
                현재 {month_in_half}개월차 기준 전체 {total_centers}개 센터 중 {on_track_count}개소({on_track_rate:.1f}%)가 {target_end_text} 911점 달성 목표선 대비 안정적인 추진 페이스를 보이고 있습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        caution_cnt = total_centers - on_track_count
        st.markdown(f"""
        <div class="insight-card insight-warning">
            <div class="insight-header">
                <span class="insight-title">⚠️ {target_end_text} 911점 도달 집중 관리 ({caution_cnt}개소 보강 필요)</span>
                <span class="insight-pill">페이스 관리 필요</span>
            </div>
            <div class="insight-body">
                현재 {month_in_half}개월차 기준 {caution_cnt}개 센터가 {target_end_text} 911점 도달 페이스에 다소 지연을 보이고 있습니다. 안전점검 오더 처리 속도를 조기 보강해야 합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

    is_safety_good = avg_safety >= benchmark_safety - 3.0
    st.markdown(f"""
    <div class="insight-card {'insight-success' if is_safety_good else 'insight-info'}">
        <div class="insight-header">
            <span class="insight-title">⏱️ 안전점검 실점검율 진척 현황</span>
            <span class="insight-pill">{'계획대비 양호' if is_safety_good else '진척 관리 필요'}</span>
        </div>
        <div class="insight-body">
            현재 {month_in_half}개월차 기준 평균 실점검율은 {avg_safety:.1f}%(중점안전점검 {avg_key:.1f}%)입니다. 계획 대비 {'양호하게 추진되고 있습니다.' if is_safety_good else '일부 센터의 추가 점검 관리가 필요합니다.'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 종합 순위 차트 & 테이블
    col_chart, col_rank = st.columns([3, 2])
    with col_chart:
        st.markdown("### 📊 센터별 현재 총점 및 911점 목표선")
        sorted_df = cur_df.sort_values(by="총점", ascending=False)
        fig_bar = px.bar(
            sorted_df,
            x="센터명",
            y="총점",
            color="예상반기총점",
            color_continuous_scale="Blues",
            labels={"총점": "현재 총점", "예상반기총점": "반기말 예상총점"},
            text="총점"
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_bar.add_hline(y=911, line_dash="dash", line_color="#EF4444", annotation_text="911점 도달선")
        fig_bar.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=30, b=80),
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_rank:
        st.markdown("### 🏆 센터 종합 순위표")
        display_rank = sorted_df[['센터명', '총점', '예상반기총점', '도달판정', '전년동월대비_증감']].copy()
        display_rank.insert(0, '순위', range(1, len(display_rank) + 1))
        st.dataframe(
            display_rank.style.format({
                '총점': '{:.1f}',
                '예상반기총점': '{:.1f}',
                '전년동월대비_증감': lambda x: f"{'+' if x>0 else ''}{x:.1f}" if pd.notna(x) else '-'
            }),
            use_container_width=True,
            height=420
        )

# =============================================================================
# PAGE 2: 📊 성과 분석
# =============================================================================
elif menu == "📊 성과 분석":
    st.markdown("### 📊 지표별 세부 성과 및 월별 추이 분석")
    st.write(f"**기준 평가월**: {selected_month} | **분석 대상**: 총 {len(cur_df)}개 고객센터")
    tab1, tab2, tab3 = st.tabs(["📋 센터별 KPI 종합표", "📈 지표별 기여도", "📉 전년 대비(YoY) 비교"])
    with tab1:
        kpi_table = cur_df[['센터명', '총점', '예상반기총점', '도달판정', '안전점검실점검율', '중점고객안전점검율', '사용계약율', '상담응대율', '상담기여도', '고객서비스만족도']].copy()
        st.dataframe(kpi_table.style.format({
            '총점': '{:.1f}',
            '예상반기총점': '{:.1f}',
            '안전점검실점검율': '{:.1f}%',
            '중점고객안전점검율': '{:.1f}%',
            '사용계약율': '{:.1f}%',
            '상담응대율': '{:.1f}%',
            '상담기여도': '{:.1f}%',
            '고객서비스만족도': '{:.1f}점'
        }), use_container_width=True)
    with tab2:
        kpi_cols = ['안전점검_점수', '중점고객_점수', '사용계약_점수', '상담응대_점수', '상담기여_점수', '만족도_점수']
        avg_kpi = cur_df[kpi_cols].mean().reset_index()
        avg_kpi.columns = ['지표명', '평균 배점']
        fig_pie = px.pie(avg_kpi, names='지표명', values='평균 배점', color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_pie, use_container_width=True)
    with tab3:
        if '전년동월대비_증감' in cur_df.columns:
            fig_yoy = px.bar(
                cur_df.sort_values(by="전년동월대비_증감", ascending=False),
                x="센터명",
                y="전년동월대비_증감",
                color="전년동월대비_증감",
                color_continuous_scale="RdBu",
                title="센터별 전년 동월 대비 총점 증감 (YoY)"
            )
            fig_yoy.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_yoy, use_container_width=True)

# =============================================================================
# PAGE 3: 🎯 센터 진단 (AI Studio CenterDetailPage 디자인과 100% 동일 구현)
# =============================================================================
elif menu == "🎯 센터 진단":
    # 1. 상단 센터 선택 헤더
    center_names = cur_df['센터명'].tolist()
    
    # 센터 선택 박스 (레이블을 보기 좋게 서식화)
    def center_format(c):
        r = cur_df[cur_df['센터명'] == c].iloc[0]
        return f"{c} 센터 ({r['총점']:.1f}점 | {target_end_text} 예상 {r['예상반기총점']:.1f}점)"

    sel_center = st.selectbox(
        "진단 센터 선택",
        center_names,
        format_func=center_format,
        label_visibility="visible"
    )
    
    c_rec = cur_df[cur_df['센터명'] == sel_center].iloc[0]
    
    # 뱃지 색상 및 라벨 결정
    is_interim = month_in_half < 6
    check_score = c_rec['예상반기총점'] if is_interim else c_rec['총점']
    if check_score >= 911.0:
        badge_bg = "#DCFCE7"
        badge_color = "#15803D"
        badge_border = "#86EFAC"
        badge_text = f"★ {target_end_text} 911점 달성 유력" if is_interim else "★ 911점 달성"
    elif check_score >= 905.0:
        badge_bg = "#FEF3C7"
        badge_color = "#B45309"
        badge_border = "#FCD34D"
        badge_text = "▲ 주의 (페이스 보강)"
    else:
        badge_bg = "#FEE2E2"
        badge_color = "#991B1B"
        badge_border = "#FCA5A5"
        badge_text = "● 위험 (집중 코칭)"

    yoy_val = c_rec['전년동월대비_증감']
    yoy_str = f"{'+' if yoy_val > 0 else ''}{yoy_val:.1f}점" if pd.notna(yoy_val) else "-"
    yoy_color = "#DC2626" if (pd.notna(yoy_val) and yoy_val < 0) else "#15803D"
    
    prev_half_str = f"{c_rec['전년반기말_총점']:.1f}점" if pd.notna(c_rec['전년반기말_총점']) else "-"

    # 센터 진단 헤더 카드
    st.markdown(f"""
    <div class="center-header-card">
        <div style="font-size:16px; font-weight:800; color:#0B4EA2;">
            🏢 {c_rec['센터명']} 고객센터 정밀 진단
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
            <div class="center-stat-pill">
                <div class="label">당월({month_in_half}개월차) 누적 총점</div>
                <div class="val" style="color:#0B4EA2;">{c_rec['총점']:.1f}점</div>
            </div>
            <div class="center-stat-pill primary">
                <div class="label">{target_end_text} 예상 총점</div>
                <div class="val" style="color:#1E40AF;">{c_rec['예상반기총점']:.1f}점</div>
            </div>
            <div class="center-stat-pill">
                <div class="label">전년 동월 대비 (YoY)</div>
                <div class="val" style="color:{yoy_color};">{yoy_str}</div>
            </div>
            <div class="center-stat-pill">
                <div class="label">전년 {target_end_text} 실적</div>
                <div class="val" style="color:#475569;">{prev_half_str}</div>
            </div>
            <div style="background:{badge_bg}; color:{badge_color}; border:1px solid {badge_border}; border-radius:8px; padding:8px 14px; font-size:12px; font-weight:800;">
                {badge_text}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 안내 뱃지
    order_status = "양호" if c_rec['안전점검실점검율'] >= benchmark_safety - 3 else "지연"
    status_advice = "양호하게 추진 중입니다." if order_status == "양호" else "보강 관리가 필요합니다."
    st.markdown(f"""
    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:12px 18px; margin-bottom:18px; font-size:12px; color:#1E3A8A; display:flex; justify-content:space-between; align-items:center;">
        <span>
            ℹ️ <strong>평가 진척 안내:</strong> 현재 {month_in_half}개월차 기준 당 센터의 안전점검 실점검율은 <strong>{c_rec['안전점검실점검율']:.1f}%</strong>로 계획 대비 {status_advice} {target_end_text} 911점 예상 판정은 <strong>{c_rec['도달판정']}</strong> 상태입니다.
        </span>
        <span style="font-weight:800; color:#0B4EA2; background:#DBEAFE; padding:4px 10px; border-radius:6px; font-size:11px;">
            진척 판정: {order_status}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 2. 레이더 차트 & 지표별 세부 채점 테이블 (2열 레이아웃)
    col_radar, col_table = st.columns([1, 1])

    with col_radar:
        st.markdown("""
        <div class="studio-card-title"><span>🎯</span> 6대 핵심 KPI 진척 밸런스 레이더</div>
        <div class="studio-card-desc">각 지표별 만점 대비 당월 달성률 현황 (안전점검 계열은 누적 진척도)</div>
        """, unsafe_allow_html=True)
        
        # Plotly Radar Chart
        categories = ['안전점검 (550)', '중점고객 (100)', '사용계약 (50)', '상담응대 (100)', '상담기여 (100)', '만족도 (100)']
        values = [
            c_rec['안전점검실점검율'],
            c_rec['중점고객안전점검율'],
            c_rec['사용계약율'],
            c_rec['상담응대율'],
            c_rec['상담기여도'],
            c_rec['고객서비스만족도']
        ]
        # 레이더 차트 닫힘을 위해 첫 번째 값 추가
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name=c_rec['센터명'],
            line_color='#0B4EA2',
            fillcolor='rgba(11, 78, 162, 0.35)'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="#64748B")),
                angularaxis=dict(tickfont=dict(size=10, color="#172B4D", weight=700))
            ),
            showlegend=False,
            height=320,
            margin=dict(l=30, r=30, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_table:
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <div class="studio-card-title"><span>📊</span> 지표별 세부 채점 및 성격 내역</div>
            <span style="font-size:11px; color:#64748B;">{month_in_half}개월차 기준</span>
        </div>
        <div class="studio-card-desc">지표별 성격(누적형 vs 월별비율형) 및 배점 채점 결과</div>
        """, unsafe_allow_html=True)

        table_html = f"""
        <table class="kpi-table">
            <thead>
                <tr>
                    <th>평가 항목</th>
                    <th>지표 성격</th>
                    <th style="text-align:right;">배점</th>
                    <th style="text-align:right;">당월 달성률</th>
                    <th style="text-align:right;">획득 점수</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:700;">안전점검실점검율</td>
                    <td style="color:#0B4EA2; font-size:11px;">핵심 점검형</td>
                    <td style="text-align:right; color:#64748B;">550점</td>
                    <td style="text-align:right; font-weight:600;">{c_rec['안전점검실점검율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['안전점검_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">중점고객안전점검율</td>
                    <td style="color:#0B4EA2; font-size:11px;">핵심 점검형</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:600;">{c_rec['중점고객안전점검율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['중점고객_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">사용계약율</td>
                    <td style="color:#64748B; font-size:11px;">월별 비율 유지</td>
                    <td style="text-align:right; color:#64748B;">50점</td>
                    <td style="text-align:right; font-weight:600;">{c_rec['사용계약율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['사용계약_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">상담응대율</td>
                    <td style="color:#64748B; font-size:11px;">월별 비율 유지</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:600;">{c_rec['상담응대율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['상담응대_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">상담기여도</td>
                    <td style="color:#64748B; font-size:11px;">월별 비율 유지</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:600;">{c_rec['상담기여도']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['상담기여_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">고객서비스만족도</td>
                    <td style="color:#64748B; font-size:11px;">조사 평가 유지</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:600;">{c_rec['고객서비스만족도']:.1f}점</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['만족도_점수']:.1f}점</td>
                </tr>
                <tr class="total-row">
                    <td>합계 (현재 누적 총점)</td>
                    <td style="color:#0B4EA2; font-size:11px;">{target_end_text} 예상 {c_rec['예상반기총점']:.1f}점</td>
                    <td style="text-align:right; color:#64748B;">1,000점</td>
                    <td style="text-align:right;">-</td>
                    <td style="text-align:right; font-size:14px;">{c_rec['총점']:.1f}점</td>
                </tr>
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    # 3. What-If 시뮬레이터 (AI Studio CenterDetailPage와 100% 동일)
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="border-top:1px solid #DCE3EA; padding-top:18px;">
        <div class="studio-card-title"><span>🔮</span> What-If 시뮬레이터: {c_rec['센터명']} 센터 {target_end_text} 911점 달성 전략 수립</div>
        <div class="studio-card-desc">{target_end_text} 최종 누적 목표치를 슬라이더로 조율하여 911점 달성 여부와 추가 필요 점수를 즉시 시뮬레이션합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    # 슬라이더 기본값 (React의 defaultSafety / defaultKey 반영)
    def_safety = 94.0 if month_in_half < 6 else float(c_rec['안전점검실점검율'])
    def_key = 95.0 if month_in_half < 6 else float(c_rec['중점고객안전점검율'])

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        sim_safety = st.slider(f"{target_end_text} 안전점검 목표치 (550점)", 70.0, 100.0, float(def_safety), 0.5, key="sim_s")
        st.caption(f"당월 누적: {c_rec['안전점검실점검율']:.1f}% (권장 92% 이상)")
        sim_key = st.slider(f"{target_end_text} 중점고객 목표치 (100점)", 60.0, 100.0, float(def_key), 0.5, key="sim_k")
        st.caption(f"당월 누적: {c_rec['중점고객안전점검율']:.1f}% (권장 95% 이상)")
    with s_col2:
        sim_contract = st.slider("사용계약율 (50점)", 60.0, 100.0, float(c_rec['사용계약율']), 1.0, key="sim_c")
        sim_resp = st.slider("상담응대율 (100점)", 70.0, 100.0, float(c_rec['상담응대율']), 0.5, key="sim_r")
    with s_col3:
        sim_contrib = st.slider("상담기여도 (100점)", 70.0, 100.0, float(c_rec['상담기여도']), 0.5, key="sim_cb")
        sim_sat = st.slider("고객서비스 만족도 (100점)", 70.0, 100.0, float(c_rec['고객서비스만족도']), 0.5, key="sim_st")

    # 시뮬레이션 계산
    sim_sc_safety = (sim_safety / 100.0) * 550.0
    sim_sc_key = (sim_key / 100.0) * 100.0
    sim_sc_contract = calc_contract_score(sim_contract)
    sim_sc_resp = (sim_resp / 100.0) * 100.0
    sim_sc_contrib = (sim_contrib / 100.0) * 100.0
    sim_sc_sat = sim_sat

    sim_total = sim_sc_safety + sim_sc_key + sim_sc_contract + sim_sc_resp + sim_sc_contrib + sim_sc_sat
    is_passing = sim_total >= 911.0
    gap = 911.0 - sim_total

    # 시뮬레이션 결과 바
    res_bg = "#DCFCE7" if is_passing else "#FEE2E2"
    res_border = "#86EFAC" if is_passing else "#FCA5A5"
    res_color = "#15803D" if is_passing else "#991B1B"
    res_badge_text = "🎉 911점 달성 (합격)" if is_passing else f"⚠️ {abs(gap):.1f}점 보강 필요"

    st.markdown(f"""
    <div class="sim-result-bar">
        <div>
            <div style="font-size:11px; color:#5E6C84;">{target_end_text} 시뮬레이션 최종 총점</div>
            <div style="font-size:22px; font-weight:800; color:#0B4EA2;">{sim_total:.1f}점</div>
        </div>
        <div style="background:{res_bg}; border:1px solid {res_border}; color:{res_color}; border-radius:8px; padding:8px 16px; font-size:13px; font-weight:800;">
            {res_badge_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# PAGE 4: ⚠️ 위험 관리
# =============================================================================
elif menu == "⚠️ 위험 관리":
    st.markdown("### ⚠️ 위험 센터 조기 감지 및 맞춤형 코칭 리스트")
    st.write(f"현재 **{month_in_half}개월차 기준 오더 누적 진척도** 및 **{target_end_text} 911점 도달 위험도**를 조기 진단합니다.")

    danger_centers = cur_df[cur_df['도달판정'] == '위험']
    caution_centers = cur_df[cur_df['도달판정'] == '주의']
    safe_centers = cur_df[cur_df['도달판정'] == '정상궤도']

    st.markdown(f"""
    <div style="display:flex; gap:12px; margin-bottom:16px;">
        <span style="background:#FEE2E2; color:#991B1B; padding:6px 14px; border-radius:20px; font-weight:bold; font-size:12px;">🔴 집중 코칭 대상: {len(danger_centers)}개소</span>
        <span style="background:#FEF3C7; color:#92400E; padding:6px 14px; border-radius:20px; font-weight:bold; font-size:12px;">🟡 관심 관찰 대상: {len(caution_centers)}개소</span>
        <span style="background:#DCFCE7; color:#166534; padding:6px 14px; border-radius:20px; font-weight:bold; font-size:12px;">🟢 정상 궤도: {len(safe_centers)}개소</span>
    </div>
    """, unsafe_allow_html=True)

    if not danger_centers.empty:
        st.markdown("#### 🚨 집중 코칭 필요 센터 (반기말 905점 미만 예상)")
        st.dataframe(danger_centers[['센터명', '총점', '예상반기총점', '전년동월대비_증감', '안전점검실점검율', '중점고객안전점검율']], use_container_width=True)

    if not caution_centers.empty:
        st.markdown("#### ⚠️ 관심 관찰 센터 (반기말 905~911점 예상)")
        st.dataframe(caution_centers[['센터명', '총점', '예상반기총점', '전년동월대비_증감', '안전점검실점검율']], use_container_width=True)

    if danger_centers.empty and caution_centers.empty:
        st.success("현재 모든 고객센터가 911점 정상 궤도에 안착해 있습니다.")

# =============================================================================
# PAGE 5: 🌡️ KPI 히트맵
# =============================================================================
elif menu == "🌡️ KPI 히트맵":
    st.markdown("### 🌡️ 센터별 KPI 달성률 매트릭스 히트맵")
    heat_cols = ['안전점검실점검율', '중점고객안전점검율', '사용계약율', '상담응대율', '상담기여도', '고객서비스만족도']
    heat_df = cur_df.set_index('센터명')[heat_cols]
    
    fig_heat = px.imshow(
        heat_df,
        color_continuous_scale="Blues",
        labels=dict(x="평가 지표", y="고객센터", color="달성률/점수"),
        aspect="auto"
    )
    fig_heat.update_layout(height=650)
    st.plotly_chart(fig_heat, use_container_width=True)

# =============================================================================
# PAGE 6: 🔬 심화 분석
# =============================================================================
elif menu == "🔬 심화 분석":
    st.markdown("### 🔬 지표 간 상관관계 및 분포 심층 분석")
    fig_sc = px.scatter(
        cur_df,
        x="안전점검실점검율",
        y="총점",
        size="예상반기총점",
        color="도달판정",
        hover_name="센터명",
        color_discrete_map={"정상궤도": "#10B981", "주의": "#F59E0B", "위험": "#EF4444"},
        title="안전점검 실점검율 vs 총점 상관분포 (원 크기: 반기말 예상총점)"
    )
    fig_sc.add_hline(y=911, line_dash="dash", line_color="#EF4444", annotation_text="911점선")
    st.plotly_chart(fig_sc, use_container_width=True)

# =============================================================================
# PAGE 7: 📑 반기 보고
# =============================================================================
elif menu == "📑 반기 보고":
    st.markdown(f"### 📑 {cur_year}년 {half_name} 고객센터 성과 종합 보고서")
    st.markdown(f"""
    #### 1. 총평
    - **평가 기간**: {cur_year}년 {half_name} ({month_in_half}/6개월차 누적)
    - **전체 센터 수**: {len(cur_df)}개소
    - **평균 점수**: {cur_df['총점'].mean():.1f}점
    - **{target_end_text} 911점 도달 정상 궤도율**: {(len(cur_df[cur_df['예상반기총점']>=911])/len(cur_df)*100):.1f}%
    
    #### 2. 핵심 추진 실적
    - 현재 {month_in_half}개월차 기준 평균 실점검율은 **{cur_df['안전점검실점검율'].mean():.1f}%**로 계획 대비 양호하게 추진 중입니다.
    - 전년 동월 대비 종합 성과는 평균 **{'+' if (yoy_diff or 0) >= 0 else ''}{(yoy_diff or 0):.1f}점**의 추세를 나타내고 있습니다.
    """)
    st.dataframe(cur_df.sort_values(by="총점", ascending=False)[['센터명', '총점', '예상반기총점', '도달판정', '안전점검실점검율']], use_container_width=True)
