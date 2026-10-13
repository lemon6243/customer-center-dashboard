# -*- coding: utf-8 -*-
"""
예스코 도시가스 고객센터 성과 대시보드 (Streamlit Application)
- Streamlit Cloud 배포용 메인 모듈 (app.py)
- 최신월 디폴트 자동 선택 및 AI Studio 비주얼 디자인 일체화
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

# 럭셔리 비즈니스 UI (AI Studio 일체형 테마)
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
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 4px 16px rgba(11, 78, 162, 0.18);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .header-title-box h1 {
        margin: 0;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
    }
    .header-title-box p {
        margin: 4px 0 0 0;
        font-size: 12px;
        color: #DBEAFE;
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
        color: #FFFFFF;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    
    /* Notice Banner */
    .banner-notice {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 20px;
        color: #1E3A8A;
        font-size: 13px;
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    
    /* KPI Metric Cards */
    .metric-grid-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border-left: 4px solid #0B4EA2;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748B;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
    }
    .metric-sub {
        font-size: 11.5px;
        margin-top: 6px;
        font-weight: 600;
        color: #0284C7;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* Insight Cards */
    .insight-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0B4EA2;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
    }
    .insight-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .insight-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #0F172A;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .insight-body {
        font-size: 12px;
        color: #475569;
        line-height: 1.55;
    }
    .insight-pill {
        font-size: 10.5px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 12px;
    }
    .insight-success {
        border-left-color: #10B981;
    }
    .insight-success .insight-pill {
        background: #DCFCE7;
        color: #15803D;
    }
    .insight-warning {
        border-left-color: #F59E0B;
    }
    .insight-warning .insight-pill {
        background: #FEF3C7;
        color: #B45309;
    }
    .insight-info {
        border-left-color: #3B82F6;
    }
    .insight-info .insight-pill {
        background: #DBEAFE;
        color: #1D4ED8;
    }
    
    /* Table Styling */
    .styled-table-wrapper {
        background: white;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 14px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 처리 및 점수 산출 로직
# -----------------------------------------------------------------------------
def normalize_date_string(val):
    if val is None or pd.isna(val):
        return '2026-08-01'
    if isinstance(val, (int, float)):
        # Excel serial date
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

def to_percentage(rate):
    if rate is None or pd.isna(rate):
        return 0.0
    try:
        num = float(rate)
        if 0 <= num <= 1.05:
            return num * 100.0
        return num
    except:
        return 0.0

def calc_contract_score(rate):
    p = to_percentage(rate)
    if p >= 90.0: return 50.0
    if p >= 80.0: return 45.0
    if p >= 70.0: return 40.0
    return 35.0

def predict_half_end_score(current_score, month, safety_score, non_cumulative_score, key_score, adjust_score=0):
    m = month if month <= 6 else month - 6
    if m >= 6:
        return round(current_score, 1)
    pace_ratio = max(0.1, m / 6.0)
    
    projected_safety = min(550.0, safety_score / pace_ratio)
    projected_key = min(100.0, key_score / pace_ratio)
    projected_total = projected_safety + projected_key + non_cumulative_score + adjust_score
    return round(min(1000.0, max(0.0, projected_total)), 1)

@st.cache_data
def load_all_records():
    excel_path = 'data/latest_data.xlsx'
    json_path = 'data/latest_data.json'
    fallback_json = 'src/data/latest_data.json'
    
    raw_list = []
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            raw_list = df.to_dict('records')
        except Exception:
            pass
            
    if not raw_list and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
        except Exception:
            pass
            
    if not raw_list and os.path.exists(fallback_json):
        try:
            with open(fallback_json, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
        except Exception:
            pass

    if not raw_list:
        return pd.DataFrame()

    processed = []
    for r in raw_list:
        date_str = normalize_date_string(r.get('평가월'))
        parts = date_str.split('-')
        year = int(parts[0]) if len(parts) > 0 else 2026
        month = int(parts[1]) if len(parts) > 1 else 8
        half = '상반기' if month <= 6 else '하반기'
        
        safety_rate = to_percentage(r.get('안전점검실점검율'))
        key_rate = to_percentage(r.get('중점고객안전점검율'))
        contract_rate = to_percentage(r.get('사용계약율'))
        response_rate = to_percentage(r.get('상담응대율'))
        contrib_rate = to_percentage(r.get('상담기여도'))
        sat_val = r.get('고객서비스만족도')
        sat_rate = float(sat_val) if sat_val is not None and not pd.isna(sat_val) else 0.0

        safety_score = (safety_rate / 100.0) * 550.0
        key_score = (key_rate / 100.0) * 100.0
        contract_score = calc_contract_score(contract_rate)
        resp_score = (response_rate / 100.0) * 100.0
        contrib_score = (contrib_rate / 100.0) * 100.0
        sat_score = sat_rate
        
        adjust = float(r.get('민원대응적정성', 0) or 0) + float(r.get('주의경고', 0) or 0) + float(r.get('가점', 0) or 0)
        calc_total = safety_score + key_score + contract_score + resp_score + contrib_score + sat_score + adjust
        
        total_score = r.get('총점')
        if total_score is None or pd.isna(total_score):
            total_score = calc_total
        else:
            total_score = float(total_score)
            
        non_cum = contract_score + resp_score + contrib_score + sat_score
        pred_half = predict_half_end_score(total_score, month, safety_score, non_cum, key_score, adjust)

        processed.append({
            '센터명': r.get('센터명', r.get('센터', '미상')),
            '평가월': date_str,
            '연도': year,
            '월': month,
            '반기': half,
            '총점': round(total_score, 1),
            '안전점검실점검율': round(safety_rate, 2),
            '중점고객안전점검율': round(key_rate, 2),
            '사용계약율': round(contract_rate, 2),
            '상담응대율': round(response_rate, 2),
            '상담기여도': round(contrib_rate, 2),
            '고객서비스만족도': round(sat_rate, 2),
            '안전점검_점수': round(safety_score, 1),
            '중점고객_점수': round(key_score, 1),
            '사용계약_점수': round(contract_score, 1),
            '상담응대_점수': round(resp_score, 1),
            '상담기여_점수': round(contrib_score, 1),
            '만족도_점수': round(sat_score, 1),
            '예상반기총점': pred_half
        })
        
    df_all = pd.DataFrame(processed)
    return df_all

# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 최신월 디폴트 설정
# -----------------------------------------------------------------------------
df_all = load_all_records()

if df_all.empty:
    st.error("데이터를 불러올 수 없습니다. data/latest_data.xlsx 또는 data/latest_data.json 파일을 확인해주세요.")
    st.stop()

# 사용 가능한 모든 월 목록 추출 (오름차순)
all_months = sorted(list(df_all['평가월'].apply(lambda x: str(x)[:7]).unique()))

# 사용자 요청: "최신월을 디폴트로 해줘 새로고침하거나 새로 접속하면 항상 2026년 2월을 표기하네.."
# -> 리스트의 가장 마지막 최신 월(len - 1)을 기본값으로 강제 지정
default_latest_idx = len(all_months) - 1

# 사이드바 설정
st.sidebar.markdown("""
<div style="display:flex; align-items:center; gap:8px; padding: 4px 0 12px 0;">
    <div style="background:#0B4EA2; color:white; width:30px; height:30px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:15px;">Y</div>
    <div>
        <div style="font-weight:800; font-size:14px; color:#0B4EA2;">예스코 고객센터</div>
        <div style="font-size:11px; color:#64748B;">성과 평가 관리 시스템</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 월 선택 드롭다운 (최신월에 [최신] 태그 표기 및 디폴트 인덱스)
format_month = lambda ym: f"{ym[:4]}년 {int(ym[5:7])}월 ({'상반기' if int(ym[5:7])<=6 else '하반기'} {int(ym[5:7]) if int(ym[5:7])<=6 else int(ym[5:7])-6}개월차){' ★최신' if ym == all_months[-1] else ''}"

selected_month = st.sidebar.selectbox(
    "📅 평가월 선택",
    all_months,
    index=default_latest_idx,
    format_func=format_month
)

# 현재 선택 월 및 기간 정보 계산
cur_df = df_all[df_all['평가월'].str.startswith(selected_month)].copy()
cur_year = int(selected_month.split('-')[0])
cur_month = int(selected_month.split('-')[1])
month_in_half = cur_month if cur_month <= 6 else cur_month - 6
half_name = "상반기" if cur_month <= 6 else "하반기"
target_end_text = "6월말" if cur_month <= 6 else "12월말"
progress_pct = int((month_in_half / 6.0) * 100)

# 전년 동월 데이터 매핑 (YoY)
prev_year = cur_year - 1
prev_df = df_all[(df_all['연도'] == prev_year) & (df_all['월'] == cur_month)].copy()
prev_map = {r['센터명']: r['총점'] for _, r in prev_df.iterrows()}
cur_df['전년동월_총점'] = cur_df['센터명'].map(prev_map)
cur_df['전년동월대비_증감'] = cur_df['총점'] - cur_df['전년동월_총점']

# 전년 반기말(6월말 or 12월말) 실적 매핑
prev_half_end_month = 6 if cur_month <= 6 else 12
prev_end_df = df_all[(df_all['연도'] == prev_year) & (df_all['월'] == prev_half_end_month)].copy()
prev_end_map = {r['센터명']: r['총점'] for _, r in prev_end_df.iterrows()}
cur_df['전년반기말_총점'] = cur_df['센터명'].map(prev_end_map)

# 판정 로직
benchmark_safety = (month_in_half / 6.0) * 92.0
def get_track_status(pred):
    if pred >= 911.0: return '정상궤도'
    if pred >= 905.0: return '주의'
    return '위험'
cur_df['도달판정'] = cur_df['예상반기총점'].apply(get_track_status)

# 네비게이션 메뉴
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

# 파일 업로더
uploaded_file = st.sidebar.file_uploader("📥 신규 데이터 업로드 (.xlsx)", type=["xlsx", "xls"])
if uploaded_file is not None:
    st.sidebar.success("파일 업로드가 완료되었습니다.")

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
    
    # 전년 동월 비교
    valid_yoy = cur_df['전년동월_총점'].dropna()
    prev_avg = valid_yoy.mean() if not valid_yoy.empty else None
    yoy_diff = (avg_score - prev_avg) if prev_avg is not None else None

    # 911점 정상 궤도
    on_track_count = len(cur_df[cur_df['예상반기총점'] >= 911.0])
    on_track_rate = (on_track_count / total_centers * 100) if total_centers > 0 else 0
    lag_centers = cur_df[(cur_df['전년동월대비_증감'] < -10) | (cur_df['예상반기총점'] < 905) | (cur_df['안전점검실점검율'] < benchmark_safety - 3)]

    # 종합 진단 현황 배너 (사용자 최신 요청 문구)
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

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 5대 핵심 인사이트 카드 (AI Studio insights.ts와 100% 동기화)
    st.markdown("### 💡 핵심 인사이트 및 자동 진단")

    # 1. 911점 도달 정상 궤도
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

    # 2. 전년 동월(YoY) 비교
    if yoy_diff is not None:
        if yoy_diff >= 0:
            top_gain = cur_df.sort_values(by="전년동월대비_증감", ascending=False).iloc[0]
            st.markdown(f"""
            <div class="insight-card insight-success">
                <div class="insight-header">
                    <span class="insight-title">📈 전년 동월 대비 종합 성과 상승</span>
                    <span class="insight-pill">YoY +{yoy_diff:.1f}점</span>
                </div>
                <div class="insight-body">
                    현재 {month_in_half}월차 평균 총점({avg_score:.1f}점)은 전년 동월({prev_avg:.1f}점) 대비 +{yoy_diff:.1f}점 상회하여 우수한 누적 흐름을 보이고 있습니다. 특히 {top_gain['센터명']} 센터가 전년 대비 +{top_gain['전년동월대비_증감']:.1f}점 상승하여 가장 두드러집니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="insight-card insight-warning">
                <div class="insight-header">
                    <span class="insight-title">⚠️ 전년 동월 대비 성과 지연 감지</span>
                    <span class="insight-pill">YoY {yoy_diff:.1f}점</span>
                </div>
                <div class="insight-body">
                    현재 {month_in_half}월차 평균 총점({avg_score:.1f}점)이 전년 동월({prev_avg:.1f}점) 대비 {yoy_diff:.1f}점 다소 뒤처져 있어, {target_end_text} 911점 달성을 위한 조기 오더 드라이브가 필요합니다.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 3. 안전점검 실점검율 진척 현황
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

    # 4. 코칭 대상 센터
    if len(lag_centers) > 0:
        lag_names = ", ".join(lag_centers['센터명'].head(3).tolist())
        st.markdown(f"""
        <div class="insight-card insight-warning">
            <div class="insight-header">
                <span class="insight-title">🚨 전년 동월 대비 누적 지연 센터 코칭 필요</span>
                <span class="insight-pill">코칭 대상 {len(lag_centers)}개소</span>
            </div>
            <div class="insight-body">
                {lag_names} 등 {len(lag_centers)}개 센터는 전년 동월 대비 오더 누적 페이스가 지연되고 있거나 {target_end_text} 911점 도달에 주의가 요구됩니다. 해당 센터의 원활한 오더 처리를 위한 맞춤형 현장 지원이 권장됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="insight-card insight-success">
            <div class="insight-header">
                <span class="insight-title">✅ 전 센터 누적 오더 정상 진척</span>
                <span class="insight-pill">전체 순항</span>
            </div>
            <div class="insight-body">
                모든 고객센터가 전년 동월 페이스를 상회하며 순조롭게 {target_end_text} 911점 달성 궤도에 안착해 있습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 5. 전년 반기말 실적 연계 911점 도달 진단
    valid_prev_end = cur_df['전년반기말_총점'].dropna()
    if not valid_prev_end.empty:
        prev_end_avg = valid_prev_end.mean()
        pred_avg = cur_df['예상반기총점'].mean()
        st.markdown(f"""
        <div class="insight-card insight-info">
            <div class="insight-header">
                <span class="insight-title">ℹ️ 전년 {target_end_text} 실적 연계 911점 도달 진단</span>
                <span class="insight-pill">반기말 벤치마크</span>
            </div>
            <div class="insight-body">
                전년도 {target_end_text} 최종 실적(평균 {prev_end_avg:.1f}점)을 벤치마크할 때, 현재 {month_in_half}개월차 추세 유지 시 센터별 평균 {target_end_text} 예상 점수는 {pred_avg:.1f}점으로 911점 목표선을 충분히 달성할 수 있습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

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
# PAGE 3: 🎯 센터 진단 & 시뮬레이터
# =============================================================================
elif menu == "🎯 센터 진단":
    st.markdown("### 🎯 센터별 정밀 진단 및 911점 달성 시뮬레이터")
    
    sel_center = st.selectbox("진단할 고객센터를 선택하세요", cur_df['센터명'].unique())
    c_rec = cur_df[cur_df['센터명'] == sel_center].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재 총점", f"{c_rec['총점']:.1f}점")
    col2.metric(f"{target_end_text} 예상총점", f"{c_rec['예상반기총점']:.1f}점")
    col3.metric("911점 도달 판정", c_rec['도달판정'])
    yoy_val = c_rec['전년동월대비_증감']
    col4.metric("전년 동월 대비", f"{'+' if yoy_val > 0 else ''}{yoy_val:.1f}점" if pd.notna(yoy_val) else "N/A")

    st.markdown("---")
    st.markdown("#### 🛠️ 실시간 What-If 시뮬레이터 (반기 마감 911점 달성 목표 시뮬레이션)")
    st.write("안전점검 실점검율 및 주요 KPI 개선 시 예상 총점 변화를 즉시 시뮬레이션합니다.")

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        s_safety = st.slider("안전점검 실점검율 (%)", 0.0, 100.0, float(c_rec['안전점검실점검율']), 0.5)
        s_key = st.slider("중점고객 안전점검율 (%)", 0.0, 100.0, float(c_rec['중점고객안전점검율']), 0.5)
    with s_col2:
        s_contract = st.slider("사용계약율 (%)", 50.0, 100.0, float(c_rec['사용계약율']), 0.5)
        s_resp = st.slider("상담응대율 (%)", 50.0, 100.0, float(c_rec['상담응대율']), 0.5)
    with s_col3:
        s_contrib = st.slider("상담기여도 (%)", 50.0, 100.0, float(c_rec['상담기여도']), 0.5)
        s_sat = st.slider("고객서비스 만족도 (점)", 50.0, 100.0, float(c_rec['고객서비스만족도']), 0.5)

    sim_safety_sc = (s_safety / 100.0) * 550.0
    sim_key_sc = (s_key / 100.0) * 100.0
    sim_contract_sc = calc_contract_score(s_contract)
    sim_resp_sc = (s_resp / 100.0) * 100.0
    sim_contrib_sc = (s_contrib / 100.0) * 100.0
    sim_sat_sc = s_sat
    sim_non_cum = sim_contract_sc + sim_resp_sc + sim_contrib_sc + sim_sat_sc
    sim_total = sim_safety_sc + sim_key_sc + sim_non_cum
    sim_pred = predict_half_end_score(sim_total, cur_month, sim_safety_sc, sim_non_cum, sim_key_sc)

    if sim_pred >= 911.0:
        st.success(f"🎉 **시뮬레이션 결과**: 예상 총점 **{sim_pred:.1f}점**으로 **{target_end_text} 911점 목표를 안정적으로 달성**합니다!")
    else:
        gap = 911.0 - sim_pred
        st.warning(f"⚠️ **시뮬레이션 결과**: 예상 총점 **{sim_pred:.1f}점**으로 911점 도달까지 **{gap:.1f}점 추가 보강**이 필요합니다.")

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
