"""
홈 화면용 빠른 이동 버튼 컴포넌트
- 사용자 역할(센터장/본사/평가)에 따라 자주 가는 페이지로 즉시 이동
"""
import streamlit as st
from utils.styles import Colors


def quick_nav_buttons(items: list, columns: int = 4):
    """
    빠른 이동 버튼 그리드
    
    Args:
        items: [
            {"icon": "📊", "label": "월별 추이", "page_key": "월별 추이", "desc": "5개월 점수 변화"},
            ...
        ]
        columns: 한 줄에 표시할 버튼 수
    
    클릭 시 st.session_state['selected_page']에 page_key를 저장하고 rerun.
    """
    if not items:
        return

    cols = st.columns(columns)
    for idx, item in enumerate(items):
        col = cols[idx % columns]
        with col:
            label_text = f"{item.get('icon', '📌')} {item.get('label', '')}"
            desc = item.get('desc', '')
            page_key = item.get('page_key', '')

            # Streamlit 기본 버튼 사용 (rerun 자동)
            if st.button(label_text, key=f"quicknav_{idx}_{page_key}", use_container_width=True):
                st.session_state['selected_page'] = page_key
                st.rerun()

            if desc:
                st.markdown(
                    f'<div style="color:{Colors.TEXT_SECONDARY}; font-size:12px; text-align:center; margin-top:-8px; margin-bottom:8px;">{desc}</div>',
                    unsafe_allow_html=True
                )


def role_selector(default: str = "본사 담당자"):
    """
    역할 선택기 (홈 상단)
    
    Returns:
        선택된 역할 문자열
    """
    roles = ["🏢 본사 담당자", "👔 센터장/팀장", "📋 평가 담당자"]

    # 기본값 인덱스 찾기
    default_idx = 0
    for i, r in enumerate(roles):
        if default in r:
            default_idx = i
            break

    selected = st.radio(
        "역할 선택",
        roles,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="role_selector_home"
    )

    # 이모지 제거 후 반환
    return selected.split(" ", 1)[1] if " " in selected else selected
