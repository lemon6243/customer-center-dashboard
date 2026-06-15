"""
🔬 심화 분석 페이지
- 데이터 분석 + 원본 데이터 통합 (탭 구조)
"""
import streamlit as st
import pandas as pd

from pages_modules import analysis, raw_data


def show(df: pd.DataFrame, device_type: str = "desktop"):
    """심화 분석 메인 함수 (탭 라우팅)"""

    if df is None or df.empty:
        st.warning("⚠️ 표시할 데이터가 없습니다.")
        return

    tab1, tab2 = st.tabs(["🔬 분석", "📋 원본 데이터"])

    with tab1:
        analysis.show(df, device_type=device_type)

    with tab2:
        raw_data.show(df, device_type=device_type)
