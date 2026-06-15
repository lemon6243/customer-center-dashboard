"""
센터별 상세 페이지
- 센터 선택
- 핵심 지표 카드
- 항목별 레이더 차트
"""

import streamlit as st
import pandas as pd
from utils.styles import ScoreThresholds
from utils.helpers import safe_unique_centers, get_period_info
from utils.prediction import calculate_predicted_score
from components.score_chart import create_kpi_radar_chart
from utils.simulator import (
    get_current_kpi_values,
    calculate_simulated_score,
    find_minimum_combo,
    CUMULATIVE_KPIS,
    VARIABLE_KPIS,
    TARGET_TOTAL,
)


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """센터별 상세 페이지 메인 함수"""
    
    try:
        all_centers = safe_unique_centers(df)
        
        if not all_centers:
            st.warning("⚠️ 분석 가능한 센터 데이터가 없습니다.")
            return
        
        # 센터 선택
        if device_type == 'mobile':
            center_name = st.selectbox("센터 선택", options=all_centers)
        else:
            col1, _ = st.columns([2, 1])
            with col1:
                center_name = st.selectbox("센터 선택", options=all_centers)
        
        # 해당 센터 데이터 필터링
        df_center = df[df['센터명'] == center_name].sort_values('평가월')
        
        if df_center.empty:
            st.warning("⚠️ 선택한 센터의 데이터가 없습니다.")
            return
        
        latest = df_center.iloc[-1]
        period_info = get_period_info(latest['평가월'])
        period_month = period_info['period_month']
        
        # 예측 점수
        prediction = calculate_predicted_score(latest, period_month)
        predicted_score = prediction['예측총점']
        
        # ====== 핵심 지표 카드 ======
        _show_center_metrics(
            latest, predicted_score, period_info, 
            df, all_centers, device_type
        )
        
        st.divider()
        
        # ====== 레이더 차트 ======
        st.subheader("📊 항목별 점수 (레이더 차트)")
        
        scores = {
            '안전점검': latest.get('안전점검_점수', 0),
            '중점고객': latest.get('중점고객_점수', 0),
            '사용계약': latest.get('사용계약_점수', 0),
            '상담응대': latest.get('상담응대_점수', 0),
            '상담기여': latest.get('상담기여_점수', 0),
            '만족도': latest.get('만족도_점수', 0),
        }
        
        fig = create_kpi_radar_chart(scores, center_name=center_name)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ 센터별 상세 분석 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


def _show_center_metrics(latest, predicted_score, period_info, 
                          df, all_centers, device_type):
    """센터의 핵심 4개 지표 표시"""
    
    col_count = 2 if device_type == 'mobile' else 4
    cols = st.columns(col_count)
    
    target = ScoreThresholds.TARGET
    
    # 1) 현재 총점
    with cols[0]:
        st.metric(
            label="현재 총점",
            value=f"{latest['총점']:.1f}점",
            delta=f"{latest['총점'] - target:.1f}점"
        )
    
    # 2) 6월 예측 또는 목표 달성 여부
    with cols[1]:
        if period_info['period_month'] < 6:
            st.metric(
                label="6월 예측",
                value=f"{predicted_score:.1f}점",
                delta=f"{predicted_score - target:.1f}점",
                help="진행률 기반 예측"
            )
        else:
            achieved = latest.get('목표달성여부', False)
            st.metric(
                label="목표 달성",
                value="달성" if achieved else "미달성",
                delta="✅" if achieved else "❌"
            )
    # show() 함수 마지막에 호출
    _render_simulation_section(df, selected_center)
    # 데스크톱/태블릿에서만 추가 카드 표시
    if col_count >= 3:
        # 3) 전체 순위
        with cols[2]:
            latest_month_df = df[df['평가월'] == df['평가월'].max()]
            rank = (latest_month_df['총점'] >= latest['총점']).sum()
            st.metric(
                label="전체 순위",
                value=f"{rank}위",
                delta=f"/ {len(all_centers)}개"
            )
        
        # 4) 진행 상황
        with cols[3]:
            st.metric(
                label="진행 상황",
                value=period_info['period_text'],
                delta=f"{period_info['progress_rate']*100:.1f}%"
            )
