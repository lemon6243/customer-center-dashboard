"""
위험 관리 페이지
- 목표 미달 예상 센터 식별
- 위험도별 분류 표시
"""

import streamlit as st
import pandas as pd
from utils.styles import ScoreThresholds
from utils.helpers import get_period_info
from utils.prediction import add_predictions_to_df, get_risk_level
from components.kpi_card import risk_card


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """위험 관리 페이지 메인 함수"""
    
    try:
        latest_month = df['평가월'].max()
        df_latest = df[df['평가월'] == latest_month].copy()
        
        period_info = get_period_info(latest_month)
        period_month = period_info['period_month']
        
        # 예측 점수 계산
        with st.spinner("🔮 위험도 분석 중..."):
            df_latest = add_predictions_to_df(df_latest, period_month)
        
        # 목표 미달 센터 추출
        risk_centers = df_latest[
            df_latest['예측점수'] < ScoreThresholds.TARGET
        ].copy()
        
        # 위험도 순으로 정렬 (낮은 예측점수 = 더 위험)
        risk_centers = risk_centers.sort_values('예측점수', ascending=True)
        
        # 결과 없을 때
        if len(risk_centers) == 0:
            st.success("🎉 모든 센터가 목표 달성 예상입니다!")
            _show_summary_stats(df_latest)
            return
        
        # 요약 헤더
        _show_risk_summary(risk_centers, df_latest, period_info)
        
        st.divider()
        
        # 위험 센터별 카드
        st.subheader(f"⚠️ 위험 센터 상세 ({len(risk_centers)}개)")
        
        for _, row in risk_centers.iterrows():
            risk_card(
                center_name=row['센터명'],
                current_score=row['총점'],
                predicted_score=row['예측점수'],
                target=ScoreThresholds.TARGET
            )
        
    except Exception as e:
        st.error(f"❌ 위험 관리 분석 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


def _show_risk_summary(risk_centers, df_latest, period_info):
    """위험 센터 요약 카드"""
    
    total = len(df_latest)
    risk_count = len(risk_centers)
    safe_count = total - risk_count
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "전체 센터",
            f"{total}개"
        )
    
    with col2:
        st.metric(
            "🟢 달성 예상",
            f"{safe_count}개",
            delta=f"{safe_count/total*100:.0f}%" if total > 0 else "0%"
        )
    
    with col3:
        st.metric(
            "🔴 위험 센터",
            f"{risk_count}개",
            delta=f"{risk_count/total*100:.0f}%" if total > 0 else "0%",
            delta_color="inverse"
        )
    
    with col4:
        avg_gap = (risk_centers['예측점수'] - ScoreThresholds.TARGET).mean()
        st.metric(
            "평균 목표 미달",
            f"{avg_gap:+.1f}점"
        )


def _show_summary_stats(df_latest):
    """모든 센터 달성 시 보여줄 요약"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "전체 센터",
            f"{len(df_latest)}개"
        )
    
    with col2:
        avg = df_latest['예측점수'].mean()
        st.metric(
            "평균 예측 점수",
            f"{avg:.1f}점",
            delta=f"목표 +{avg - ScoreThresholds.TARGET:.1f}"
        )
    
    with col3:
        min_score = df_latest['예측점수'].min()
        st.metric(
            "최저 예측 점수",
            f"{min_score:.1f}점",
            delta=f"목표 +{min_score - ScoreThresholds.TARGET:.1f}"
        )
