"""
전체 현황 페이지
- 핵심 KPI 카드
- 센터별 점수 랭킹 (현재 + 예측)
- 상세 점수표
"""

import streamlit as st
import pandas as pd
from utils.styles import Colors, ScoreThresholds
from utils.helpers import get_period_info
from utils.prediction import add_predictions_to_df
from components.kpi_card import info_box
from components.score_chart import create_center_ranking_bar


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """전체 현황 페이지 메인 함수"""
    
    try:
        # 필수 컬럼 확인
        required_cols = ['총점', '목표달성여부']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"❌ 필수 컬럼 누락: {missing}")
            return
        
        # 최신 월 데이터 추출
        latest_month = df['평가월'].max()
        df_latest = df[df['평가월'] == latest_month].copy()
        
        # 반기 정보
        period_info = get_period_info(latest_month)
        period_month = period_info['period_month']
        
        # 예측 점수 계산
        with st.spinner("🔮 예측 점수 계산 중..."):
            df_latest = add_predictions_to_df(df_latest, period_month)
        
        # ====== 핵심 KPI 카드 ======
        _show_key_metrics(df_latest, period_info, device_type)
        
        st.divider()
        
        # ====== 예측 로직 안내 ======
        if period_month < 6:
            info_box(
                title="개선된 예측 로직 안내",
                content=(
                    f"현재: <b>{period_info['period_text']}</b> "
                    f"(진행률 {period_info['progress_rate']*100:.1f}%)<br>"
                    "• <b>누적형 지표</b> (안전점검·중점고객·사용계약): 진행률 기반 예측<br>"
                    "• <b>비누적형 지표</b> (상담응대·상담기여·만족도): 현재 점수 유지<br>"
                    "• 예측 총점은 1000점을 초과하지 않도록 제한됩니다"
                ),
                icon="💡"
            )
        
        # ====== 센터별 랭킹 차트 ======
        st.subheader(f"🏆 센터별 현재 점수 및 예측 ({latest_month.strftime('%Y년 %m월')} 기준)")
        
        df_sorted = df_latest.sort_values('총점', ascending=False).reset_index(drop=True)
        df_sorted['순위'] = range(1, len(df_sorted) + 1)
        
        # 차트용 정렬 (낮은 점수가 아래로)
        df_chart = df_sorted.sort_values('총점', ascending=True)
        
        chart_height = 400 if device_type == 'mobile' else 600
        fig = create_center_ranking_bar(
            df_chart,
            show_predicted=(period_month < 6),
            height=chart_height
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # ====== 상세 점수표 ======
        _show_score_table(df_sorted)
        
    except Exception as e:
        st.error(f"❌ 전체 현황 표시 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


def _show_key_metrics(df_latest: pd.DataFrame, period_info: dict, device_type: str):
    """핵심 KPI 4개 카드 표시"""
    
    if device_type == 'mobile':
        col_count = 2
    else:
        col_count = 4
    
    cols = st.columns(col_count)
    
    avg_score = df_latest['총점'].mean()
    avg_predicted = df_latest['예측점수'].mean()
    target_achieved = (df_latest['예측점수'] >= ScoreThresholds.TARGET).sum()
    total_centers = len(df_latest)
    
    with cols[0]:
        st.metric(
            label="📊 평균 점수",
            value=f"{avg_score:.1f}",
            delta=f"예측: {avg_predicted:.1f}",
            help="현재 누적 점수 및 6월 예측 점수"
        )
    
    with cols[1]:
        achievement_rate = target_achieved / total_centers * 100 if total_centers > 0 else 0
        st.metric(
            label="🎯 목표 달성",
            value=f"{target_achieved}/{total_centers}",
            delta=f"{achievement_rate:.1f}%",
            help=f"예측 점수 {ScoreThresholds.TARGET}점 이상 센터 수"
        )
    
    if col_count >= 3:
        with cols[2]:
            st.metric(
                label="📅 현재 진행",
                value=period_info['period_text'],
                delta=f"{period_info['period_month']}/6개월"
            )
        
        with cols[3]:
            st.metric(
                label="🏁 목표 점수",
                value=f"{ScoreThresholds.TARGET}점",
                delta="반기 최종"
            )


def _show_score_table(df_sorted: pd.DataFrame):
    """상세 점수표 (expander 안)"""
    
    with st.expander("📋 상세 점수표 보기 (예측 점수 포함)", expanded=True):
        display_cols = [
            '순위', '센터명', '총점', '예측점수', '목표대비',
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수'
        ]
        
        df_display = df_sorted[display_cols].copy()
        df_display['목표대비'] = (df_display['예측점수'] - ScoreThresholds.TARGET).round(1)
        
        st.dataframe(
            df_display.style.format({
                '총점': '{:.1f}',
                '예측점수': '{:.1f}',
                '목표대비': '{:+.1f}',
                '안전점검_점수': '{:.1f}',
                '중점고객_점수': '{:.1f}',
                '사용계약_점수': '{:.1f}',
                '상담응대_점수': '{:.1f}',
                '상담기여_점수': '{:.1f}',
                '만족도_점수': '{:.1f}'
            }).background_gradient(
                subset=['예측점수'], 
                cmap='RdYlGn', 
                vmin=850, 
                vmax=950
            ),
            use_container_width=True,
            hide_index=True,
            height=600
        )
