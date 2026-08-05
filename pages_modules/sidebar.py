"""
사이드바 모듈
- 네비게이션 메뉴
- 데이터 관리 (업로드/다운로드)
- 필터 옵션
- 설정
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from data_loader import load_cumulative_data, validate_cumulative_data
from score_calculator import calculate_scores

from utils.helpers import (
    safe_unique_centers, 
    convert_df_to_excel, 
    get_filename_with_timestamp
)


# ==================== 메뉴 정의 ====================

MENU_OPTIONS = [
    "🏠 홈",
    "📊 성과 분석",      # ⭐ 변경 (전체 현황 + 월별 추이)
    "🎯 센터 진단",      # ⭐ 변경 (구 "센터별 상세")
    "⚠️ 위험 관리",
    "🌡️ KPI 히트맵",
    "🔬 심화 분석",      # ⭐ 변경 (데이터 분석 + 원본 데이터)
    "📑 상반기 보고",   # ⭐ 신규 추가
]


# ==================== 네비게이션 ====================

def show_navigation() -> str:
    """사이드바 네비게이션 메뉴 표시"""
    
    with st.sidebar:
        st.markdown("## 📍 빠른 메뉴")
        
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = MENU_OPTIONS[0]
        
        current = st.session_state['current_page']
        default_index = MENU_OPTIONS.index(current) if current in MENU_OPTIONS else 0
        
        selected = st.radio(
            "페이지 이동",
            MENU_OPTIONS,
            index=default_index,
            label_visibility="collapsed"
        )
        
        st.session_state['current_page'] = selected
        st.markdown("---")
    
    return selected


# ==================== 데이터 정보 + 업로드 ====================

def show_data_management():
    """데이터 관리 섹션 (정보 표시 + 업로드)"""
    
    with st.sidebar:
        st.header("📂 데이터 관리")
        
        # 현재 데이터 정보
        if st.session_state.get('df') is not None:
            _show_data_info(st.session_state['df'])
        else:
            st.warning("⚠️ 데이터가 없습니다.")
        
        st.divider()
        
        # 새 데이터 업로드
        _show_uploader()


def _show_data_info(df: pd.DataFrame):
    """현재 데이터 정보 카드"""
    
    st.success("✅ 데이터 로드됨")
    
    center_count = len(safe_unique_centers(df))
    
    try:
        min_month = (
            df['평가월'].min().strftime('%Y-%m') 
            if df['평가월'].notna().any() else '-'
        )
        max_month = (
            df['평가월'].max().strftime('%Y-%m') 
            if df['평가월'].notna().any() else '-'
        )
    except Exception:
        min_month, max_month = '-', '-'
    
    st.info(f"""
    📌 **현재 데이터**
    - 총 행수: {len(df):,}
    - 센터 수: {center_count}개
    - 평가 기간: {min_month} ~ {max_month}
    - 최종 업데이트: GitHub 최신 버전
    """)


def _show_uploader():
    """새 데이터 업로드 UI"""
    
    st.subheader("📤 새 데이터 업로드")
    
    uploaded_file = st.file_uploader(
        "엑셀 파일 선택 (xlsx)",
        type=['xlsx'],
        help="월별 평가 데이터가 포함된 엑셀 파일을 업로드하세요"
    )
    
    if not uploaded_file:
        return
    
    with st.spinner("📊 데이터 처리 중..."):
        try:
            df_raw = load_cumulative_data(uploaded_file)
            
            if df_raw is None:
                st.error("❌ 데이터 로딩 실패. 파일 형식을 확인해주세요.")
                return
            
            is_valid, messages = validate_cumulative_data(df_raw)
            
            if not is_valid:
                st.error("❌ 데이터 검증 실패")
                for msg in messages:
                    st.error(msg)
                return
            
            # 검증 통과 → 점수 계산
            st.success("✅ 데이터 검증 완료")
            df_scored = calculate_scores(df_raw)
            st.session_state['df'] = df_scored
            
            center_count = len(safe_unique_centers(df_scored))
            st.info(f"""
            📊 **처리 완료**
            - 총 {len(df_scored):,}행
            - {center_count}개 센터
            - {df_scored['평가월'].nunique()}개월 데이터
            """)
            
            # 다운로드 버튼
            excel_data = convert_df_to_excel(df_scored)
            if excel_data:
                st.download_button(
                    label="💾 처리된 데이터 다운로드",
                    data=excel_data,
                    file_name=get_filename_with_timestamp("latest_data"),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="이 파일을 data/latest_data.xlsx로 저장 후 GitHub에 업로드하세요"
                )
                
                st.warning("""
                ⚠️ **다음 단계:**
                1. 위 버튼으로 파일 다운로드
                2. `data/latest_data.xlsx`로 저장
                3. GitHub에 커밋 & 푸시
                """)
                
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
            import traceback
            with st.expander("🔍 상세 오류 (개발자용)"):
                st.code(traceback.format_exc())


# ==================== 필터 ====================

def show_filters() -> pd.DataFrame:
    """
    필터 UI 표시 및 필터링된 데이터프레임 반환
    
    Returns:
        필터 적용된 DataFrame (없으면 원본)
    """
    df = st.session_state.get('df')
    if df is None:
        return None
    
    with st.sidebar:
        st.divider()
        st.subheader("🔍 필터")
        
        # 평가월 필터
        try:
            months = sorted(df['평가월'].dropna().dt.to_period('M').unique())
        except Exception:
            months = []
        
        selected_months = st.multiselect(
            "평가월 선택",
            options=months,
            default=months,
            format_func=lambda x: x.strftime('%Y년 %m월')
        )
        
        # 센터 필터
        centers = safe_unique_centers(df)
        selected_centers = st.multiselect(
            "센터 선택",
            options=centers,
            default=centers
        )
        
        # 필터 적용
        if selected_months and selected_centers:
            df_filtered = df[
                (df['평가월'].dt.to_period('M').isin(selected_months)) &
                (df['센터명'].isin(selected_centers))
            ]
            st.caption(f"필터 결과: {len(df_filtered):,}행")
            return df_filtered
    
    return df


# ==================== 설정/도움말 ====================

def show_settings():
    """설정 및 도움말 섹션"""
    
    with st.sidebar:
        st.divider()
        
        # 배점 규칙
        with st.expander("📖 배점 규칙"):
            st.markdown("""
            **총점: 1000점**
            
            - 안전점검: 550점
            - 중점고객: 100점
            - 사용계약: 50점
            - 상담응대: 100점
            - 상담기여: 100점
            - 만족도: 100점
            
            **목표: 911점 이상**
            """)
        
        # 화면 설정 (디바이스 모드)
        with st.expander("⚙️ 화면 설정"):
            device = st.radio(
                "디바이스 모드",
                options=['desktop', 'tablet', 'mobile'],
                index=0,
                format_func=lambda x: {
                    'desktop': '🖥️ 데스크톱',
                    'tablet': '📱 태블릿',
                    'mobile': '📱 모바일'
                }[x]
            )
            st.session_state['device_type'] = device
            st.caption("실제 배포 시에는 자동 감지됩니다")
        
        # 캐시 초기화
        st.divider()
        if st.button("🔄 캐시 초기화", help="데이터 로딩 문제가 있을 때 사용하세요"):
            st.cache_data.clear()
            st.session_state.clear()
            st.success("✅ 캐시가 초기화되었습니다. 페이지를 새로고침하세요.")
            st.rerun()
    # ==================== 관리자 전용: 데이터 품질 점검 ====================
        with st.sidebar.expander("⚙️ 관리자", expanded=False):
            admin_password = st.text_input(
                "관리자 비밀번호",
                type="password",
                key="admin_password_input",
            )
    
            expected_password = st.secrets.get("admin_password", "")
    
            if expected_password and admin_password == expected_password:
                st.success("관리자 모드")
    
                errors = st.session_state.get("data_validation_errors", [])
                warnings = st.session_state.get("data_validation_warnings", [])
    
                st.markdown("#### 데이터 품질 점검")
    
                if not errors and not warnings:
                    st.success("✅ 데이터 검증 결과 이상 없음")
    
                for message in errors:
                    st.error(message)
    
                for message in warnings:
                    st.warning(message)
    
            elif admin_password:
                st.error("비밀번호가 일치하지 않습니다.")

