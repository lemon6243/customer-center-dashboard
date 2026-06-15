"""
도시가스 고객센터 성과 대시보드
버전 3.0 - 모듈화 리뉴얼 (Phase 1 완료)
"""

import streamlit as st
import pandas as pd
import os
from typing import Optional

# 로컬 모듈
from score_calculator import calculate_scores

# 유틸
from utils.styles import apply_global_styles
from utils.helpers import clean_dataframe

# 페이지 모듈
from pages_modules import (
    home,
    performance,        # ⭐ 신규
    center_detail,
    risk,
    heatmap,
    deep_analysis,      # ⭐ 신규
)


# ==================== 페이지 설정 ====================

st.set_page_config(
    page_title="고객센터 성과 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 전역 CSS 적용
apply_global_styles()


# ==================== 데이터 로딩 ====================

@st.cache_data(ttl=3600, show_spinner=False)
def load_latest_data_from_github() -> Optional[pd.DataFrame]:
    """GitHub의 latest_data.xlsx 자동 로드"""
    
    data_path = "data/latest_data.xlsx"
    
    if not os.path.exists(data_path):
        return None
    
    try:
        # 파일 크기 확인
        if os.path.getsize(data_path) == 0:
            st.error("❌ 데이터 파일이 비어있습니다.")
            return None
        
        # 엑셀 읽기
        df = pd.read_excel(data_path, engine='openpyxl')
        
        if df.empty:
            st.error("❌ 데이터가 비어있습니다.")
            return None
        
        # 필수 컬럼 확인
        required_cols = ['센터명', '평가월']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"❌ 필수 컬럼 누락: {missing}")
            return None
        
        # 데이터 정리 (NaN, 잘못된 값 제거)
        df = clean_dataframe(df)
        
        if df.empty:
            st.error("❌ 유효한 데이터가 없습니다.")
            return None
        
        # 점수 컬럼 자동 계산
        required_scores = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수', '목표달성여부'
        ]
        if any(c not in df.columns for c in required_scores):
            df = calculate_scores(df)
        
        return df
        
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
        return None


# ==================== 페이지 라우팅 ====================

PAGE_ROUTER = {
    "🏠 홈": home.show,
    "📊 성과 분석": performance.show,        # ⭐ 변경
    "🎯 센터 진단": center_detail.show,       # ⭐ 변경 (메뉴명만)
    "⚠️ 위험 관리": risk.show,
    "🌡️ KPI 히트맵": heatmap.show,
    "🔬 심화 분석": deep_analysis.show,       # ⭐ 변경
}


def render_page(selected_page: str, df: pd.DataFrame):
    """선택된 페이지 렌더링"""
    
    page_func = PAGE_ROUTER.get(selected_page)
    
    if page_func is None:
        st.error(f"❌ 알 수 없는 페이지: {selected_page}")
        return
    
    device_type = st.session_state.get('device_type', 'desktop')
    
    # heatmap만 device_type을 받지 않음 (기존 모듈 호환)
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
            '<div class="main-header">🏢 도시가스 고객센터 성과 대시보드</div>',
            unsafe_allow_html=True
        )
        
        # 초기 데이터 로드 (세션에 없으면)
        if 'df' not in st.session_state or st.session_state.get('df') is None:
            with st.spinner("📊 데이터 로드 중..."):
                df_loaded = load_latest_data_from_github()
                st.session_state['df'] = df_loaded
                
                if df_loaded is not None:
                    st.success("✅ 데이터 로드 완료!", icon="✅")
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
        """)


if __name__ == "__main__":
    main()
