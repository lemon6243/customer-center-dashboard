"""
홈 화면용 큰 KPI 카드 컴포넌트
- 임원/관리자가 30초 안에 핵심 지표를 파악할 수 있도록 시각적 강조
"""
import streamlit as st
from utils.styles import Colors, get_score_color


def big_metric_card(
    label: str,
    value: str,
    delta: str = None,
    delta_color: str = "normal",  # "normal", "inverse", "off"
    icon: str = "📊",
    help_text: str = None,
):
    """
    큰 메트릭 카드 (홈 화면용)
    
    Args:
        label: 지표 이름 (예: "전체 평균 점수")
        value: 메인 값 (예: "887.3")
        delta: 변화량 (예: "+12.5 vs 전월")
        delta_color: "normal"(상승=초록), "inverse"(상승=빨강), "off"(회색)
        icon: 아이콘 이모지
        help_text: 도움말 (마우스 호버 시 표시)
    """
    # delta 색상 결정
    if delta and delta_color != "off":
        is_positive = delta.strip().startswith("+")
        if delta_color == "normal":
            color = Colors.SUCCESS if is_positive else Colors.DANGER
        else:  # inverse
            color = Colors.DANGER if is_positive else Colors.SUCCESS
        delta_html = f'<div style="color:{color}; font-size:14px; font-weight:600; margin-top:4px;">{delta}</div>'
    elif delta:
        delta_html = f'<div style="color:{Colors.TEXT_SUB}; font-size:14px; margin-top:4px;">{delta}</div>'
    else:
        delta_html = ""

    help_attr = f'title="{help_text}"' if help_text else ""

    html = f"""
    <div {help_attr} style="
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-left: 4px solid {Colors.PRIMARY};
        border-radius: 12px;
        padding: 20px 24px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="font-size:20px;">{icon}</span>
            <span style="color:{Colors.TEXT_SUB}; font-size:13px; font-weight:500;">{label}</span>
        </div>
        <div style="color:{Colors.TEXT_MAIN}; font-size:32px; font-weight:700; line-height:1.2;">
            {value}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def score_big_card(label: str, score: float, target: float = 911, icon: str = "🎯", delta: str = None):
    """
    점수 전용 큰 카드 (목표 대비 색상 자동 적용)
    
    Args:
        label: 카드 라벨
        score: 현재 점수
        target: 목표 점수 (기본 911)
        icon: 아이콘
        delta: 변화량 텍스트
    """
    color = get_score_color(score)
    pct = (score / target * 100) if target > 0 else 0

    delta_html = ""
    if delta:
        is_positive = delta.strip().startswith("+")
        d_color = Colors.SUCCESS if is_positive else Colors.DANGER
        delta_html = f'<div style="color:{d_color}; font-size:14px; font-weight:600; margin-top:4px;">{delta}</div>'

    html = f"""
    <div style="
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px 24px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="font-size:20px;">{icon}</span>
            <span style="color:{Colors.TEXT_SUB}; font-size:13px; font-weight:500;">{label}</span>
        </div>
        <div style="color:{color}; font-size:32px; font-weight:700; line-height:1.2;">
            {score:,.1f}
            <span style="font-size:14px; color:{Colors.TEXT_SUB}; font-weight:400;">
                / {target:,.0f} ({pct:.1f}%)
            </span>
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def count_big_card(label: str, count: int, total: int = None, icon: str = "📍", color: str = None, suffix: str = "개"):
    """
    개수 전용 큰 카드 (예: 위험 센터 3개 / 전체 24개)
    """
    if color is None:
        color = Colors.PRIMARY

    total_html = ""
    if total is not None and total > 0:
        pct = count / total * 100
        total_html = f'<span style="font-size:14px; color:{Colors.TEXT_SUB}; font-weight:400;"> / {total}{suffix} ({pct:.1f}%)</span>'

    html = f"""
    <div style="
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px 24px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="font-size:20px;">{icon}</span>
            <span style="color:{Colors.TEXT_SUB}; font-size:13px; font-weight:500;">{label}</span>
        </div>
        <div style="color:{color}; font-size:32px; font-weight:700; line-height:1.2;">
            {count}{suffix}{total_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
