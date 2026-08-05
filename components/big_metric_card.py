"""
홈 화면 핵심 지표 카드 컴포넌트
- 모든 카드의 높이·여백·값 위치를 동일하게 유지
"""

import streamlit as st

from utils.styles import Colors, get_score_color


def _footer_html(text: str | None, color: str | None = None) -> str:
    """카드 하단 보조문구 HTML"""
    if not text:
        return '<div class="yesco-metric-footer"></div>'

    text_color = color or Colors.TEXT_SUB

    return (
        f'<div class="yesco-metric-footer" '
        f'style="color:{text_color};">{text}</div>'
    )


def _render_metric_card(
    label: str,
    value_html: str,
    icon: str,
    accent_color: str,
    footer: str | None = None,
    footer_color: str | None = None,
    help_text: str | None = None,
):
    """통일된 핵심지표 카드 렌더링"""
    help_attr = f'title="{help_text}"' if help_text else ""

    html = f"""
    <div class="yesco-metric-card" {help_attr}
         style="border-top:3px solid {accent_color};">
        <div class="yesco-metric-header">
            <span style="font-size:18px;line-height:1;">{icon}</span>
            <span class="yesco-metric-label">{label}</span>
        </div>
        <div class="yesco-metric-value" style="color:{accent_color};">
            {value_html}
        </div>
        {_footer_html(footer, footer_color)}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def big_metric_card(
    label: str,
    value: str,
    delta: str = None,
    delta_color: str = "normal",
    icon: str = "📊",
    help_text: str = None,
):
    """일반 텍스트 값 핵심지표 카드"""
    footer_color = Colors.TEXT_SUB

    if delta and delta_color != "off":
        is_positive = delta.strip().startswith("+") or "▲" in delta

        if delta_color == "normal":
            footer_color = Colors.SUCCESS if is_positive else Colors.DANGER
        else:
            footer_color = Colors.DANGER if is_positive else Colors.SUCCESS

    _render_metric_card(
        label=label,
        value_html=value,
        icon=icon,
        accent_color=Colors.PRIMARY,
        footer=delta,
        footer_color=footer_color,
        help_text=help_text,
    )


def score_big_card(
    label: str,
    score: float,
    target: float = 911,
    icon: str = "🎯",
    delta: str = None,
    color: str = None,
    status_text: str = None,
    show_target: bool = True,
):
    """점수형 핵심지표 카드"""
    accent_color = color or get_score_color(score)

    target_html = ""

    if show_target:
        pct = (score / target * 100) if target else 0

        target_html = (
            f'<span style="font-size:14px;font-weight:500;'
            f'color:{Colors.TEXT_SUB};letter-spacing:0;">'
            f' / {target:,.0f} ({pct:.1f}%)</span>'
        )

    footer = status_text or delta
    footer_color = Colors.TEXT_SUB

    if delta and not status_text:
        is_positive = delta.strip().startswith("+") or "▲" in delta
        footer_color = Colors.SUCCESS if is_positive else Colors.DANGER

    _render_metric_card(
        label=label,
        value_html=f"{score:,.1f}점{target_html}",
        icon=icon,
        accent_color=accent_color,
        footer=footer,
        footer_color=footer_color,
        help_text="진행월에는 반기말 예측 페이스를 기준으로 해석합니다.",
    )


def count_big_card(
    label: str,
    count: int,
    total: int = None,
    icon: str = "📍",
    color: str = None,
    suffix: str = "개",
):
    """센터 수·건수용 핵심지표 카드"""
    accent_color = color or Colors.PRIMARY

    total_html = ""

    if total is not None and total > 0:
        pct = count / total * 100

        total_html = (
            f'<span style="font-size:14px;font-weight:500;'
            f'color:{Colors.TEXT_SUB};letter-spacing:0;">'
            f' / {total}{suffix} ({pct:.1f}%)</span>'
        )

    _render_metric_card(
        label=label,
        value_html=f"{count}{suffix}{total_html}",
        icon=icon,
        accent_color=accent_color,
        footer=None,
    )
