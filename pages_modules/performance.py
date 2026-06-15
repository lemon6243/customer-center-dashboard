"""
📊 성과 분석 페이지
- 전체 현황 + 월별 추이 통합 (탭 구조)
"""
import streamlit as st
import pandas as pd

from pages_modules import overview, trend


def show(df: pd.DataFrame, device_type: str = "desktop"):
    """성과 분석 메인 함수 (탭 라우팅)"""

    if df is None or df.empty:
        st.warning("⚠️ 표시할 데이터가 없습니다.")
        return

    tab1, tab2 = st.tabs(["📊 전체 현황", "📈 월별 추이"])

    with tab1:
        overview.show(df, device_type=device_type)

    with tab2:
        trend.show(df, device_type=device_type)
