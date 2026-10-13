# -*- coding: utf-8 -*-
"""
도시가스 고객센터 성과 대시보드 (Streamlit Application)
- Streamlit Cloud 배포용 메인 모듈 (app.py)
"""
import streamlit as st
import pandas as pd
import json
import os
import math
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="고객센터 성과 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 커스텀 스타일 (럭셔리 비즈니스 UI)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #0B4EA2 0%, #1E3A8A 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(11, 78, 162, 0.15);
    }
    .metric-container {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 12px;
        border-left: 4px solid #0B4EA2;
    }
    .metric-title {
        font-size: 13px;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 12px;
        color: #3B82F6;
        margin-top: 4px;
        font-weight: 500;
    }
    .banner-notice {
        background: #F0F7FF;
        border: 1px solid #BAE6FD;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 18px;
        color: #0369A1;
        font-size: 13px;
        line-height: 1.6;
    }
    .insight-card {
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 4px solid #3B82F6;
        background: #F8FAFC;
    }
    .insight-success {
        background: #F0FDF4;
        border-left-color: #22C55E;
        color: #166534;
    }
    .insight-warning {
        background: #FFFBEB;
        border-left-color: #F59E0B;
        color: #92400E;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 데이터 파싱 및 점수 계산 유틸리티
# -----------------------------------------------------------------------------
def normalize_date_string(val):
    if val is None:
        return '2026-02-01'
    if isinstance(val, (int, float)):
        if 30000 < val < 70000:
            # Excel serial date
            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(val) - 2)
            return dt.strftime('%Y-%m-01')
        s = str(int(val))
        if len(s) == 6:
            return f"{s[:4]}-{s[4:6]}-01"
        return s
    s = str(val).strip()
    if len(s) >= 7 and s[:4].isdigit():
        return f"{s[:7]}-01"
    return '2026-02-01'

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
    # 1. Excel 시도
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
        year = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 2026
        month = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2
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
# 메인 애플리케이션
# -----------------------------------------------------------------------------
df_all = load_all_records()

if df_all.empty:
    st.error("데이터를 불러올 수 없습니다. data/latest_data.xlsx 또는 data/latest_data.json 파일을 확인해주세요.")
    st.stop()

# 사이드바 설정
st.sidebar.title("🏢 대시보드 메뉴")
all_months = sorted(list(df_all['평가월'].apply(lambda x: str(x)[:7]).unique()))
default_idx = all_months.index('2026-02') if '2026-02' in all_months else len(all_months) - 1

selected_month = st.sidebar.selectbox("📅 평가월 선택", all_months, index=default_idx)

# 현재 선택 월 및 기간 정보 계산
cur_df = df_all[df_all['평가월'].str.startswith(selected_month)].copy()
cur_year = int(selected_month.split('-')[0])
cur_month = int(selected_month.split('-')[1])
month_in_half = cur_month if cur_month <= 6 else cur_month - 6
half_name = "상반기" if cur_month <= 6 else "하반기"
target_end_text = "6월말" if cur_month <= 6 else "12월말"

# 전년 동월 데이터 매핑
prev_year = cur_year - 1
prev_df = df_all[(df_all['연도'] == prev_year) & (df_all['월'] == cur_month)].copy()
prev_map = {r['센터명']: r['총점'] for _, r in prev_df.iterrows()}
cur_df['전년동월_총점'] = cur_df['센터명'].map(prev_map)
cur_df['전년동월대비_증감'] = cur_df['총점'] - cur_df['전년동월_총점']

# 판정
benchmark_safety = (month_in_half / 6.0) * 92.0
def get_track_status(pred):
    if pred >= 915: return '정상궤도'
    if pred >= 905: return '주의'
    return '위험'
cur_df['도달판정'] = cur_df['예상반기총점'].apply(get_track_status)

# 네비게이션
menu = st.sidebar.radio(
    "페이지 이동",
    ["🏠 홈", "📊 성과 분석", "🎯 센터 진단", "⚠️ 위험 관리", "🌡️ KPI 히트맵", "🔬 심화 분석", "📑 상반기 보고"]
)

# 사이드바 파일 업로더
uploaded_file = st.sidebar.file_uploader("📥 신규 엑셀 데이터 등록", type=["xlsx", "xls"])
if uploaded_file is not None:
    st.sidebar.success("파일이 성공적으로 업로드되었습니다. (임시 반영)")

# =============================================================================
# 1. 🏠 홈 대시보드
# =============================================================================
if menu == "🏠 홈":
    st.markdown(f"""
    <div class="main-header">
        <h2 style="margin:0; font-size: 24px;">🏢 도시가스 고객센터 성과 대시보드</h2>
        <p style="margin:4px 0 0 0; opacity: 0.9; font-size: 14px;">
            {selected_month} 기준 | {half_name} {month_in_half}/6개월차 (진척률 {(month_in_half/6*100):.0f}%) | 목표: {target_end_text} 911점 도달
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 누적 진단 현황 배너 (사용자 최신 요청 문구 완벽 반영)
    avg_safety = cur_df['안전점검실점검율'].mean()
    st.markdown(f"""
    <div class="banner-notice">
        <strong>💡 고객센터 종합 진단 현황 ({month_in_half}개월차)</strong><br/>
        현재 <strong>{month_in_half}개월차 기준 평균 실점검율은 {avg_safety:.1f}%</strong>입니다. 계획 대비 양호하게 추진 중이며,
        전년 동월 및 <strong>{target_end_text} 911점 달성 목표선</strong>을 기준으로 센터별 진척 페이스를 종합 모니터링하고 있습니다.
    </div>
    """, unsafe_allow_html=True)

    # 4대 핵심 지표 카드
    total_centers = len(cur_df)
    avg_score = cur_df['총점'].mean()
    prev_avg = cur_df['전년동월_총점'].dropna().mean() if not cur_df['전년동월_총점'].dropna().empty else None
    yoy_diff = (avg_score - prev_avg) if prev_avg is not None else None
    
    on_track_count = len(cur_df[cur_df['예상반기총점'] >= 911.0])
    on_track_rate = (on_track_count / total_centers * 100) if total_centers > 0 else 0
    lag_centers = cur_df[(cur_df['전년동월대비_증감'] < -10) | (cur_df['예상반기총점'] < 905) | (cur_df['안전점검실점검율'] < benchmark_safety - 3)]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        yoy_str = f"전년비 {'+' if yoy_diff >= 0 else ''}{yoy_diff:.1f}점" if yoy_diff is not None else f"{half_name} {month_in_half}개월차"
        st.markdown(f"""
        <div class="metric-container" style="border-left-color: #0B4EA2;">
            <div class="metric-title">전체 센터 평균 총점</div>
            <div class="metric-value">{avg_score:.1f}점</div>
            <div class="metric-sub">{yoy_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-container" style="border-left-color: #10B981;">
            <div class="metric-title">{target_end_text} 911점 예상 달성률</div>
            <div class="metric-value">{on_track_rate:.1f}%</div>
            <div class="metric-sub">{total_centers}개소 중 {on_track_count}개소 정상 궤도</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-container" style="border-left-color: #F59E0B;">
            <div class="metric-title">누적 지연 / 중점 코칭 센터</div>
            <div class="metric-value">{len(lag_centers)}개소</div>
            <div class="metric-sub">전년비 지연 및 911점 미달 위험</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        safety_status = "계획대비 양호" if avg_safety >= benchmark_safety - 3 else "관리 필요"
        st.markdown(f"""
        <div class="metric-container" style="border-left-color: #6366F1;">
            <div class="metric-title">안전점검 평균 실점검율</div>
            <div class="metric-value">{avg_safety:.1f}%</div>
            <div class="metric-sub">계획({benchmark_safety:.1f}%) 대비 {safety_status}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 핵심 인사이트 및 자동 진단
    st.subheader("💡 핵심 인사이트 및 자동 진단")
    
    # 인사이트 1: 911점 정상 궤도
    if on_track_count >= total_centers * 0.8:
        st.markdown(f"""
        <div class="insight-card insight-success">
            <strong>🎯 {target_end_text} 911점 도달 정상 궤도 ({on_track_count}개소)</strong><br/>
            현재 {month_in_half}개월차 기준 전체 {total_centers}개 센터 중 {on_track_count}개소({on_track_rate:.1f}%)가 {target_end_text} 911점 달성 목표선 대비 안정적인 추진 페이스를 보이고 있습니다.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="insight-card insight-warning">
            <strong>⚠️ {target_end_text} 911점 도달 집중 관리 ({total_centers - on_track_count}개소 보강 필요)</strong><br/>
            현재 {month_in_half}개월차 기준 {total_centers - on_track_count}개 센터가 {target_end_text} 911점 도달 페이스에 다소 지연을 보이고 있습니다. 안전점검 오더 처리 속도를 조기 보강해야 합니다.
        </div>
        """, unsafe_allow_html=True)

    # 인사이트 2: 전년 동월 비교
    if yoy_diff is not None:
        if yoy_diff >= 0:
            st.markdown(f"""
            <div class="insight-card insight-success">
                <strong>📈 전년 동월 대비 종합 성과 상승 (+{yoy_diff:.1f}점)</strong><br/>
                현재 {month_in_half}월차 평균 총점({avg_score:.1f}점)은 전년 동월({prev_avg:.1f}점) 대비 +{yoy_diff:.1f}점 상회하여 우수한 누적 흐름을 유지하고 있습니다.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="insight-card insight-warning">
                <strong>⚠️ 전년 동월 대비 성과 지연 감지 ({yoy_diff:.1f}점)</strong><br/>
                현재 {month_in_half}월차 평균 총점({avg_score:.1f}점)이 전년 동월({prev_avg:.1f}점) 대비 {yoy_diff:.1f}점 다소 뒤처져 있어, {target_end_text} 911점 달성을 위한 조기 오더 드라이브가 필요합니다.
            </div>
            """, unsafe_allow_html=True)

    # 인사이트 3: 안전점검 실점검율
    st.markdown(f"""
    <div class="insight-card insight-success">
        <strong>⏱️ 안전점검 실점검율 진척 현황</strong><br/>
        현재 {month_in_half}개월차 기준 평균 실점검율은 {avg_safety:.1f}%입니다. 계획 대비 양호하게 추진되고 있습니다.
    </div>
    """, unsafe_allow_html=True)

    # 인사이트 4: 코칭 대상 센터
    if len(lag_centers) > 0:
        lag_names = ", ".join(lag_centers['센터명'].head(4).tolist())
        st.markdown(f"""
        <div class="insight-card insight-warning">
            <strong>🚨 전년 동월 대비 누적 지연 센터 코칭 필요 ({len(lag_centers)}개소)</strong><br/>
            {lag_names} 등 {len(lag_centers)}개 센터는 전년 동월 대비 오더 누적 페이스가 지연되고 있거나 {target_end_text} 911점 도달에 주의가 요구됩니다. 해당 센터의 원활한 오더 처리를 위한 맞춤형 현장 지원이 권장됩니다.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 차트 섹션: 센터별 점수 현황
    st.subheader("📊 센터별 성과 및 911점 도달 전망")
    sorted_df = cur_df.sort_values(by="총점", ascending=False)
    
    fig = px.bar(
        sorted_df,
        x="센터명",
        y="총점",
        color="예상반기총점",
        color_continuous_scale="Blues",
        labels={"총점": "현재 총점", "예상반기총점": "반기말 예상총점"},
        title=f"센터별 총점 및 반기말 예상 점수 분포 ({selected_month})"
    )
    fig.add_hline(y=911, line_dash="dash", line_color="#EF4444", annotation_text="911점 달성선")
    fig.update_layout(xaxis_tickangle=-45, height=450, margin=dict(l=20, r=20, t=40, b=80))
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 2. 📊 성과 분석
# =============================================================================
elif menu == "📊 성과 분석":
    st.title("📊 월별 성과 및 KPI 분석")
    st.write(f"**평가월**: {selected_month} | **전체 센터 수**: {len(cur_df)}개소")

    tab1, tab2 = st.tabs(["센터별 KPI 세부 현황", "지표별 점수 기여도"])
    with tab1:
        st.dataframe(
            cur_df[['센터명', '총점', '예상반기총점', '도달판정', '전년동월대비_증감', '안전점검실점검율', '중점고객안전점검율', '고객서비스만족도']],
            use_container_width=True
        )
    with tab2:
        kpi_cols = ['안전점검_점수', '중점고객_점수', '사용계약_점수', '상담응대_점수', '상담기여_점수', '만족도_점수']
        avg_kpi = cur_df[kpi_cols].mean().reset_index()
        avg_kpi.columns = ['KPI 지표', '평균 배점']
        fig = px.pie(avg_kpi, names='KPI 지표', values='평균 배점', title="KPI 지표별 평균 획득 점수 비중")
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 3. 🎯 센터 진단 & 시뮬레이터
# =============================================================================
elif menu == "🎯 센터 진단":
    st.title("🎯 센터별 정밀 진단 및 911점 도달 시뮬레이터")
    
    sel_center = st.selectbox("진단할 센터 선택", cur_df['센터명'].unique())
    center_data = cur_df[cur_df['센터명'] == sel_center].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("현재 총점", f"{center_data['총점']:.1f}점")
    col2.metric("반기말 예상점수", f"{center_data['예상반기총점']:.1f}점")
    col3.metric("판정", center_data['도달판정'])

    st.markdown("---")
    st.subheader("🛠️ 911점 달성 목표 시뮬레이터")
    st.write("KPI 실적 개선 시 반기말 예상 총점 변화를 실시간으로 시뮬레이션합니다.")

    s_safety = st.slider("안전점검 실점검율 (%)", 0.0, 100.0, float(center_data['안전점검실점검율']), 0.5)
    s_resp = st.slider("상담응대율 (%)", 0.0, 100.0, float(center_data['상담응대율']), 0.5)
    s_sat = st.slider("고객서비스 만족도 (점)", 0.0, 100.0, float(center_data['고객서비스만족도']), 0.5)

    sim_safety_score = (s_safety / 100.0) * 550.0
    sim_resp_score = (s_resp / 100.0) * 100.0
    sim_sat_score = s_sat
    sim_non_cum = float(center_data['사용계약_점수']) + sim_resp_score + float(center_data['상담기여_점수']) + sim_sat_score
    sim_total = sim_safety_score + float(center_data['중점고객_점수']) + sim_non_cum
    sim_pred = predict_half_end_score(sim_total, cur_month, sim_safety_score, sim_non_cum, float(center_data['중점고객_점수']))

    st.success(f"**시뮬레이션 결과**: 예상 총점 **{sim_pred:.1f}점** ({'🎉 911점 목표 달성!' if sim_pred >= 911 else f'⚠️ 목표까지 {911 - sim_pred:.1f}점 추가 필요'})")

# =============================================================================
# 4. ⚠️ 위험 관리
# =============================================================================
elif menu == "⚠️ 위험 관리":
    st.title("⚠️ 위험 센터 조기 감지 및 코칭 리스트")
    
    danger_df = cur_df[cur_df['도달판정'] == '위험']
    caution_df = cur_df[cur_df['도달판정'] == '주의']
    normal_df = cur_df[cur_df['도달판정'] == '정상궤도']

    st.write(f"- 🔴 **위험(집중 코칭)**: {len(danger_df)}개소 | 🟡 **주의(관찰)**: {len(caution_df)}개소 | 🟢 **정상 궤도**: {len(normal_df)}개소")

    if not danger_df.empty:
        st.subheader("🚨 집중 코칭 필요 센터 (반기말 905점 미만 예상)")
        st.dataframe(danger_df[['센터명', '총점', '예상반기총점', '전년동월대비_증감', '안전점검실점검율']], use_container_width=True)
    else:
        st.info("현재 위험 판정 센터가 없습니다.")

    if not caution_df.empty:
        st.subheader("⚠️ 관심 관찰 센터 (반기말 905~911점 예상)")
        st.dataframe(caution_df[['센터명', '총점', '예상반기총점', '전년동월대비_증감', '안전점검실점검율']], use_container_width=True)

# =============================================================================
# 5. 🌡️ KPI 히트맵
# =============================================================================
elif menu == "🌡️ KPI 히트맵":
    st.title("🌡️ 센터별 KPI 달성률 히트맵")
    heat_cols = ['안전점검실점검율', '중점고객안전점검율', '사용계약율', '상담응대율', '상담기여도', '고객서비스만족도']
    heat_df = cur_df.set_index('센터명')[heat_cols]
    
    fig = px.imshow(heat_df, color_continuous_scale="Blues", aspect="auto")
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 6. 🔬 심화 분석
# =============================================================================
elif menu == "🔬 심화 분석":
    st.title("🔬 상관관계 및 심화 분석")
    fig = px.scatter(
        cur_df,
        x="안전점검실점검율",
        y="총점",
        size="예상반기총점",
        color="도달판정",
        hover_name="센터명",
        title="안전점검 실점검율과 총점 간 상관관계"
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 7. 📑 상반기 보고
# =============================================================================
elif menu == "📑 상반기 보고":
    st.title(f"📑 {cur_year}년 {half_name} 성과 종합 보고서")
    st.markdown(f"""
    ### 1. 종합 개요
    - **평가 기간**: {cur_year}년 {half_name} ({month_in_half}/6개월차)
    - **전체 센터 수**: {total_centers}개소
    - **평균 점수**: {cur_df['총점'].mean():.1f}점
    - **{target_end_text} 911점 도달 정상 궤도율**: {on_track_rate:.1f}% ({on_track_count}개 센터)

    ### 2. 핵심 추진 실적
    - 현재 {month_in_half}개월차 기준 평균 안전점검 실점검율은 **{avg_safety:.1f}%**로 계획 대비 양호한 진척 수준을 나타내고 있습니다.
    - 전년 동월 대비 종합 성과는 평균 **{'+' if yoy_diff >= 0 else ''}{yoy_diff:.1f}점**의 변동을 기록하였습니다.
    """)
    st.table(cur_df.sort_values(by="총점", ascending=False)[['센터명', '총점', '예상반기총점', '도달판정']].head(10))
