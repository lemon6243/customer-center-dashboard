"""
도시가스 고객센터 성과 대시보드
버전 3.1 - Phase 3 (작년 데이터 자동 분리 로드)
"""

import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components

from typing import Optional, Tuple

# 로컬 모듈
from score_calculator import calculate_scores
from data_loader import add_period_columns, validate_cumulative_data

# 유틸
from utils.styles import apply_global_styles
from utils.helpers import clean_dataframe

# 페이지 모듈
from pages_modules import (
    sidebar,
    home,
    performance,
    center_detail,
    risk,
    heatmap,
    deep_analysis,
    half_report,   # ⭐ 신규 추가
)


# ==================== 페이지 설정 ====================

# ==================== 페이지 설정 ====================

st.set_page_config(
    page_title="고객센터 성과 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Google Analytics 4 ====================
GA_MEASUREMENT_ID = "G-JKSWFV2Z13"
components.html(
    f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>
    """,
    height=0,
    width=0,
)

# 전역 CSS 적용
apply_global_styles()



# ==================== 데이터 로딩 ====================

@st.cache_data(ttl=3600, show_spinner=False)
def load_latest_data_from_github() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    GitHub의 latest_data.xlsx 자동 로드 후 금년/작년 데이터 분리
    
    Returns:
        (df_current_year, df_last_year)
        - df_current_year: 금년(가장 최근 연도) 데이터
        - df_last_year: 작년 데이터 (없으면 None)
    """
    data_path = "data/latest_data.xlsx"
    
    if not os.path.exists(data_path):
        return None, None
    
    try:
        if os.path.getsize(data_path) == 0:
            st.error("❌ 데이터 파일이 비어있습니다.")
            return None, None
        
        # 엑셀 읽기
        df_all = pd.read_excel(data_path, engine='openpyxl')
        
        if df_all.empty:
            st.error("❌ 데이터가 비어있습니다.")
            return None, None
        
        # 필수 컬럼 확인
        required_cols = ['센터명', '평가월']
        missing = [c for c in required_cols if c not in df_all.columns]
        if missing:
            st.error(f"❌ 필수 컬럼 누락: {missing}")
            return None, None
        
        # 데이터 정리
        df_all = add_period_columns(df_all)
        
        if df_all.empty:
            st.error("❌ 유효한 데이터가 없습니다.")
            return None, None
        
        # ⭐ 연도 기준으로 금년/작년 자동 분리
        df_all['_year'] = pd.to_datetime(df_all['평가월'], errors='coerce').dt.year
        
        years = sorted(df_all['_year'].dropna().unique())
        if not years:
            st.error("❌ 평가월에서 연도를 추출할 수 없습니다.")
            return None, None
        
        # 가장 최근 연도 = 금년, 그 이전 = 작년
        current_year = int(years[-1])
        df_current = df_all[df_all['_year'] == current_year].drop(columns=['_year']).copy()
        
        if len(years) >= 2:
            last_year = int(years[-2])
            df_last = df_all[df_all['_year'] == last_year].drop(columns=['_year']).copy()
        else:
            df_last = None
        
        # 금년 점수 컬럼 자동 계산 (없으면)
        required_scores = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수', '목표달성여부'
        ]
        if any(c not in df_current.columns for c in required_scores):
            df_current = calculate_scores(df_current)
        # GitHub 자동 로드 데이터도 업로드 데이터와 동일하게 검증
        is_valid, validation_errors, validation_warnings = validate_cumulative_data(df_current)

        # 관리자 전용 화면에서 표시할 수 있도록 보관
        st.session_state["data_validation_errors"] = validation_errors
        st.session_state["data_validation_warnings"] = validation_warnings
        
        # 오류는 데이터 사용을 막아야 하므로 관리자 여부와 무관하게 표시
        if not is_valid:
            st.error("데이터 검증 오류가 있습니다. 관리자에게 문의해주세요.")
            return None, df_last


        
        # 작년 데이터는 점수 재계산하지 않음 (구조가 다르므로 총점 그대로 사용)
        
        return df_current, df_last
        
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
        return None, None


# ==================== 페이지 라우팅 ====================

PAGE_ROUTER = {
    "🏠 홈": home.show,
    "📊 성과 분석": performance.show,
    "🎯 센터 진단": center_detail.show,
    "⚠️ 위험 관리": risk.show,
    "🌡️ KPI 히트맵": heatmap.show,
    "🔬 심화 분석": deep_analysis.show,
    "📑 상반기 보고": half_report.show,   # ⭐ 신규 추가
}


def render_page(selected_page: str, df: pd.DataFrame):
    """선택된 페이지 렌더링"""
    page_func = PAGE_ROUTER.get(selected_page)
    if page_func is None:
        st.error(f"❌ 알 수 없는 페이지: {selected_page}")
        return

    device_type = st.session_state.get('device_type', 'desktop')

    # heatmap만 device_type을 받지 않음
    if selected_page == "🌡️ KPI 히트맵":
        page_func(df)
    else:
        page_func(df, device_type=device_type)


# ==================== 메인 ====================

def main():
    """메인 함수"""
    
    try:
        # 헤더
        st.markdown(
            '<div class="main-header">🏢 예스코 고객센터 성과 대시보드</div>',
            unsafe_allow_html=True
        )
        
        # 초기 데이터 로드 (세션에 없으면)
        if 'df' not in st.session_state or st.session_state.get('df') is None:
            with st.spinner("📊 데이터 로드 중..."):
                df_current, df_last_year = load_latest_data_from_github()
                
                st.session_state['df'] = df_current
                st.session_state['df_last_year'] = df_last_year  # ⭐ 작년 데이터 저장
                
                if df_current is not None:
                    if df_last_year is not None and not df_last_year.empty:
                        st.success(
                            f"✅ 데이터 로드 완료! (금년 {len(df_current)}행 + 작년 {len(df_last_year)}행)",
                            icon="✅"
                        )
                    else:
                        st.success(
                            f"✅ 데이터 로드 완료! (금년 {len(df_current)}행, 작년 데이터 없음)",
                            icon="✅"
                        )
                else:
                    st.info("💡 저장된 데이터가 없습니다. 사이드바에서 새 데이터를 업로드해주세요.")
        
        # ===== 사이드바 =====
        selected_page = sidebar.show_navigation()
        sidebar.show_data_management()
        df_filtered = sidebar.show_filters()
        sidebar.show_settings()
        
        # ===== 메인 화면 =====
        if st.session_state.get('df') is None:
            _show_welcome()
        else:
            # 필터된 df가 있으면 그걸, 없으면 원본 사용
            df_to_show = df_filtered if df_filtered is not None else st.session_state['df']
            render_page(selected_page, df_to_show)
            
    except Exception as e:
        st.error(f"❌ 앱 실행 중 오류 발생: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


def _show_welcome():
    """데이터 없을 때 환영 화면"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### 👋 환영합니다!
        
        **시작하기:**
        1. 왼쪽 사이드바에서 엑셀 파일 업로드
        2. 처리된 데이터 다운로드
        3. GitHub에 업로드하여 팀 공유
        
        **또는**
        
        `data/latest_data.xlsx` 파일이 있다면 자동으로 로드됩니다.
        
        💡 **작년 데이터 포함 시**: 같은 파일에 작년 데이터(2025년 등)를 함께 넣으면 
        반기 전망에서 작년 동기와 비교할 수 있습니다.
        """)


if __name__ == "__main__":
    main()
