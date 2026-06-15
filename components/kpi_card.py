"""
KPI 카드 컴포넌트
- 메트릭 카드 (st.metric 래핑)
- 점수 카드 (색상 자동 적용)
- 등급 배지
"""

import streamlit as st
from utils.styles import Colors, get_score_color, get_score_grade
from utils.helpers import safe_unique_centers


def metric_card(label: str, value: str, delta: str = None, help_text: str = None):
    """
    기본 메트릭 카드 (st.metric 래퍼)
    
    Args:
        label: 카드 라벨 (예: "📊 평균 점수")
        value: 메인 값 (예: "892.3")
        delta: 변동값 또는 보조 텍스트 (예: "예측: 925.1")
        help_text: 툴팁 텍스트
    """
    st.metric(label=label, value=value, delta=delta, help=help_text)


def score_card(label: str, score: float, target: float = 911, 
               show_gap: bool = True, help_text: str = None):
    """
    점수 카드 - 목표 대비 자동 색상 적용
    
    Args:
        label: 카드 라벨
        score: 점수
        target: 목표 점수 (기본 911)
        show_gap: 목표 대비 차이 표시 여부
    """
    gap = score - target
    delta = f"{gap:+.1f}점 (목표 대비)" if show_gap else None
    
    st.metric(
        label=label,
        value=f"{score:.1f}점",
        delta=delta,
        delta_color="normal" if gap >= 0 else "inverse",
        help=help_text,
    )


def grade_badge(score: float) -> str:
    """
    점수에 따른 등급 배지 HTML 반환
    
    Returns:
        예: '<span style="...">🟢 달성</span>'
    """
    grade, color, emoji = get_score_grade(score)
    
    return f"""
    <span style="
        display: inline-block;
        padding: 4px 12px;
        background-color: {color}22;
        color: {color};
        border: 1px solid {color};
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
    ">{emoji} {grade}</span>
    """


def info_box(title: str, content: str, color: str = None, icon: str = "💡"):
    """
    정보 박스 (색상 강조)
    
    Args:
        title: 박스 제목
        content: 내용 (HTML 가능)
        color: 강조 색상 (None이면 PRIMARY)
        icon: 아이콘 이모지
    """
    if color is None:
        color = Colors.PRIMARY
    
    st.markdown(f"""
    <div style="
        background-color: {color}11;
        border-left: 4px solid {color};
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    ">
        <div style="
            font-weight: 700;
            color: {color};
            font-size: 1rem;
            margin-bottom: 0.4rem;
        ">{icon} {title}</div>
        <div style="
            color: {Colors.TEXT_MAIN};
            font-size: 0.95rem;
            line-height: 1.5;
        ">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def risk_card(center_name: str, current_score: float, predicted_score: float, 
              target: float = 911):
    """
    위험 센터 카드 (위험 관리 페이지용)
    
    Args:
        center_name: 센터명
        current_score: 현재 점수
        predicted_score: 예측 점수
        target: 목표 점수
    """
    grade, color, emoji = get_score_grade(predicted_score)
    gap = predicted_score - target
    
    st.markdown(f"""
    <div style="
        background-color: {color}15;
        border-left: 5px solid {color};
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
    ">
        <h4 style="color: {color}; margin: 0 0 0.5rem 0; font-size: 1.1rem;">
            {emoji} {center_name} <span style="font-size: 0.9rem; font-weight: 500;">- {grade}</span>
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("현재 점수", f"{current_score:.1f}")
    with col2:
        st.metric("예측 점수", f"{predicted_score:.1f}")
    with col3:
        st.metric("목표 대비", f"{gap:+.1f}", delta_color="inverse")


def summary_metrics_row(metrics: list, device_type: str = 'desktop'):
    """
    여러 메트릭을 한 줄에 표시 (반응형)
    
    Args:
        metrics: 메트릭 딕셔너리 리스트
            예: [{'label': '평균', 'value': '892', 'delta': '+5'}, ...]
        device_type: 'desktop' | 'tablet' | 'mobile'
    """
    if device_type == 'mobile':
        col_count = 2
    elif device_type == 'tablet':
        col_count = 2
    else:
        col_count = min(len(metrics), 4)
    
    cols = st.columns(col_count)
    
    for i, m in enumerate(metrics):
        with cols[i % col_count]:
            st.metric(
                label=m.get('label', ''),
                value=m.get('value', ''),
                delta=m.get('delta', None),
                help=m.get('help', None),
            )
