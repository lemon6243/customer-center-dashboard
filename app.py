# -*- coding: utf-8 -*-
"""
예스코 도시가스 고객센터 성과 대시보드 (Streamlit Application)
- AI Studio React 프리뷰(홈, 성과 분석, 센터 진단, 위험 관리, KPI 히트맵, 심화 분석, 반기 보고)와 100% 동일한 비주얼 & 레이아웃
- 고신뢰성 다중 데이터 로더 (파일 업로더 + 다중 로컬 경로 자동 탐색 + 내장 백업)
- 데이터 전처리 (0~1 소수점 비율 -> 퍼센트 자동 변환, Excel 날짜 시리얼 완벽 대응)
- 전년 동월(YoY) 및 전년 반기말 벤치마크 연계 분석
"""

import streamlit as st
import pandas as pd
import json
import os
import math
from datetime import datetime, timedelta
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    px = None
    go = None
import textwrap

def render_html(html_str: str, in_sidebar: bool = False):
    """HTML 문자열의 선행 들여쓰기를 제거하여 Markdown 코드블록 오인식 방지 및 안전한 렌더링 보장"""
    dedented = textwrap.dedent(html_str).strip()
    if in_sidebar:
        st.sidebar.markdown(dedented, unsafe_allow_html=True)
    else:
        st.markdown(dedented, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 시스템 (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="예스코 고객센터 성과 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 럭셔리 비즈니스 UI (AI Studio React 프리뷰와 100% 일치하는 스타일 시트)
render_html("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    /* Global Font with Icon Font Protection */
    html, body, p, div, span, label, input, button, select, textarea {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Material Symbols & Icon Font Protection (Eliminates _arrow_ text leaks and overlap) */
    .material-symbols-rounded,
    .material-icons,
    [class*="material-symbols"],
    [class*="material-icons"],
    [data-testid="stExpanderToggleIcon"],
    span[data-testid*="Icon"] {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-style: normal !important;
        font-weight: 400 !important;
        font-size: 18px !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        text-rendering: optimizeLegibility !important;
        flex-shrink: 0 !important;
        width: 20px !important;
        height: 20px !important;
    }

    [data-testid="stSidebar"] details summary {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 10px 14px !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
        cursor: pointer !important;
        min-height: 44px !important;
        box-sizing: border-box !important;
    }

    [data-testid="stSidebar"] details summary p {
        margin: 0 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
        white-space: nowrap !important;
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
        gap: 14px;
    }
    .header-title-box h1 {
        margin: 0;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF !important;
    }
    .header-title-box p {
        margin: 6px 0 0 0;
        font-size: 13px;
        opacity: 0.9;
        color: #E2E8F0 !important;
    }
    .header-badge-box {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .badge-pill-header {
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.35);
        color: #FFFFFF;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    
    /* Top Alert Banner Notice */
    .banner-notice {
        background: linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%);
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .banner-notice-text {
        font-size: 13px;
        color: #1E3A8A;
        line-height: 1.55;
    }
    .banner-notice-badge {
        background: #FFFFFF;
        border: 1px solid #BFDBFE;
        color: #0B4EA2;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
    }

    /* Metric Grid Cards */
    .metric-grid-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0B4EA2;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 104px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-grid-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.06);
    }
    .metric-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748B;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #1E293B;
        margin: 6px 0 2px 0;
        letter-spacing: -0.5px;
    }
    .metric-sub {
        font-size: 11px;
        font-weight: 600;
        color: #64748B;
    }

    /* Studio White Box Container */
    .studio-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 22px;
    }
    .studio-box-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        flex-wrap: wrap;
        gap: 8px;
    }
    .studio-box-title {
        font-size: 15px;
        font-weight: 800;
        color: #1E293B;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .studio-box-desc {
        font-size: 12px;
        color: #64748B;
        margin-top: 2px;
    }

    /* Insights Grid */
    .insight-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 14px;
        margin-bottom: 22px;
    }
    .insight-card {
        border-radius: 10px;
        padding: 16px 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-size: 12px;
        line-height: 1.5;
        border-width: 1px;
        border-style: solid;
    }
    .insight-success { background: #F0FDF4; border-color: #BBF7D0; color: #166534; }
    .insight-warning { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }
    .insight-danger  { background: #FEF2F2; border-color: #FECACA; color: #991B1B; }
    .insight-info    { background: #EFF6FF; border-color: #BFDBFE; color: #1E40AF; }
    
    .insight-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .insight-title {
        font-size: 13px;
    }
    .insight-pill {
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid currentColor;
        font-weight: 700;
    }
    .insight-body {
        font-size: 12px;
        opacity: 0.95;
    }

    /* Custom Table Styling */
    .studio-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        text-align: left;
    }
    .studio-table th {
        background: #F8FAFC;
        color: #475569;
        font-weight: 700;
        padding: 10px 14px;
        border-top: 1px solid #E2E8F0;
        border-bottom: 2px solid #E2E8F0;
        white-space: nowrap;
    }
    .studio-table td {
        padding: 11px 14px;
        border-bottom: 1px solid #F1F5F9;
        color: #1E293B;
    }
    .studio-table tr:hover td {
        background: #F8FAFC;
    }
    
    /* Rank Badges */
    .rank-top-badge {
        background: #DCFCE7;
        color: #166534;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
    }
    .rank-bottom-badge {
        background: #FEF3C7;
        color: #92400E;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
    }
    .score-badge {
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
    }
    .score-badge-s { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
    .score-badge-a { background: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; }
    .score-badge-b { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
    .score-badge-c { background: #FFEDD5; color: #C2410C; border: 1px solid #FED7AA; }
    .score-badge-d { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }

    /* Simulator Result Banner */
    .sim-result-bar {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 14px;
    }

    /* Risk Center Card */
    .risk-center-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: transform 0.15s ease;
    }
    .risk-center-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Sidebar Layout & Overlap Prevention (Match React Preview) */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #DCE3EA !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #DCE3EA !important;
        border-radius: 8px !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] details summary {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 10px 14px !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
        cursor: pointer !important;
        border-bottom: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] details[open] summary {
        border-bottom: 1px solid #E2E8F0 !important;
        background: #F8FAFC !important;
    }
    [data-testid="stSidebar"] details summary p {
        margin: 0 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
    }
    [data-testid="stSidebar"] .stFileUploader {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

</style>
""")


# -----------------------------------------------------------------------------
# 2. 데이터 정규화 및 점수 산출 로직 (React scoreCalculator.ts와 100% 동일)
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

def to_percentage(rate):
    """0~1 사이 소수 비율인 경우 100을 곱해 % 단위로 자동 변환"""
    if rate is None or pd.isna(rate):
        return 0.0
    try:
        num = float(rate)
        if 0.0 <= num <= 1.05:
            return num * 100.0
        return num
    except:
        return 0.0

def calc_contract_score(contract_rate):
    p = to_percentage(contract_rate)
    if p >= 90.0:
        return 50.0
    elif p >= 80.0:
        return 45.0
    elif p >= 70.0:
        return 40.0
    return 35.0

def predict_half_end_score(current_score, month, safety_score=None, non_cum_score=None, key_score=None, adjust_score=0):
    m = month if month <= 6 else month - 6
    if m >= 6:
        return current_score
    pace_ratio = max(0.1, m / 6.0)
    if safety_score is not None and key_score is not None and non_cum_score is not None:
        projected_safety = min(550.0, safety_score / pace_ratio)
        projected_key = min(100.0, key_score / pace_ratio)
        projected_total = projected_safety + projected_key + non_cum_score + adjust_score
        return round(min(1000.0, max(0.0, projected_total)), 1)
    return round((current_score * 0.85) + ((current_score / pace_ratio) * 0.15), 1)



def generate_automated_insights(cur_df, df_all, month_in_half, target_end_text):
    total_centers = len(cur_df)
    avg_score = cur_df['총점'].mean()
    avg_safety = cur_df['안전점검실점검율'].mean()
    avg_key = cur_df['중점고객안전점검율'].mean()
    benchmark_safety_rate = (month_in_half / 6.0) * 92.0

    valid_yoy = cur_df['전년동월_총점'].dropna()
    prev_year_avg = valid_yoy.mean() if not valid_yoy.empty else None
    yoy_diff = (avg_score - prev_year_avg) if prev_year_avg is not None else None

    on_track_count = len(cur_df[cur_df['예상반기총점'] >= 911.0])
    on_track_rate = (on_track_count / total_centers * 100) if total_centers > 0 else 0
    caution_count = total_centers - on_track_count

    insights = []
    # 1. 911점 도달 진단
    if on_track_count >= total_centers * 0.8:
        insights.append({
            'type': 'success',
            'title': f'{target_end_text} 911점 도달 정상 궤도 ({on_track_count}개소)',
            'message': f'현재 {month_in_half}개월차 기준 전체 {total_centers}개 센터 중 {on_track_count}개소({on_track_rate:.1f}%)가 {target_end_text} 911점 달성 목표선 대비 안정적인 추진 페이스를 보이고 있습니다.',
            'badge': '911점 궤도 정상'
        })
    else:
        insights.append({
            'type': 'warning',
            'title': f'{target_end_text} 911점 도달 집중 관리 ({caution_count}개소 보강 필요)',
            'message': f'현재 {month_in_half}개월차 기준 {caution_count}개 센터가 {target_end_text} 911점 도달 페이스에 다소 지연을 보이고 있습니다. 안전점검 오더 처리 속도를 조기 보강해야 합니다.',
            'badge': '페이스 관리 필요'
        })

    # 2. YoY 진단
    if prev_year_avg is not None and yoy_diff is not None:
        yoy_valid = cur_df.dropna(subset=['전년동월대비_증감'])
        top_gain = yoy_valid.sort_values(by='전년동월대비_증감', ascending=False).iloc[0] if not yoy_valid.empty else None
        top_text = f' 특히 {top_gain["센터명"]} 센터가 전년 대비 +{top_gain["전년동월대비_증감"]:.1f}점 상승하여 가장 두드러집니다.' if top_gain is not None and top_gain['전년동월대비_증감'] > 0 else ''
        if yoy_diff >= 0:
            insights.append({
                'type': 'success',
                'title': '전년 동월 대비 종합 성과 상승',
                'message': f'현재 {month_in_half}월차 평균 총점({avg_score:.1f}점)은 전년 동월({prev_year_avg:.1f}점) 대비 +{yoy_diff:.1f}점 상회하여 우수한 누적 흐름을 보이고 있습니다.{top_text}',
                'badge': f'YoY +{yoy_diff:.1f}점'
            })
        else:
            insights.append({
                'type': 'warning',
                'title': '전년 동월 대비 성과 지연 감지',
                'message': f'현재 {month_in_half}월차 평균 총점({avg_score:.1f}점)이 전년 동월({prev_year_avg:.1f}점) 대비 {abs(yoy_diff):.1f}점 다소 뒤처져 있어, {target_end_text} 911점 달성을 위한 조기 오더 드라이브가 필요합니다.',
                'badge': f'YoY {yoy_diff:.1f}점'
            })

    # 3. 안전점검 진단
    safety_diff = avg_safety - benchmark_safety_rate
    is_safety_good = safety_diff >= -3.0
    insights.append({
        'type': 'success' if is_safety_good else 'info',
        'title': '안전점검 실점검율 진척 현황',
        'message': f'현재 {month_in_half}개월차 기준 평균 실점검율은 {avg_safety:.1f}%(중점안전점검 {avg_key:.1f}%)입니다. 계획 대비 {"양호하게 추진되고 있습니다." if is_safety_good else "일부 센터의 추가 점검 관리가 필요합니다."}',
        'badge': '계획대비 양호' if is_safety_good else '진척 관리 필요'
    })

    # 4. 누적 지연 센터 코칭 필요
    lag_centers = cur_df[(cur_df['전년동월대비_증감'] < -10) | (cur_df['예상반기총점'] < 905) | (cur_df['오더진척상태'] == '지연')]
    if not lag_centers.empty:
        lag_names = ', '.join(lag_centers['센터명'].head(3).tolist())
        worst_yoy = lag_centers.sort_values(by='전년동월대비_증감', ascending=True).iloc[0] if not lag_centers.dropna(subset=['전년동월대비_증감']).empty else None
        worst_text = f' ({worst_yoy["센터명"]} 센터 전년비 {worst_yoy["전년동월대비_증감"]:.1f}점)' if worst_yoy is not None and pd.notna(worst_yoy['전년동월대비_증감']) else ''
        insights.append({
            'type': 'warning',
            'title': '전년 동월 대비 누적 지연 센터 코칭 필요',
            'message': f'{lag_names} 등 {len(lag_centers)}개 센터는 전년 동월 대비 오더 누적 페이스가 지연되고 있거나 {target_end_text} 911점 도달에 주의가 요구됩니다.{worst_text} 해당 센터의 원활한 오더 처리를 위한 맞춤형 현장 지원이 권장됩니다.',
            'badge': f'코칭 대상 {len(lag_centers)}개소'
        })
    else:
        insights.append({
            'type': 'success',
            'title': '전 센터 누적 오더 정상 진척',
            'message': f'모든 고객센터가 전년 동월 페이스를 상회하며 순조롭게 {target_end_text} 911점 달성 궤도에 안착해 있습니다.',
            'badge': '전체 순항'
        })

    # 5. 전년 반기말 실적 연계 911점 도달 진단
    prev_half_records = cur_df.dropna(subset=['전년반기말_총점'])
    if not prev_half_records.empty:
        prev_end_avg = prev_half_records['전년반기말_총점'].mean()
        pred_avg = cur_df['예상반기총점'].mean()
        insights.append({
            'type': 'info',
            'title': f'전년 {target_end_text} 실적 연계 911점 도달 진단',
            'message': f'전년도 {target_end_text} 최종 실적(평균 {prev_end_avg:.1f}점, 전 센터 911점 도달)을 벤치마크할 때, 현재 {month_in_half}개월차 추세 유지 시 센터별 평균 {target_end_text} 예상 점수는 {pred_avg:.1f}점으로 911점 목표선을 충분히 달성할 수 있습니다.',
            'badge': '반기말 벤치마크'
        })

    return insights

def get_score_badge(score, expected_score=None, is_interim=False):
    """
    고객센터 평가 등급 판정:
    - 반기 마감(6월/12월, 즉 최종 확정월): 당월 총점 기준으로 최종 판정
    - 반기 진행 중(1~5개월차, 예: 9월=하반기 3개월차 50% 진행):
      누적 오더 진행 속도 및 12월말(또는 6월말) 예상 총점을 기준으로 현시점 평가 등급 산출
      (예: 50% 시점 총점 824.5점은 1,000점 만점 기준 960~1,000점 페이스이므로 S등급 최우수 판정)
    """
    eval_s = expected_score if (is_interim and expected_score is not None and not (isinstance(expected_score, float) and math.isnan(expected_score))) else score

    if eval_s >= 930:
        return "S", "score-badge-s", "최우수" if not is_interim else "최우수 (유력)"
    elif eval_s >= 911:
        return "A", "score-badge-a", "우수" if not is_interim else "우수 (달성유력)"
    elif eval_s >= 895:
        return "B", "score-badge-b", "보통" if not is_interim else "보통 (정상궤도)"
    elif eval_s >= 875:
        return "C", "score-badge-c", "주의" if not is_interim else "주의 (오더보강)"
    return "D", "score-badge-d", "미달" if not is_interim else "미달 위험"

@st.cache_data
def load_data_from_path(file_path):
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        try:
            df = pd.read_excel(file_path)
            return df.to_dict(orient='records')
        except Exception:
            # zipfile fallback for xlsx
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_path, 'r') as z:
                sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
                ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
                strings = []
                for si in sst.findall(f'{ns}si'):
                    t = si.find(f'{ns}t')
                    if t is not None:
                        strings.append(t.text or '')
                    else:
                        strings.append(''.join([elem.text or '' for elem in si.iter(f'{ns}t')]))
                sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                rows = sheet.findall(f'.//{ns}row')
                header_row = rows[0]
                col_map = {}
                for c in header_row.findall(f'{ns}c'):
                    ref = c.attrib.get('r', '')
                    col = ''.join([ch for ch in ref if ch.isalpha()])
                    t = c.attrib.get('t')
                    v = c.find(f'{ns}v')
                    val = v.text if v is not None else ''
                    if t == 's':
                        val = strings[int(val)] if val.isdigit() and int(val) < len(strings) else val
                    col_map[col] = val
                recs = []
                for r in rows[1:]:
                    rec = {}
                    for c in r.findall(f'{ns}c'):
                        ref = c.attrib.get('r', '')
                        col = ''.join([ch for ch in ref if ch.isalpha()])
                        h = col_map.get(col)
                        if not h:
                            continue
                        t = c.attrib.get('t')
                        v = c.find(f'{ns}v')
                        val = v.text if v is not None else ''
                        if t == 's':
                            val = strings[int(val)] if val.isdigit() and int(val) < len(strings) else val
                        else:
                            try:
                                val = float(val) if '.' in val else int(val)
                            except ValueError:
                                pass
                        rec[h] = val
                    if rec:
                        recs.append(rec)
                return recs
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

def load_local_records():
    """
    [데이터 우선순위 정책]
    1순위: 사용자가 항상 업로드/커밋하는 data/latest_data.xlsx 파일을 최우선으로 탐색 및 로드합니다.
    2순위: data/latest_data.json 백업 파일
    3순위: 내장 기본 데이터
    """
    # 1순위: latest_data.xlsx 탐색 (엑셀 파일 최우선)
    excel_candidates = [
        os.path.join(os.path.dirname(__file__), 'data', 'latest_data.xlsx'),
        os.path.join(os.path.dirname(__file__), 'latest_data.xlsx'),
        'data/latest_data.xlsx',
        'latest_data.xlsx',
        os.path.join(os.path.dirname(__file__), 'data', 'latest_data.xls'),
        'data/latest_data.xls',
    ]
    for p in excel_candidates:
        if os.path.exists(p):
            try:
                data = load_data_from_path(p)
                if data and len(data) > 0:
                    return data
            except Exception:
                continue

    # 2순위: JSON 데이터 파일 탐색
    json_candidates = [
        os.path.join(os.path.dirname(__file__), 'data', 'latest_data.json'),
        os.path.join(os.path.dirname(__file__), 'src', 'data', 'latest_data.json'),
        os.path.join(os.path.dirname(__file__), 'latest_data.json'),
        'data/latest_data.json',
        'src/data/latest_data.json',
        'latest_data.json',
    ]
    for p in json_candidates:
        if os.path.exists(p):
            try:
                data = load_data_from_path(p)
                if data and len(data) > 0:
                    return data
            except Exception:
                continue

    # 3순위: 비상용 내장 목업 데이터
    centers = ["자양", "휘경", "중부", "동부", "서대문", "마포", "용산", "성동", "광진", "노원", "도봉", "강북", "성북", "중랑", "동대문", "남양주", "구리", "가평", "양평", "포천", "덕소/양평", "퇴계원/별내", "의정부"]
    fallback = []
    for c in centers:
        fallback.append({
            "센터명": c,
            "평가월": "2026-09-01",
            "안전점검실점검율": 0.48,
            "중점고객안전점검율": 0.52,
            "사용계약율": 0.93,
            "상담응대율": 1.0,
            "상담기여도": 1.0,
            "고객서비스만족도": 94.5,
            "민원대응적정성": 0,
            "주의경고": 0,
            "가점": 0,
            "총점": 650.0
        })
    return fallback

@st.cache_data
def process_dataframe(raw_list):
    df = pd.DataFrame(raw_list)
    # 날짜 정규화
    df['정규평가월'] = df['평가월'].apply(normalize_date_string)
    df['평가연월'] = df['정규평가월'].str.slice(0, 7)
    df['연도'] = df['정규평가월'].apply(lambda x: int(x[:4]))
    df['월'] = df['정규평가월'].apply(lambda x: int(x[5:7]))
    df['반기'] = df['월'].apply(lambda m: '상반기' if m <= 6 else '하반기')
    df['반기월차'] = df['월'].apply(lambda m: m if m <= 6 else m - 6)

    # 비율 지표 to_percentage() 적용 (0.15 -> 15.0%)
    df['안전점검실점검율'] = df['안전점검실점검율'].apply(to_percentage)
    df['중점고객안전점검율'] = df['중점고객안전점검율'].apply(to_percentage)
    df['사용계약율'] = df['사용계약율'].apply(to_percentage)
    df['상담응대율'] = df['상담응대율'].apply(to_percentage)
    df['상담기여도'] = df['상담기여도'].apply(to_percentage)
    df['고객서비스만족도'] = pd.to_numeric(df.get('고객서비스만족도', 0), errors='coerce').fillna(0)

    # 배점 산출
    df['안전점검_점수'] = (df['안전점검실점검율'] / 100.0) * 550.0
    df['중점고객_점수'] = (df['중점고객안전점검율'] / 100.0) * 100.0
    df['사용계약_점수'] = df['사용계약율'].apply(calc_contract_score)
    df['상담응대_점수'] = (df['상담응대율'] / 100.0) * 100.0
    df['상담기여_점수'] = (df['상담기여도'] / 100.0) * 100.0
    df['만족도_점수'] = df['고객서비스만족도']
        
    calc_total = (
        df['안전점검_점수'] +
        df['중점고객_점수'] +
        df['사용계약_점수'] +
        df['상담응대_점수'] +
        df['상담기여_점수'] +
        df['만족도_점수']
    )
    # 원시 데이터에 신뢰할 수 있는 총점이 있으면 우선 유지, 없으면 계산값 적용
    if '총점' in df.columns:
        df['총점'] = pd.to_numeric(df['총점'], errors='coerce')
        df['총점'] = df['총점'].fillna(calc_total)
    else:
        df['총점'] = calc_total

    # 전년 동월 및 반기말 비교 벤치마크 맵 구축
    all_recs = df.to_dict(orient='records')
    yoy_map = {}
    py_half_end_map = {}
    for r in all_recs:
        key = (r['연도'], r['월'], r['센터명'])
        yoy_map[key] = r['총점']
        if r['월'] in [6, 12]:
            py_half_end_map[(r['연도'], r['월'], r['센터명'])] = r['총점']

    def calc_realistic_projected_score(row):
        """전년 12월말(또는 6월말) 실적 및 전년 동월 대비 누적 증감(YoY) 페이스를 100% 기준으로 하는 직관적/고신뢰성 예측 모델"""
        cur_s = float(row['총점'])
        m = row['반기월차']
        if m >= 6:
            return round(cur_s, 1)
        
        target_m = 6 if row['월'] <= 6 else 12
        py_end = py_half_end_map.get((row['연도'] - 1, target_m, row['센터명']))
        py_cur = yoy_map.get((row['연도'] - 1, row['월'], row['센터명']))
        
        # 1순위: 전년 12월말 실적(py_end)과 전년 동월 대비 증감(yoy_d)이 있는 경우
        # 예: 용산센터 (전년 12월말 929.4점, 전년 8월대비 -24.1점) -> 12월말 예상 = 929.4 - 24.1 = 905.3점 (미달 위험)
        if py_end is not None and py_cur is not None:
            yoy_d = cur_s - py_cur
            predicted = py_end + yoy_d
            return round(min(1000.0, max(0.0, predicted)), 1)
        
        # 2순위: 전년 반기말 실적만 있는 경우
        if py_end is not None:
            return round(min(1000.0, max(0.0, py_end)), 1)
        
        # 3순위: 신규 센터 등 전년 벤치마크가 없는 경우 진도율 기반 추정
        pace_ratio = max(0.1, m / 6.0)
        non_cum = row['사용계약_점수'] + row['상담응대_점수'] + row['상담기여_점수'] + row['만족도_점수']
        projected_safety = min(550.0, row['안전점검_점수'] / pace_ratio)
        projected_key = min(100.0, row['중점고객_점수'] / pace_ratio)
        base_extrapolation = projected_safety + projected_key + non_cum
        return round(min(1000.0, max(0.0, base_extrapolation)), 1)

    df['예상반기총점'] = df.apply(calc_realistic_projected_score, axis=1)

    def enrich(row):
        py = yoy_map.get((row['연도'] - 1, row['월'], row['센터명']))
        target_m = 6 if row['월'] <= 6 else 12
        py_end = py_half_end_map.get((row['연도'] - 1, target_m, row['센터명']))
        yoy_diff = (row['총점'] - py) if py is not None else None
        
        # 도달 판정
        if row['예상반기총점'] < 905:
            judgment = '위험'
        elif row['예상반기총점'] < 915:
            judgment = '주의'
        else:
            judgment = '정상궤도'

        # 오더 진척 상태
        m_in_h = row['반기월차']
        bm = (m_in_h / 6.0) * 92.0
        if row['안전점검실점검율'] < bm - 3.0:
            order_status = '지연'
        elif row['안전점검실점검율'] < bm:
            order_status = '보통'
        else:
            order_status = '양호'

        return pd.Series([py, yoy_diff, py_end, judgment, order_status])

    df[['전년동월_총점', '전년동월대비_증감', '전년반기말_총점', '도달판정', '오더진척상태']] = df.apply(enrich, axis=1)
    return df


# 사이드바 데이터 상태 관리 (커스텀 업로드 레코드 유지)
if 'custom_records' not in st.session_state:
    st.session_state.custom_records = None

if st.session_state.custom_records is not None:
    raw_records = st.session_state.custom_records
else:
    raw_records = load_local_records()

df_all = process_dataframe(raw_records)

# -----------------------------------------------------------------------------
# 4. 사이드바 네비게이션 및 평가월 선택 (Studio 프리뷰와 100% 동일한 순서 & 디자인)
# -----------------------------------------------------------------------------
all_months = sorted(list(df_all['평가연월'].unique()))
latest_month = all_months[-1] if all_months else "2026-09"

# [1] 사이드바 최상단 브랜드 로고 (프리뷰와 동일)
render_html("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:18px; padding-bottom:12px; border-bottom:1px solid #E2E8F0;">
    <div style="background:#0B4EA2; color:white; width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:16px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        Y
    </div>
    <div>
        <div style="font-size:14px; font-weight:800; color:#0B4EA2; line-height:1.2;">예스코 고객센터</div>
        <div style="font-size:11px; color:#64748B;">성과 평가 관리 시스템</div>
    </div>
</div>
""", in_sidebar=True)

# [2] 메인 메뉴 라디오 버튼 (프리뷰와 1:1 일치)
menu = st.sidebar.radio(
    "메인 메뉴",
    ["🏠 홈", "📊 성과 분석", "🎯 센터 진단", "⚠️ 위험 관리", "🌡️ KPI 히트맵", "🔬 심화 분석", "📑 상반기 보고"]
)

# [3] 평가월 선택 (2026년 9월 등 최신월 자동 기본 선택)
default_idx = len(all_months) - 1 if all_months else 0
month_display_map = {m: f"{m} (★최신)" if m == latest_month else m for m in all_months}

selected_month = st.sidebar.selectbox(
    "📅 평가월 선택",
    options=all_months,
    index=default_idx,
    format_func=lambda m: month_display_map.get(m, m)
)

cur_df = df_all[df_all['평가연월'] == selected_month].copy()
if cur_df.empty:
    cur_df = df_all.copy()

cur_year = cur_df['연도'].iloc[0]
cur_month = cur_df['월'].iloc[0]
half_name = "상반기" if cur_month <= 6 else "하반기"
month_in_half = cur_month if cur_month <= 6 else cur_month - 6
target_end_text = "6월말" if cur_month <= 6 else "12월말"
progress_pct = int((month_in_half / 6) * 100)
benchmark_safety = (month_in_half / 6) * 92.0

# [4] 데이터 현황 정보 카드 (프리뷰와 100% 일치)
render_html(f"""
<div style="background:white; border:1px solid #DCE3EA; border-radius:10px; padding:12px; margin-top:12px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
    <div style="font-size:12px; font-weight:700; color:#172B4D; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span>📊 데이터 현황</span>
        <span style="width:8px; height:8px; border-radius:50%; background:#10B981; display:inline-block;"></span>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>기준월:</span> <strong style="color:#172B4D;">{cur_year}년 {cur_month}월</strong>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>진행 경과:</span> <span style="color:#0B4EA2; font-weight:600;">{half_name} {month_in_half}/6개월차 ({progress_pct}%)</span>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>대상 센터:</span> <strong style="color:#172B4D;">{len(cur_df)}개소</strong>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between;">
        <span>전체 레코드:</span> <span>{len(df_all):,}건</span>
    </div>
</div>
""", in_sidebar=True)

# [5] 엑셀 데이터 관리 섹션 (프리뷰와 동일하게 데이터 현황 카드 하단에 독립 배치)
with st.sidebar.expander("📁 엑셀 데이터 교체 & 관리", expanded=False):
    uploaded_file = st.file_uploader(
        "데이터 파일 교체 (.xlsx / .json)",
        type=['xlsx', 'xls', 'json'],
        key="sidebar_data_uploader",
        help="최신 엑셀 또는 JSON 데이터를 직접 업로드하여 분석할 수 있습니다."
    )
    if uploaded_file is not None:
        try:
            custom_data = parse_uploaded_bytes(uploaded_file.getvalue(), uploaded_file.name)
            if custom_data:
                st.session_state.custom_records = custom_data
                st.success(f"✅ 파일 로드 성공: {len(custom_data)}건")
                st.rerun()
        except Exception as e:
            st.error(f"파일 파싱 실패: {e}")

    if st.button("기본 데이터로 복원", use_container_width=True, key="restore_default_btn"):
        st.session_state.custom_records = None
        st.cache_data.clear()
        st.success("기본 데이터로 복원되었습니다.")
        st.rerun()

# [6] 배점 규칙 & 기준 안내 (사이드바 하단에 깔끔하게 배치하여 겹침 차단)
with st.sidebar.expander("⚖️ 배점 규칙 & 기준 안내", expanded=False):
    st.markdown("""
    **🎯 종합 합격 및 재계약 기준**
    - 반기 합격: **911점 이상** (1,000점 만점)
    - 연간 재계약: 상·하반기 합산 **1,822점 이상**
    - 판정: 911점 이상(안전/달성), 895~910점(주의), 895점 미만(위험)

    ---
    **📊 6대 핵심 KPI 배점**
    - **안전점검실점검율**: 550점 (누적형)
    - **중점고객안전점검율**: 100점 (누적형)
    - **사용계약율**: 50점 (A:50, B:45, C:40, D:35)
    - **상담응대율**: 100점 (당월형)
    - **상담기여도**: 100점 (당월형)
    - **고객서비스만족도**: 100점 (당월형)
    - *가감점: 민원대응(±5), 주의경고(-1~-5), 가점(+5)*
    """)

# [7] 사이드바 푸터 버전 표기
render_html("""
<div style="text-align:center; font-size:10px; color:#94A3B8; margin-top:16px; padding-top:8px; border-top:1px solid #E2E8F0;">
    YESCO Customer Dashboard v2.1
</div>
""", in_sidebar=True)

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
    lag_centers = cur_df[(cur_df['전년동월대비_증감'] < -10) | (cur_df['예상반기총점'] < 905) | (cur_df['오더진척상태'] == '지연')]
    safety_diff = avg_safety - benchmark_safety
    is_safety_good = safety_diff >= -3.0

    # 1. 고객센터 종합 진단 배너
    render_html(f"""
    <div class="banner-notice">
        <div class="banner-notice-text">
            <strong>💡 고객센터 종합 진단 현황 ({month_in_half}개월차)</strong><br/>
            현재 <strong>{month_in_half}개월차 기준 평균 실점검율은 {avg_safety:.1f}%</strong>(중점안전점검 {avg_key:.1f}%)입니다. 계획 대비 양호하게 추진 중이며, 전년 동월 및 <strong>{target_end_text} 911점 달성 목표선</strong>을 기준으로 센터별 진척 페이스를 종합 모니터링하고 있습니다.
        </div>
        <div class="banner-notice-badge">
            {half_name} {month_in_half}/6개월차 ({progress_pct}% 진척)
        </div>
    </div>
    """)

    # 2. 4대 핵심 지표 카드
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        yoy_str = f"전년 동월({prev_avg:.1f}점) 대비 {'+' if (yoy_diff or 0) >= 0 else ''}{(yoy_diff or 0):.1f}점" if yoy_diff is not None else f"{half_name} {month_in_half}개월차"
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #0B4EA2;">
            <div class="metric-title"><span>전체 센터 평균 총점</span> <span>📊</span></div>
            <div class="metric-value">{avg_score:.1f}점</div>
            <div class="metric-sub" style="color: {'#16A34A' if (yoy_diff or 0) >= 0 else '#DC2626'};">{yoy_str}</div>
        </div>
        """)
    with c2:
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #10B981;">
            <div class="metric-title"><span>{target_end_text} 911점 예상 달성률</span> <span>🎯</span></div>
            <div class="metric-value">{on_track_rate:.1f}%</div>
            <div class="metric-sub" style="color: #059669;">총 {total_centers}개소 중 {on_track_count}개소 정상 궤도</div>
        </div>
        """)
    with c3:
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #F59E0B;">
            <div class="metric-title"><span>누적 지연 / 중점 코칭 센터</span> <span>⚠️</span></div>
            <div class="metric-value">{len(lag_centers)}개소</div>
            <div class="metric-sub" style="color: #D97706;">전년비 지연 및 911점 미달 위험</div>
        </div>
        """)
    with c4:
        safety_status_text = "양호" if is_safety_good else "관리 필요"
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #6366F1;">
            <div class="metric-title"><span>안전점검 평균 실점검율</span> <span>⏱️</span></div>
            <div class="metric-value">{avg_safety:.1f}%</div>
            <div class="metric-sub" style="color: #4F46E5;">계획({benchmark_safety:.1f}%) 대비 {safety_status_text}</div>
        </div>
        """)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 3. 핵심 인사이트 및 자동 진단 (Studio와 100% 동일한 5대 전항목 카드 렌더링)
    render_html(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <div style="font-size:15px; font-weight:800; color:#1E293B;">💡 핵심 인사이트 및 자동 진단</div>
        <span style="font-size:11px; background:#F1F5F9; color:#475569; padding:3px 10px; border-radius:12px; font-weight:600;">전년 동월 및 {target_end_text} 벤치마크 연계</span>
    </div>
    """)

    all_insights = generate_automated_insights(cur_df, df_all, month_in_half, target_end_text)

    # 1행: 1, 2, 3번 인사이트 (3열)
    in_row1 = st.columns(3)
    for idx, card in enumerate(all_insights[:3]):
        with in_row1[idx]:
            c_type = card['type']
            cls_name = f"insight-{c_type}"
            render_html(f"""
            <div class="insight-card {cls_name}" style="min-height: 115px; margin-bottom: 12px;">
                <div class="insight-header">
                    <span class="insight-title">{card['title']}</span>
                    <span class="insight-pill">{card['badge']}</span>
                </div>
                <div class="insight-body">
                    {card['message']}
                </div>
            </div>
            """)

    # 2행: 4, 5번 인사이트 (2열 그리드로 균형감 있게 배치)
    if len(all_insights) > 3:
        in_row2 = st.columns(2)
        for idx, card in enumerate(all_insights[3:]):
            with in_row2[idx]:
                c_type = card['type']
                cls_name = f"insight-{c_type}"
                render_html(f"""
                <div class="insight-card {cls_name}" style="min-height: 110px; margin-bottom: 12px;">
                    <div class="insight-header">
                        <span class="insight-title">{card['title']}</span>
                        <span class="insight-pill">{card['badge']}</span>
                    </div>
                    <div class="insight-body">
                        {card['message']}
                    </div>
                </div>
                """)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. 차트 & 랭킹 2열 레이아웃
    col_chart, col_rank = st.columns([3, 2])
    
    with col_chart:
        render_html(f"""
        <div class="studio-box-header">
            <div>
                <div class="studio-box-title">전체 센터 누적 총점 분포 및 {target_end_text} 도달 궤도</div>
                <div class="studio-box-desc">🔵 정상 궤도(915점 이상) | 🟠 주의(905~914점) | 🔴 위험/지연(905점 미만)</div>
            </div>
            <span style="font-size:11px; background:#F1F5F9; padding:4px 8px; border-radius:6px; font-weight:700;">{cur_year}년 {cur_month}월</span>
        </div>
        """)

        sorted_df = cur_df.sort_values(by="총점", ascending=False)
        colors = []
        for _, r in sorted_df.iterrows():
            if r['도달판정'] == '위험' or r['예상반기총점'] < 905:
                colors.append('#D92D20')
            elif r['도달판정'] == '주의' or r['예상반기총점'] < 915:
                colors.append('#D48A00')
            else:
                colors.append('#0B4EA2')

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=sorted_df['센터명'],
            y=sorted_df['총점'],
            marker_color=colors,
            text=[f"{v:.1f}" for v in sorted_df['총점']],
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>총점: %{y:.1f}점<extra></extra>"
        ))
        # 당월 평균선
        fig_bar.add_hline(y=avg_score, line_dash="dash", line_color="#0B4EA2", annotation_text=f"당월평균 ({avg_score:.1f})")
        # 전년 동월선
        if prev_avg is not None:
            fig_bar.add_hline(y=prev_avg, line_dash="dot", line_color="#8E44AD", annotation_text=f"전년동월 ({prev_avg:.1f})")
        # 최종 목표 911선 (5개월차 이상 또는 직관 비교용)
        if month_in_half >= 5:
            fig_bar.add_hline(y=911, line_dash="dash", line_color="#10B981", annotation_text="최종목표 (911)")

        min_s = max(0, int(sorted_df['총점'].min() - 30))
        max_s = min(1000, int(sorted_df['총점'].max() + 30))
        fig_bar.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=25, b=60),
            xaxis_tickangle=-40,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[min_s, max_s], gridcolor='#F1F5F9')
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_rank:
        render_html(f"""
        <div class="studio-box-header">
            <div class="studio-box-title">🏆 센터별 성과 및 전년비 증감</div>
            <span style="font-size:11px; color:#64748B;">누적 순위</span>
        </div>
        """)

        top3 = sorted_df.head(3)
        bottom3 = sorted_df.tail(3).iloc[::-1]

        st.markdown("<div style='font-size:12px; font-weight:800; color:#15803D; margin-bottom:6px;'>▲ 상위 우수 센터 (Top 3)</div>", unsafe_allow_html=True)
        for i, (_, r) in enumerate(top3.iterrows()):
            yoy_badge = f"YoY {'+' if r['전년동월대비_증감'] >= 0 else ''}{r['전년동월대비_증감']:.1f}" if pd.notna(r['전년동월대비_증감']) else f"안전: {r['안전점검실점검율']:.0f}%"
            render_html(f"""
            <div style="background:#F0FDF4; border:1px solid #DCFCE7; border-radius:8px; padding:9px 14px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="rank-top-badge">{i+1}</span>
                    <strong style="color:#1E293B; font-size:13px;">{r['센터명']}</strong>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; color:#15803D; font-size:13px;">{r['총점']:.1f}점</div>
                    <div style="font-size:10px; color:#166534;">{yoy_badge}</div>
                </div>
            </div>
            """)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:12px; font-weight:800; color:#B45309; margin-bottom:6px;'>▼ 코칭 집중 관리 센터 (Bottom 3)</div>", unsafe_allow_html=True)
        for i, (_, r) in enumerate(bottom3.iterrows()):
            yoy_badge = f"YoY {'+' if r['전년동월대비_증감'] >= 0 else ''}{r['전년동월대비_증감']:.1f}" if pd.notna(r['전년동월대비_증감']) else f"안전: {r['안전점검실점검율']:.0f}%"
            render_html(f"""
            <div style="background:#FFFBEB; border:1px solid #FEF3C7; border-radius:8px; padding:9px 14px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="rank-bottom-badge">{len(sorted_df) - i}</span>
                    <strong style="color:#1E293B; font-size:13px;">{r['센터명']}</strong>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; color:#B45309; font-size:13px;">{r['총점']:.1f}점</div>
                    <div style="font-size:10px; color:#92400E;">{yoy_badge}</div>
                </div>
            </div>
            """)


# =============================================================================
# PAGE 2: 📊 성과 분석 (Studio PerformancePage.tsx 100% 동일)
# =============================================================================
elif menu == "📊 성과 분석":
    render_html(f"""
    <div class="studio-box-header">
        <div>
            <div class="studio-box-title">📈 센터별 월별 총점 추이 그래프</div>
            <div class="studio-box-desc">전체 평균 및 개별 센터의 월별 성과 궤적 비교</div>
        </div>
    </div>
    """)

    # 센터 선택 드롭다운
    all_centers = sorted(list(df_all['센터명'].unique()))
    center_opts = ["전체평균"] + all_centers
    sel_trend_center = st.selectbox("비교 분석 센터 선택", center_opts, index=0)

    # 월별 추이 데이터 집계
    trend_data = []
    for m in all_months:
        m_df = df_all[df_all['평가연월'] == m]
        if not m_df.empty:
            avg_val = m_df['총점'].mean()
            row_dict = {"month": m, "전체평균": round(avg_val, 1)}
            if sel_trend_center != "전체평균":
                c_val = m_df[m_df['센터명'] == sel_trend_center]
                row_dict[sel_trend_center] = round(c_val['총점'].iloc[0], 1) if not c_val.empty else None
            trend_data.append(row_dict)
    
    trend_df = pd.DataFrame(trend_data)
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df['month'],
        y=trend_df['전체평균'],
        mode='lines+markers',
        name='전체평균',
        line=dict(color='#64748B', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    if sel_trend_center != "전체평균" and sel_trend_center in trend_df.columns:
        fig_trend.add_trace(go.Scatter(
            x=trend_df['month'],
            y=trend_df[sel_trend_center],
            mode='lines+markers',
            name=f'{sel_trend_center} 센터',
            line=dict(color='#0B4EA2', width=3),
            marker=dict(size=8, color='#0B4EA2')
        ))
    fig_trend.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='#F1F5F9'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 센터별 종합 평가표 (HTML 커스텀 테이블)
    render_html(f"""
    <div class="studio-box-header">
        <div>
            <div class="studio-box-title">📋 {cur_year}년 {cur_month}월 고객센터별 종합 평가표</div>
            <div class="studio-box-desc">전체 {len(cur_df)}개 센터 실적 데이터 및 6대 KPI 달성 현황 (진행월 평가는 연말 누적 페이스 기준 적용)</div>
        </div>
    </div>
    """)

    search_keyword = st.text_input("🔍 센터명 검색", "", placeholder="예: 자양, 휘경...")
    filtered_cur_df = cur_df[cur_df['센터명'].str.contains(search_keyword)] if search_keyword else cur_df
    sorted_table = filtered_cur_df.sort_values(by="총점", ascending=False)

    table_rows = []
    is_interim = (month_in_half < 6)
    for rank, (_, r) in enumerate(sorted_table.iterrows(), start=1):
        exp_score = r.get('예상반기총점', r['총점'])
        g, cls, desc = get_score_badge(r['총점'], expected_score=exp_score, is_interim=is_interim)
        row_html = (
            f'<tr>'
            f'<td style="font-weight:700; color:#64748B;">{rank}</td>'
            f'<td style="font-weight:800; color:#1E293B;">{r["센터명"]}</td>'
            f'<td style="text-align:right; font-weight:800; color:#0B4EA2;">{r["총점"]:.1f}</td>'
            f'<td style="text-align:center;"><span class="score-badge {cls}">{g}등급 ({desc})</span></td>'
            f'<td style="text-align:right; color:#475569;">{r["안전점검_점수"]:.1f} <span style="font-size:10px; color:#94A3B8;">({r["안전점검실점검율"]:.0f}%)</span></td>'
            f'<td style="text-align:right; color:#475569;">{r["중점고객_점수"]:.1f} <span style="font-size:10px; color:#94A3B8;">({r["중점고객안전점검율"]:.0f}%)</span></td>'
            f'<td style="text-align:right; color:#475569;">{r["사용계약_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["상담응대_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["상담기여_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["만족도_점수"]:.1f}</td>'
            f'</tr>'
        )
        table_rows.append(row_html)

    tbody_content = "".join(table_rows)
    full_html_table = (
        '<div style="overflow-x:auto; border:1px solid #E2E8F0; border-radius:10px; background:white;">'
        '<table class="studio-table">'
        '<thead><tr>'
        '<th>순위</th><th>센터명</th><th style="text-align:right;">총점</th><th style="text-align:center;">평가상태</th>'
        '<th style="text-align:right;">안전점검 (550)</th><th style="text-align:right;">중점고객 (100)</th>'
        '<th style="text-align:right;">사용계약 (50)</th><th style="text-align:right;">상담응대 (100)</th>'
        '<th style="text-align:right;">상담기여 (100)</th><th style="text-align:right;">만족도 (100)</th>'
        '</tr></thead>'
        f'<tbody>{tbody_content}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(full_html_table, unsafe_allow_html=True)


# =============================================================================
# PAGE 3: 🎯 센터 진단 (Studio CenterDetailPage.tsx 100% 동일)
# =============================================================================
elif menu == "🎯 센터 진단":
    center_names = cur_df['센터명'].tolist()
    def center_format(c):
        r = cur_df[cur_df['센터명'] == c].iloc[0]
        return f"{c} 센터 ({r['총점']:.1f}점 | {target_end_text} 예상 {r['예상반기총점']:.1f}점)"

    sel_center = st.selectbox("진단 센터 선택", center_names, format_func=center_format)
    c_rec = cur_df[cur_df['센터명'] == sel_center].iloc[0]

    # 상단 센터 평가 배지 및 요약 카드
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
    yoy_text = f"{'+' if yoy_val >= 0 else ''}{yoy_val:.1f}점" if pd.notna(yoy_val) else "-"
    yoy_color = "#15803D" if (yoy_val or 0) >= 0 else "#DC2626"

    py_end_val = c_rec['전년반기말_총점']
    py_end_text = f"{py_end_val:.1f}점" if pd.notna(py_end_val) else "-"

    render_html(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:20px 24px; margin-bottom:20px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="background:#0B4EA2; color:white; width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:800;">
                    {c_rec['센터명'][:1]}
                </div>
                <div>
                    <h2 style="margin:0; font-size:20px; font-weight:800; color:#1E293B;">{c_rec['센터명']} 고객센터 종합 정밀 진단</h2>
                    <p style="margin:2px 0 0 0; font-size:12px; color:#64748B;">{cur_year}년 {cur_month}월 ({half_name} {month_in_half}개월차) | 기준 벤치마크 평가</p>
                </div>
            </div>
            <div style="background:{badge_bg}; color:{badge_color}; border:1px solid {badge_border}; border-radius:20px; padding:6px 16px; font-weight:800; font-size:13px;">
                {badge_text}
            </div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; padding-top:14px; border-top:1px solid #F1F5F9;">
            <div style="background:#F8FAFC; padding:12px 14px; border-radius:8px;">
                <div style="font-size:11px; color:#64748B;">현재 누적 총점</div>
                <div style="font-size:20px; font-weight:800; color:#0B4EA2;">{c_rec['총점']:.1f}점</div>
            </div>
            <div style="background:#F8FAFC; padding:12px 14px; border-radius:8px;">
                <div style="font-size:11px; color:#64748B;">{target_end_text} 예상 총점</div>
                <div style="font-size:20px; font-weight:800; color:#10B981;">{c_rec['예상반기총점']:.1f}점</div>
            </div>
            <div style="background:#F8FAFC; padding:12px 14px; border-radius:8px;">
                <div style="font-size:11px; color:#64748B;">전년 동월 대비 (YoY)</div>
                <div style="font-size:20px; font-weight:800; color:{yoy_color};">{yoy_text}</div>
            </div>
            <div style="background:#F8FAFC; padding:12px 14px; border-radius:8px;">
                <div style="font-size:11px; color:#64748B;">전년 {target_end_text} 최종 실적</div>
                <div style="font-size:20px; font-weight:800; color:#64748B;">{py_end_text}</div>
            </div>
        </div>
    </div>
    """)

    col_radar, col_table = st.columns([1, 1])
    with col_radar:
        render_html("""
        <div class="studio-box-title"><span>🎯</span> 6대 핵심 KPI 진척 밸런스 레이더</div>
        <div class="studio-box-desc">각 지표별 만점 대비 당월 달성률 현황 (안전점검 계열은 누적 진척도)</div>
        """)

        categories = ['안전점검 (550)', '중점고객 (100)', '사용계약 (50)', '상담응대 (100)', '상담기여 (100)', '만족도 (100)']
        values = [
            c_rec['안전점검실점검율'],
            c_rec['중점고객안전점검율'],
            c_rec['사용계약율'],
            c_rec['상담응대율'],
            c_rec['상담기여도'],
            c_rec['고객서비스만족도']
        ]
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name=c_rec['센터명'],
            line_color='#0B4EA2',
            fillcolor='rgba(11, 78, 162, 0.3)'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="#64748B")),
                angularaxis=dict(tickfont=dict(size=10, color="#172B4D", weight=700))
            ),
            showlegend=False,
            height=320,
            margin=dict(l=25, r=25, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_table:
        render_html(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="studio-box-title"><span>📊</span> 지표별 세부 채점 및 성격 내역</div>
            <span style="font-size:11px; color:#64748B;">{month_in_half}개월차 기준</span>
        </div>
        <div class="studio-box-desc">지표별 성격(누적형 vs 월별비율형) 및 배점 채점 결과</div>
        """)

        table_html = f"""
        <table class="studio-table" style="margin-top:10px;">
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
                    <td style="color:#0B4EA2; font-size:11px;">오더 누적형</td>
                    <td style="text-align:right; color:#64748B;">550점</td>
                    <td style="text-align:right; font-weight:700;">{c_rec['안전점검실점검율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['안전점검_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">중점고객안전점검율</td>
                    <td style="color:#0B4EA2; font-size:11px;">오더 누적형</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:700;">{c_rec['중점고객안전점검율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['중점고객_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">사용계약율</td>
                    <td style="color:#64748B; font-size:11px;">구간 배점형</td>
                    <td style="text-align:right; color:#64748B;">50점</td>
                    <td style="text-align:right; font-weight:700;">{c_rec['사용계약율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['사용계약_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">상담응대율</td>
                    <td style="color:#64748B; font-size:11px;">월별 비율형</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:700;">{c_rec['상담응대율']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['상담응대_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">상담기여도</td>
                    <td style="color:#64748B; font-size:11px;">월별 비율형</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:700;">{c_rec['상담기여도']:.1f}%</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['상담기여_점수']:.1f}점</td>
                </tr>
                <tr>
                    <td style="font-weight:700;">고객서비스만족도</td>
                    <td style="color:#64748B; font-size:11px;">조사 평가형</td>
                    <td style="text-align:right; color:#64748B;">100점</td>
                    <td style="text-align:right; font-weight:700;">{c_rec['고객서비스만족도']:.1f}점</td>
                    <td style="text-align:right; font-weight:800; color:#0B4EA2;">{c_rec['만족도_점수']:.1f}점</td>
                </tr>
                <tr style="background:#F1F5F9; font-weight:800;">
                    <td>합계 (현재 누적 총점)</td>
                    <td style="color:#0B4EA2; font-size:11px;">{target_end_text} 예상 {c_rec['예상반기총점']:.1f}점</td>
                    <td style="text-align:right; color:#64748B;">1,000점</td>
                    <td style="text-align:right;">-</td>
                    <td style="text-align:right; font-size:14px; color:#0B4EA2;">{c_rec['총점']:.1f}점</td>
                </tr>
            </tbody>
        </table>
        """
        render_html(table_html)

    # What-If 시뮬레이터
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    render_html(f"""
    <div style="border-top:1px solid #E2E8F0; padding-top:18px;">
        <div class="studio-box-title"><span>🔮</span> What-If 시뮬레이터: {c_rec['센터명']} 센터 {target_end_text} 911점 달성 전략 수립</div>
        <div class="studio-box-desc">{target_end_text} 최종 누적 목표치를 슬라이더로 조율하여 911점 달성 여부와 추가 필요 점수를 실시간 시뮬레이션합니다.</div>
    </div>
    """)

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

    sim_sc_safety = (sim_safety / 100.0) * 550.0
    sim_sc_key = (sim_key / 100.0) * 100.0
    sim_sc_contract = calc_contract_score(sim_contract)
    sim_sc_resp = (sim_resp / 100.0) * 100.0
    sim_sc_contrib = (sim_contrib / 100.0) * 100.0
    sim_sc_sat = sim_sat
    sim_total = sim_sc_safety + sim_sc_key + sim_sc_contract + sim_sc_resp + sim_sc_contrib + sim_sc_sat

    is_passing = sim_total >= 911.0
    gap = 911.0 - sim_total
    res_bg = "#DCFCE7" if is_passing else "#FEE2E2"
    res_border = "#86EFAC" if is_passing else "#FCA5A5"
    res_color = "#15803D" if is_passing else "#991B1B"
    res_badge_text = "🎉 911점 달성 (합격)" if is_passing else f"⚠️ {abs(gap):.1f}점 보강 필요"

    render_html(f"""
    <div class="sim-result-bar">
        <div>
            <div style="font-size:11px; color:#64748B;">{target_end_text} 시뮬레이션 최종 총점</div>
            <div style="font-size:24px; font-weight:800; color:#0B4EA2;">{sim_total:.1f}점</div>
        </div>
        <div style="background:{res_bg}; border:1px solid {res_border}; color:{res_color}; border-radius:8px; padding:10px 18px; font-size:14px; font-weight:800;">
            {res_badge_text}
        </div>
    </div>
    """)


# =============================================================================
# PAGE 4: ⚠️ 위험 관리 (Studio RiskPage.tsx 100% 동일)
# =============================================================================
elif menu == "⚠️ 위험 관리":
    high_risk_centers = cur_df[(cur_df['예상반기총점'] < 911.0) | (cur_df['전년동월대비_증감'] < -20.0)]
    warning_centers = cur_df[
        (~cur_df['센터명'].isin(high_risk_centers['센터명'])) &
        ((cur_df['예상반기총점'] < 930.0) | (cur_df['오더진척상태'] == '지연') | (cur_df['전년동월대비_증감'] < -5.0))
    ]
    safe_centers = cur_df[
        (~cur_df['센터명'].isin(high_risk_centers['센터명'])) &
        (~cur_df['센터명'].isin(warning_centers['센터명']))
    ]

    render_html(f"""
    <div class="banner-notice" style="border-left: 4px solid #0B4EA2;">
        <div class="banner-notice-text">
            <strong>⚠️ {target_end_text} 911점 도달 궤도 및 누적 오더 진척 위험 진단</strong><br/>
            현재 <strong>{month_in_half}개월차 기준 평균 실점검율</strong>은 계획 대비 양호한 수준을 유지하고 있습니다.<br/>
            고객센터 종합 평가는 단순 현재 점수가 아닌 <strong>'전년 동월 대비 진척도'</strong> 및 <strong>'전년 반기말 실적 대비 {target_end_text} 911점 도달 가능성'</strong>을 기준으로 선제적 코칭 및 지원 대상 센터를 정밀 진단합니다.
        </div>
        <div style="display:flex; gap:8px;">
            <span style="background:#FEF3C7; color:#92400E; padding:6px 12px; border-radius:20px; font-weight:700; font-size:11px;">집중 코칭: {len(high_risk_centers) + len(warning_centers)}개소</span>
            <span style="background:#DCFCE7; color:#166534; padding:6px 12px; border-radius:20px; font-weight:700; font-size:11px;">정상 궤도: {len(safe_centers)}개소</span>
        </div>
    </div>
    """)

    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        render_html(f"""
        <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:14px; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#991B1B; font-size:13px;">🚨 {target_end_text} 911점 미달 위험 ({len(high_risk_centers)}개소)</strong>
                <span style="font-size:10px; background:#FFFFFF; color:#991B1B; padding:2px 8px; border-radius:10px; font-weight:700; border:1px solid #FECACA;">긴급 오더 보강</span>
            </div>
            <div style="font-size:11px; color:#B91C1C; margin-top:4px;">전년 대비 오더 지연으로 잔여 기간 특단의 안전점검 보강 필요</div>
        </div>
        """)
        for _, r in high_risk_centers.iterrows():
            yoy_txt = f"{'+' if r['전년동월대비_증감'] >= 0 else ''}{r['전년동월대비_증감']:.1f}점" if pd.notna(r['전년동월대비_증감']) else "-"
            prev_half_txt = f"{r['전년반기말_총점']:.1f}점" if pd.notna(r['전년반기말_총점']) else "-"
            gap_needed = max(0.0, 911.0 - r['예상반기총점'])
            render_html(f"""
            <div class="risk-center-card" style="border-left: 4px solid #EF4444; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="font-size:14px; color:#1E293B;">{r['센터명']} 센터</strong>
                    <span style="color:#DC2626; font-weight:800; font-size:13px;">{target_end_text} 예상 {r['예상반기총점']:.1f}점</span>
                </div>
                <div style="font-size:11px; color:#64748B; line-height:1.6; border-top:1px solid #F1F5F9; border-bottom:1px solid #F1F5F9; padding:6px 0; margin-bottom:8px;">
                    • 현재 총점: <strong style="color:#1E293B;">{r['총점']:.1f}점</strong><br/>
                    • 안전점검 달성: <strong style="color:#1E293B;">{r['안전점검실점검율']:.1f}%</strong> (권장선 {benchmark_safety:.1f}%)<br/>
                    • 전년 동월 대비: <strong style="color:#DC2626;">{yoy_txt}</strong> | 전년 {target_end_text}: {prev_half_txt}
                </div>
                <div style="font-size:11.5px; color:#991B1B; font-weight:600; line-height:1.45; background:#FEF2F2; padding:6px 10px; border-radius:6px;">
                    👉 <strong>처방 의견:</strong> 911점 달성까지 예상 {gap_needed:.1f}점 부족. 매월 안전점검 오더 건수 +100건 이상 집중 처리 긴급 코칭 필요.
                </div>
            </div>
            """)
        if high_risk_centers.empty:
            st.info("해당 위험 센터가 없습니다. 전 센터 정상 진척 중입니다.")

    with r_col2:
        render_html(f"""
        <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:14px; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#92400E; font-size:13px;">⚠️ 주의 / 집중 코칭 대상 ({len(warning_centers)}개소)</strong>
                <span style="font-size:10px; background:#FFFFFF; color:#92400E; padding:2px 8px; border-radius:10px; font-weight:700; border:1px solid #FDE68A;">오더 페이스 관리</span>
            </div>
            <div style="font-size:11px; color:#D97706; margin-top:4px;">911점 경계선 또는 전년비 소폭 지연으로 오더 누적 속도 유지 필요</div>
        </div>
        """)
        for _, r in warning_centers.iterrows():
            yoy_txt = f"{'+' if r['전년동월대비_증감'] >= 0 else ''}{r['전년동월대비_증감']:.1f}점" if pd.notna(r['전년동월대비_증감']) else "-"
            prev_half_txt = f"{r['전년반기말_총점']:.1f}점" if pd.notna(r['전년반기말_총점']) else "-"
            render_html(f"""
            <div class="risk-center-card" style="border-left: 4px solid #F59E0B; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="font-size:14px; color:#1E293B;">{r['센터명']} 센터</strong>
                    <span style="color:#D97706; font-weight:800; font-size:13px;">{target_end_text} 예상 {r['예상반기총점']:.1f}점</span>
                </div>
                <div style="font-size:11px; color:#64748B; line-height:1.6; border-top:1px solid #F1F5F9; border-bottom:1px solid #F1F5F9; padding:6px 0; margin-bottom:8px;">
                    • 현재 총점: <strong style="color:#1E293B;">{r['총점']:.1f}점</strong><br/>
                    • 안전점검 달성: <strong style="color:#1E293B;">{r['안전점검실점검율']:.1f}%</strong><br/>
                    • 전년 동월 대비: <strong style="color:#D97706;">{yoy_txt}</strong> | 전년 {target_end_text}: {prev_half_txt}
                </div>
                <div style="font-size:11.5px; color:#92400E; font-weight:600; line-height:1.45; background:#FFFBEB; padding:6px 10px; border-radius:6px;">
                    👉 <strong>처방 의견:</strong> 월별 오더 처리 누적 페이스를 상시 모니터링하여 {target_end_text} 911점 합격선 안정적 수성 유도.
                </div>
            </div>
            """)
        if warning_centers.empty:
            st.info("해당 주의 센터가 없습니다.")

    with r_col3:
        render_html(f"""
        <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:14px; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#166534; font-size:13px;">✅ 안정 / 911점 달성 유력 ({len(safe_centers)}개소)</strong>
                <span style="font-size:10px; background:#FFFFFF; color:#166534; padding:2px 8px; border-radius:10px; font-weight:700; border:1px solid #BBF7D0;">우수 누적 궤도</span>
            </div>
            <div style="font-size:11px; color:#15803D; margin-top:4px;">전년 동월 상회 및 견고한 오더 누적 속도로 911점 초과 달성 유력</div>
        </div>
        """)
        for _, r in safe_centers.iterrows():
            yoy_txt = f"YoY {'+' if r['전년동월대비_증감'] >= 0 else ''}{r['전년동월대비_증감']:.1f}점" if pd.notna(r['전년동월대비_증감']) else "순항"
            render_html(f"""
            <div class="risk-center-card" style="border-left: 4px solid #10B981; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <strong style="font-size:14px; color:#1E293B;">{r['센터명']} 센터</strong>
                    <span style="color:#15803D; font-weight:800; font-size:13px;">{target_end_text} 예상 {r['예상반기총점']:.1f}점</span>
                </div>
                <div style="display:flex; justify-content:space-between; text-size:11px; color:#64748B;">
                    <span>현재: {r['총점']:.1f}점 (안전: {r['안전점검실점검율']:.0f}%)</span>
                    <span style="color:#15803D; font-weight:700;">{yoy_txt}</span>
                </div>
            </div>
            """)


# =============================================================================
# PAGE 5: 🌡️ KPI 히트맵 (Studio HeatmapPage.tsx 100% 동일)
# =============================================================================
elif menu == "🌡️ KPI 히트맵":
    render_html("""
    <div class="studio-box-header">
        <div>
            <div class="studio-box-title">🌡️ 전체 센터 6대 KPI 달성률 매트릭스 히트맵</div>
            <div class="studio-box-desc">S: 95% 이상 (짙은 녹색) | A: 90~94% (연한 녹색) | B: 85~89% (황색) | C: 75~84% (주황) | D: 75% 미만 (적색)</div>
        </div>
    </div>
    """)

    heat_kpis = ['안전점검실점검율', '중점고객안전점검율', '사용계약율', '상담응대율', '상담기여도', '고객서비스만족도']
    heat_labels = ['안전점검(550)', '중점고객(100)', '사용계약(50)', '상담응대(100)', '상담기여(100)', '만족도(100)']
    
    sorted_heat_df = cur_df.sort_values(by="총점", ascending=False).set_index('센터명')
    matrix_vals = sorted_heat_df[heat_kpis].values

    fig_heat = px.imshow(
        matrix_vals,
        labels=dict(x="평가 지표", y="고객센터", color="달성률(%)"),
        x=heat_labels,
        y=sorted_heat_df.index,
        color_continuous_scale=[
            [0.0, "#D92D20"],
            [0.75, "#E66A1F"],
            [0.85, "#F59E0B"],
            [0.90, "#84CC16"],
            [1.0, "#178A5B"]
        ],
        zmin=60,
        zmax=100,
        text_auto=".1f",
        aspect="auto"
    )
    fig_heat.update_layout(
        height=620,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis_tickfont=dict(size=11, color="#1E293B", weight=700),
        yaxis_tickfont=dict(size=11, color="#1E293B")
    )
    st.plotly_chart(fig_heat, use_container_width=True)


# =============================================================================
# PAGE 6: 🔬 심화 분석 (Studio DeepAnalysisPage.tsx 100% 동일)
# =============================================================================
elif menu == "🔬 심화 분석":
    render_html("""
    <div class="studio-box-header">
        <div>
            <div class="studio-box-title">🔬 지표 간 상관관계 및 분포 심층 분석</div>
            <div class="studio-box-desc">안전점검 실점검율 vs 총점 상관성 분석 및 주요 지표 간 피어슨 상관계수</div>
        </div>
    </div>
    """)

    c_s1, c_s2 = st.columns([3, 2])
    with c_s1:
        st.markdown("#### 🎯 안전점검 실점검율 vs 총점 상관분포")
        fig_scatter = px.scatter(
            cur_df,
            x="안전점검실점검율",
            y="총점",
            size="예상반기총점",
            color="도달판정",
            hover_name="센터명",
            color_discrete_map={"정상궤도": "#10B981", "주의": "#F59E0B", "위험": "#EF4444"},
            labels={"안전점검실점검율": "안전점검 실점검율(%)", "총점": "당월 총점(점)"}
        )
        fig_scatter.add_hline(y=911, line_dash="dash", line_color="#EF4444", annotation_text="911점선")
        fig_scatter.add_vline(x=benchmark_safety, line_dash="dash", line_color="#0B4EA2", annotation_text=f"기준진척 ({benchmark_safety:.1f}%)")
        fig_scatter.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=30, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='#F1F5F9'),
            xaxis=dict(gridcolor='#F1F5F9')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c_s2:
        st.markdown("#### 🔗 6대 지표 상관계수 행렬")
        score_cols = ['안전점검_점수', '중점고객_점수', '사용계약_점수', '상담응대_점수', '상담기여_점수', '만족도_점수', '총점']
        labels_short = ['안전', '중점', '계약', '응대', '기여', '만족', '총점']
        corr_matrix = cur_df[score_cols].corr().values

        fig_corr = px.imshow(
            corr_matrix,
            x=labels_short,
            y=labels_short,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            text_auto=".2f"
        )
        fig_corr.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=30, b=40)
        )
        st.plotly_chart(fig_corr, use_container_width=True)


# =============================================================================
# PAGE 7: 📑 반기 보고 (Studio HalfReportPage.tsx 100% 동일)
# =============================================================================
elif menu in ["📑 상반기 보고", "📑 반기 보고"]:
    # 2026년 상반기 마감(2026년 6월) 실적 데이터 자동 필터링 (Studio HalfReportPage.tsx 100% 동일)
    h1_df = df_all[df_all['평가연월'] == '2026-06'].copy()
    if h1_df.empty:
        h1_df = df_all[(df_all['연도'] == 2026) & (df_all['월'] <= 6)].sort_values('월').groupby('센터명').last().reset_index()

    h1_total_centers = len(h1_df)
    h1_avg_score = h1_df['총점'].mean() if not h1_df.empty else 0.0
    h1_pass_count = len(h1_df[h1_df['총점'] >= 911.0])
    h1_pass_rate = (h1_pass_count / h1_total_centers * 100) if h1_total_centers > 0 else 0.0

    # 2025년 상반기(2025년 6월) 실적 비교
    last_year_h1 = df_all[df_all['평가연월'] == '2025-06'].copy()
    last_year_avg = last_year_h1['총점'].mean() if not last_year_h1.empty else None
    h1_yoy_diff = (h1_avg_score - last_year_avg) if last_year_avg is not None else None

    # 상단 배너 헤더
    render_html("""
    <div class="yesco-header-banner" style="background: linear-gradient(135deg, #0B4EA2 0%, #073874 100%);">
        <div class="header-title-box">
            <h1>📑 2026년 상반기 고객센터 종합 평가 결과 리포트</h1>
            <p>2026년 상반기(1~6월) 마감 실적 및 전년(2025년) 상반기 대비 증감 총괄 분석표 (공식 보고용)</p>
        </div>
        <div class="header-badge-box">
            <span class="badge-pill-header" style="background:#FFFFFF; color:#0B4EA2;">2026년 6월말 마감 확정</span>
            <span class="badge-pill-header">기준 목표: 911.0점</span>
        </div>
    </div>
    """)

    # 3대 핵심 지표 카드 (Studio HalfReportPage.tsx 1:1)
    rep_c1, rep_c2, rep_c3 = st.columns(3)
    with rep_c1:
        yoy_text = f"전년 대비 {'+' if (h1_yoy_diff or 0) >= 0 else ''}{(h1_yoy_diff or 0):.1f}점" if h1_yoy_diff is not None else "기준 목표 911점"
        yoy_col = "#15803D" if (h1_yoy_diff or 0) >= 0 else "#DC2626"
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #0B4EA2;">
            <div class="metric-title"><span>상반기 평균 총점</span> <span>📊</span></div>
            <div class="metric-value">{h1_avg_score:.1f}점</div>
            <div class="metric-sub" style="color: {yoy_col}; font-weight:700;">{yoy_text}</div>
        </div>
        """)
    with rep_c2:
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #10B981;">
            <div class="metric-title"><span>911점 달성률</span> <span>🎯</span></div>
            <div class="metric-value" style="color: #15803D;">{h1_pass_rate:.1f}%</div>
            <div class="metric-sub" style="color: #15803D;">{h1_pass_count}개 센터 달성 / 총 {h1_total_centers}개소</div>
        </div>
        """)
    with rep_c3:
        fail_count = h1_total_centers - h1_pass_count
        render_html(f"""
        <div class="metric-grid-card" style="border-left-color: #F59E0B;">
            <div class="metric-title"><span>미달 센터 현황</span> <span>⚠️</span></div>
            <div class="metric-value" style="color: #D97706;">{fail_count}개소</div>
            <div class="metric-sub">하반기 재계약 보강 관리 대상</div>
        </div>
        """)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 권역 조정 및 센터 통합 안내 알림창 (Studio 1:1)
    render_html("""
    <div style="background:#FFFDF5; border:1px solid #FDE68A; border-radius:10px; padding:12px 16px; margin-bottom:18px; font-size:12px; color:#92400E; line-height:1.6;">
        <strong style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
            <span>ℹ️</span> 권역 조정 및 센터 통합 안내
        </strong>
        <div>• <strong>퇴계원/별내</strong>: 2026년 통합 운영 센터로 단일 실적으로 평가되었습니다.</div>
        <div>• <strong>구리</strong>: 2026년 4월 권역조정으로 행정동을 흡수하였으나, 안전점검은 기존 관리세대 기준으로 공정하게 평가되었습니다.</div>
    </div>
    """)

    # 센터별 2026년 상반기 평가 종합 순위 테이블 (Studio 1:1)
    st.markdown("#### 🏢 센터별 2026년 상반기 평가 종합 순위 (마감 실적)")

    sorted_h1 = h1_df.sort_values(by="총점", ascending=False).copy()
    h1_table_rows = []
    
    last_year_map = {r['센터명']: r['총점'] for _, r in last_year_h1.iterrows()} if not last_year_h1.empty else {}

    for rank, (_, r) in enumerate(sorted_h1.iterrows(), start=1):
        g, cls, desc = get_score_badge(r['총점'])
        target_gap = r['총점'] - 911.0
        gap_col = "#15803D" if target_gap >= 0 else "#991B1B"
        gap_txt = f"{'+' if target_gap >= 0 else ''}{target_gap:.1f}"

        ly_score = last_year_map.get(r['센터명'])
        if ly_score is not None:
            diff_val = r['총점'] - ly_score
            diff_col = "#15803D" if diff_val >= 0 else "#991B1B"
            diff_txt = f"{'+' if diff_val >= 0 else ''}{diff_val:.1f}"
        else:
            diff_col = "#94A3B8"
            diff_txt = "-"

        row_html = (
            f'<tr>'
            f'<td style="font-weight:700; color:#64748B;">{rank}</td>'
            f'<td style="font-weight:800; color:#1E293B;">{r["센터명"]}</td>'
            f'<td style="text-align:right; font-weight:800; color:#0B4EA2;">{r["총점"]:.1f}</td>'
            f'<td style="text-align:right; font-weight:700; color:{gap_col};">{gap_txt}</td>'
            f'<td style="text-align:right; font-weight:600; color:{diff_col};">{diff_txt}</td>'
            f'<td style="text-align:right; color:#475569;">{r["안전점검_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["중점고객_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["사용계약_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["상담응대_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["상담기여_점수"]:.1f}</td>'
            f'<td style="text-align:right; color:#475569;">{r["만족도_점수"]:.1f}</td>'
            f'</tr>'
        )
        h1_table_rows.append(row_html)

    h1_tbody = "".join(h1_table_rows)
    h1_html_table = (
        '<div style="overflow-x:auto; border:1px solid #E2E8F0; border-radius:10px; background:white; margin-bottom:16px;">'
        '<table class="studio-table">'
        '<thead><tr>'
        '<th>순위</th><th>센터명</th><th style="text-align:right;">상반기 총점</th><th style="text-align:right;">목표(911) 대비</th><th style="text-align:right;">전년 대비</th>'
        '<th style="text-align:right;">안전점검(550)</th><th style="text-align:right;">중점고객(100)</th>'
        '<th style="text-align:right;">사용계약(50)</th><th style="text-align:right;">상담응대(100)</th>'
        '<th style="text-align:right;">상담기여(100)</th><th style="text-align:right;">만족도(100)</th>'
        '</tr></thead>'
        f'<tbody>{h1_tbody}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(h1_html_table, unsafe_allow_html=True)

    # 엑셀 다운로드 버튼
    export_df = sorted_h1[['센터명', '총점', '안전점검_점수', '중점고객_점수', '사용계약_점수', '상담응대_점수', '상담기여_점수', '만족도_점수']].copy()
    export_df.insert(0, '순위', range(1, len(export_df) + 1))
    
    csv_bytes = export_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 2026년 상반기 종합 보고서 다운로드 (CSV)",
        data=csv_bytes,
        file_name="yesco_2026_h1_report.csv",
        mime="text/csv",
        use_container_width=True
    )


# =============================================================================
# PAGE 7: 📑 상반기 보고 (2026년 상반기 6월 마감 실적 종합 리포트)
# =============================================================================
elif menu == "📑 상반기 보고":
    # 2026년 상반기 마감인 6월 데이터 및 전년(2025년) 6월 벤치마크 추출
    h1_df = df_all[(df_all['연도'] == 2026) & (df_all['월'] == 6)].copy()
    if h1_df.empty:
        # 혹시 2026년 6월이 없으면 상반기 중 가장 늦은 월 사용
        h1_df = df_all[(df_all['연도'] == 2026) & (df_all['월'] <= 6)].copy()
        if not h1_df.empty:
            max_m = h1_df['월'].max()
            h1_df = h1_df[h1_df['월'] == max_m].copy()
        else:
            h1_df = cur_df.copy()

    py_h1_df = df_all[(df_all['연도'] == 2025) & (df_all['월'] == 6)].copy()
    py_h1_map = dict(zip(py_h1_df['센터명'], py_h1_df['총점'])) if not py_h1_df.empty else {}

    total_h1_centers = len(h1_df)
    avg_h1_score = h1_df['총점'].mean() if total_h1_centers > 0 else 0.0
    pass_h1_count = len(h1_df[h1_df['총점'] >= 911])
    pass_h1_rate = (pass_h1_count / total_h1_centers * 100) if total_h1_centers > 0 else 0.0
    under_h1_count = total_h1_centers - pass_h1_count

    py_avg_h1 = py_h1_df['총점'].mean() if not py_h1_df.empty else 0.0
    yoy_h1_diff = (avg_h1_score - py_avg_h1) if py_avg_h1 > 0 else 0.0

    # 배너
    render_html(f"""
    <div style="background:linear-gradient(135deg, #0B4EA2 0%, #073874 100%); color:white; padding:22px 28px; border-radius:14px; margin-bottom:22px; box-shadow:0 4px 16px rgba(11,78,162,0.18); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
        <div>
            <h1 style="margin:0; font-size:22px; font-weight:800; letter-spacing:-0.5px; color:#FFFFFF !important;">📑 2026년 상반기 종합 평가 결과 리포트</h1>
            <p style="margin:6px 0 0 0; font-size:13px; opacity:0.9; color:#E2E8F0 !important;">2026년 상반기(1~6월) 최종 마감 실적 및 전년(2025년) 상반기 대비 증감 종합 분석</p>
        </div>
        <div style="display:flex; gap:8px;">
            <span style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35); color:#FFFFFF; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">2026년 06월 마감 확정</span>
            <span style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35); color:#FFFFFF; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">총 23개 센터 평가 완료</span>
        </div>
    </div>
    """)

    # 3대 핵심 KPI 카드
    diff_color = "#166534" if yoy_h1_diff >= 0 else "#991B1B"
    diff_symbol = "+" if yoy_h1_diff >= 0 else ""
    render_html(f"""
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px; margin-bottom:22px;">
        <div class="metric-grid-card" style="border-left:4px solid #0B4EA2;">
            <div class="metric-title"><span>상반기 평균 총점</span> <span>📊</span></div>
            <div class="metric-value" style="color:#0B4EA2;">{avg_h1_score:.1f}점</div>
            <div class="metric-sub" style="color:{diff_color}; font-weight:700;">전년 대비 {diff_symbol}{yoy_h1_diff:.1f}점 (기준 목표 911.0점)</div>
        </div>
        <div class="metric-grid-card" style="border-left:4px solid #10B981;">
            <div class="metric-title"><span>911점 달성률</span> <span>🎯</span></div>
            <div class="metric-value" style="color:#10B981;">{pass_h1_rate:.1f}%</div>
            <div class="metric-sub" style="color:#10B981; font-weight:700;">{pass_h1_count}개 센터 달성 / 총 {total_h1_centers}개소</div>
        </div>
        <div class="metric-grid-card" style="border-left:4px solid #EF4444;">
            <div class="metric-title"><span>미달 센터 현황</span> <span>⚠️</span></div>
            <div class="metric-value" style="color:#EF4444;">{under_h1_count}개소</div>
            <div class="metric-sub" style="color:#64748B;">하반기 재계약 종합 관리 대상</div>
        </div>
    </div>
    """)

    # 권역 조정 및 센터 통합 안내
    render_html("""
    <div style="background:#FFFDF5; border:1px solid #FDE68A; border-radius:12px; padding:16px 20px; margin-bottom:22px; color:#92400E; font-size:12px; line-height:1.6;">
        <div style="font-weight:800; font-size:13px; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
            <span>ℹ️</span> 권역 조정 및 센터 통합 안내사항
        </div>
        <div>• <strong>퇴계원/별내</strong>: 2026년 통합 운영 센터로 단일 실적으로 집계 평가되었습니다.</div>
        <div>• <strong>구리</strong>: 2026년 4월 권역조정으로 행정동을 흡수하였으나, 안전점검은 기존 관리세대 기준으로 공정하게 산정되었습니다.</div>
    </div>
    """)

    # 센터별 종합 평가 순위 테이블
    h1_sorted = h1_df.sort_values(by='총점', ascending=False).reset_index(drop=True)
    h1_rows_html = ""
    for idx, row in h1_sorted.iterrows():
        rank = idx + 1
        cname = row['센터명']
        total_s = float(row['총점'])
        target_gap = total_s - 911.0
        gap_style = "color:#166534; font-weight:700;" if target_gap >= 0 else "color:#991B1B; font-weight:700;"
        gap_text = f"+{target_gap:.1f}" if target_gap >= 0 else f"{target_gap:.1f}"
        
        py_s = py_h1_map.get(cname)
        if py_s is not None:
            py_diff = total_s - py_s
            py_text = f"+{py_diff:.1f}" if py_diff >= 0 else f"{py_diff:.1f}"
            py_style = "color:#166534; font-weight:700;" if py_diff >= 0 else "color:#991B1B; font-weight:700;"
        else:
            py_text = "-"
            py_style = "color:#94A3B8;"

        h1_rows_html += f"""
        <tr>
            <td style="font-weight:700; color:#64748B;">{rank}</td>
            <td style="font-weight:800; color:#1E293B;">{cname}</td>
            <td style="text-align:right; font-weight:800; color:#0B4EA2;">{total_s:.1f}</td>
            <td style="text-align:right; {gap_style}">{gap_text}</td>
            <td style="text-align:right; {py_style}">{py_text}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('안전점검_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('중점고객_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('사용계약_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('상담응대_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('상담기여_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('만족도_점수', 0)):.1f}</td>
        </tr>
        """

    h1_table_html = f"""
    <div class="studio-box">
        <div class="studio-box-header">
            <div>
                <div class="studio-box-title">🏢 센터별 2026년 상반기 평가 종합 순위</div>
                <div class="studio-box-desc">2026년 6월 마감 기준 총점 및 6대 핵심 평가지표 배점 내역</div>
            </div>
        </div>
        <div style="overflow-x:auto;">
            <table class="studio-table">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>센터명</th>
                        <th style="text-align:right;">상반기 총점</th>
                        <th style="text-align:right;">목표(911) 대비</th>
                        <th style="text-align:right;">전년 대비</th>
                        <th style="text-align:right;">안전점검(550)</th>
                        <th style="text-align:right;">중점고객(100)</th>
                        <th style="text-align:right;">사용계약(50)</th>
                        <th style="text-align:right;">상담응대(100)</th>
                        <th style="text-align:right;">상담기여(100)</th>
                        <th style="text-align:right;">만족도(100)</th>
                    </tr>
                </thead>
                <tbody>
                    {h1_rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """
    render_html(h1_table_html)
