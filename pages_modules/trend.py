"""
월별 추이 페이지
- 센터별 총점 추이
- 항목별 추이
"""

import streamlit as st
import pandas as pd
from utils.half_year import get_latest_month, filter_current_half, get_half
from utils.helpers import safe_unique_centers
from components.score_chart import create_monthly_trend_line


# KPI 옵션 매핑
KPI_OPTIONS = {
    '안전점검': '안전점검_점수',
    '중점고객': '중점고객_점수',
    '사용계약': '사용계약_점수',
    '상담응대': '상담응대_점수',
    '상담기여': '상담기여_점수',
    '만족도': '만족도_점수',
}


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """월별 추이 페이지 메인 함수"""
    
    try:
        st.subheader("🎯 센터별 추이 비교")
        
        # 센터 선택
        all_centers = safe_unique_centers(df)
        
        if not all_centers:
            st.warning("⚠️ 분석 가능한 센터 데이터가 없습니다.")
            return
        
        centers = st.multiselect(
            "비교할 센터 선택",
            options=all_centers,
            default=all_centers,
            help="비교하고 싶은 센터를 선택하세요. 기본값은 전체 센터입니다."
        )
        
        if not centers:
            st.warning("⚠️ 센터를 선택하세요.")
            return
        
        df_filtered = df[df['센터명'].isin(centers)]

        # 최신 평가월이 속한 현재 반기만 표시
        latest_month = get_latest_month(df_filtered)
        
        if latest_month is None:
            st.warning("⚠️ 평가월 데이터를 확인해주세요.")
            return
        
        df_filtered = filter_current_half(df_filtered, latest_month)
        half_label = get_half(latest_month)
        
        st.caption(
            f"📅 현재 표시 구간: {latest_month.year}년 {half_label} "
            f"({latest_month.month if latest_month.month <= 6 else latest_month.month - 6}/6개월차)"
        )

        
        # ====== 총점 추이 ======
        fig = create_monthly_trend_line(
            df_filtered,
            y_col='총점',
            title=f'센터별 {half_label} 월별 총점 추이'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # ====== 항목별 추이 ======
        st.subheader("📊 항목별 추이")
        
        selected_kpi = st.selectbox(
            "분석할 항목 선택",
            options=list(KPI_OPTIONS.keys())
        )
        
        kpi_col = KPI_OPTIONS[selected_kpi]
        
        if kpi_col in df_filtered.columns:
            fig2 = create_monthly_trend_line(
                df_filtered,
                y_col=kpi_col,
                title=f'{half_label} {selected_kpi} 월별 추이'
            )
            # 항목별 차트는 좀 더 낮게
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning(f"⚠️ '{kpi_col}' 컬럼이 데이터에 없습니다.")
            
    except Exception as e:
        st.error(f"❌ 추이 분석 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
