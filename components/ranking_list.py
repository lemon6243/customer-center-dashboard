"""
홈 화면용 랭킹 리스트 컴포넌트
- Top 5 / Bottom 5 센터 표시
- 점수 순 / 상승·하락 폭 순 토글 가능
"""
import streamlit as st
import pandas as pd
from utils.styles import Colors, get_score_color


def _rank_badge_html(i: int) -> str:
    """순위 배지 HTML 반환"""
    if i == 1:
        return "🥇"
    elif i == 2:
        return "🥈"
    elif i == 3:
        return "🥉"
    else:
        return (
            f'<span style="display:inline-block;width:22px;height:22px;'
            f'border-radius:50%;background:{Colors.BG_CARD};'
            f'border:1px solid {Colors.BORDER};text-align:center;'
            f'font-size:12px;font-weight:600;color:{Colors.TEXT_SUB};">{i}</span>'
        )


def ranking_list(
    df: pd.DataFrame,
    title: str,
    value_col: str = "총점",
    name_col: str = "센터명",
    n: int = 5,
    ascending: bool = False,
    icon: str = "🏆",
    show_rank: bool = True,
    value_format: str = "{:,.1f}점",
    use_score_color: bool = True,
):
    """랭킹 리스트 표시"""
    if df is None or df.empty or value_col not in df.columns:
        st.info(f"{title}: 표시할 데이터가 없습니다.")
        return

    df_sorted = (
        df.dropna(subset=[value_col, name_col])
        .sort_values(value_col, ascending=ascending)
        .head(n)
    )

    if df_sorted.empty:
        st.info(f"{title}: 표시할 데이터가 없습니다.")
        return

    rows_html = ""
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        name = str(row[name_col])
        value = row[value_col]

        if use_score_color and value_col == "총점":
            value_color = get_score_color(value)
        elif ascending:
            value_color = Colors.DANGER
        else:
            value_color = Colors.SUCCESS

        rank_html = ""
        if show_rank:
            badge = _rank_badge_html(i)
            rank_html = f'<span style="width:30px;text-align:center;display:inline-block;">{badge}</span>'

        try:
            value_str = value_format.format(value)
        except Exception:
            value_str = str(value)

        # ⚠️ HTML 줄바꿈/들여쓰기 없이 한 줄로!
        rows_html += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 12px;border-bottom:1px solid {Colors.BG_GRAY};">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'{rank_html}'
            f'<span style="color:{Colors.TEXT_MAIN};font-size:14px;font-weight:500;">{name}</span>'
            f'</div>'
            f'<span style="color:{value_color};font-size:15px;font-weight:700;">{value_str}</span>'
            f'</div>'
        )

    html = (
        f'<div style="background:{Colors.BG_CARD};border:1px solid {Colors.BORDER};'
        f'border-radius:12px;padding:16px 8px 8px 8px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<div style="padding:0 12px 12px 12px;border-bottom:2px solid {Colors.PRIMARY};'
        f'margin-bottom:4px;display:flex;align-items:center;gap:8px;">'
        f'<span style="font-size:18px;">{icon}</span>'
        f'<span style="color:{Colors.TEXT_MAIN};font-size:15px;font-weight:700;">{title}</span>'
        f'</div>'
        f'{rows_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def change_ranking_list(
    df_change: pd.DataFrame,
    title: str,
    name_col: str = "센터명",
    change_col: str = "변화량",
    current_col: str = "총점",
    n: int = 5,
    ascending: bool = False,
    icon: str = "📈",
):
    """전월 대비 변화량 랭킹"""
    if df_change is None or df_change.empty or change_col not in df_change.columns:
        st.info(f"{title}: 비교할 전월 데이터가 없습니다.")
        return

    df_sorted = (
        df_change.dropna(subset=[change_col])
        .sort_values(change_col, ascending=ascending)
        .head(n)
    )

    if df_sorted.empty:
        st.info(f"{title}: 표시할 데이터가 없습니다.")
        return

    rows_html = ""
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        name = str(row[name_col])
        change = row[change_col]
        current = row[current_col] if current_col in df_sorted.columns else None

        change_color = Colors.SUCCESS if change >= 0 else Colors.DANGER
        change_sign = "+" if change >= 0 else ""
        change_arrow = "▲" if change >= 0 else "▼"

        current_html = ""
        if current is not None and pd.notna(current):
            current_html = (
                f'<span style="color:{Colors.TEXT_SUB};font-size:12px;margin-left:6px;">'
                f'(현재 {current:,.1f}점)</span>'
            )

        badge = _rank_badge_html(i)
        rank_html = f'<span style="width:30px;text-align:center;display:inline-block;">{badge}</span>'

        # ⚠️ 한 줄로 압축
        rows_html += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 12px;border-bottom:1px solid {Colors.BG_GRAY};">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'{rank_html}'
            f'<span><span style="color:{Colors.TEXT_MAIN};font-size:14px;font-weight:500;">{name}</span>'
            f'{current_html}</span>'
            f'</div>'
            f'<span style="color:{change_color};font-size:15px;font-weight:700;">'
            f'{change_arrow} {change_sign}{change:,.1f}</span>'
            f'</div>'
        )

    html = (
        f'<div style="background:{Colors.BG_CARD};border:1px solid {Colors.BORDER};'
        f'border-radius:12px;padding:16px 8px 8px 8px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<div style="padding:0 12px 12px 12px;border-bottom:2px solid {Colors.PRIMARY};'
        f'margin-bottom:4px;display:flex;align-items:center;gap:8px;">'
        f'<span style="font-size:18px;">{icon}</span>'
        f'<span style="color:{Colors.TEXT_MAIN};font-size:15px;font-weight:700;">{title}</span>'
        f'</div>'
        f'{rows_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
