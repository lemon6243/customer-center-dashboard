"""
KPI 히트맵 페이지
3가지 히트맵 뷰 제공:
  - Tab 1: 센터 × KPI 달성률 (최신월 기준)
  - Tab 2: 센터 × 월별 총점 (전체 월 추이)
  - Tab 3: 월별 KPI 평균 (전체 센터 평균)
"""

import streamlit as st
import pandas as pd

# 기존 kpi_heatmap.py의 show_kpi_heatmap 함수를 그대로 사용
# (해당 모듈이 잘 작성되어 있어서 그대로 재활용)
from kpi_heatmap import show_kpi_heatmap


def show(df: pd.DataFrame):
    """KPI 히트맵 페이지 메인 함수"""
    show_kpi_heatmap(df)
