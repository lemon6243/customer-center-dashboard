"""
원본 데이터 페이지
- 데이터프레임 전체 표시
- Excel 다운로드
"""

import streamlit as st
import pandas as pd
from utils.helpers import convert_df_to_excel, get_filename_with_timestamp


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """원본 데이터 페이지 메인 함수"""
    
    st.subheader("📋 원본 데이터")
    st.caption("업로드된 평가 데이터를 그대로 확인할 수 있습니다.")
    
    try:
        # 데이터 통계 요약
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 행수", f"{len(df):,}")
        with col2:
            st.metric("컬럼 수", f"{len(df.columns)}")
        with col3:
            if '평가월' in df.columns and df['평가월'].notna().any():
                period = f"{df['평가월'].min().strftime('%Y-%m')} ~ {df['평가월'].max().strftime('%Y-%m')}"
                st.metric("평가 기간", period)
        
        st.divider()
        
        # 데이터프레임 표시
        st.dataframe(
            df,
            use_container_width=True,
            height=600
        )
        
        # 다운로드 버튼
        excel_data = convert_df_to_excel(df)
        
        if excel_data:
            st.download_button(
                label="💾 데이터 다운로드 (Excel)",
                data=excel_data,
                file_name=get_filename_with_timestamp("dashboard_data"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"❌ 데이터 표시 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
