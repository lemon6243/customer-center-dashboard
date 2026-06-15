"""
홈 화면용 랭킹 리스트 컴포넌트
- Top 5 / Bottom 5 센터 표시
- 점수 순 / 상승·하락 폭 순 토글 가능
"""
import streamlit as st
import pandas as pd
from utils.styles import Colors, get_score_color


def ranking_list(
    df: pd.DataFrame,
    title: str,
    value_col: str = "총점",
    name_col: str = "센터명",
    n: int = 5,
    ascending: bool = False,  # False=Top, True=Bottom
    icon: str = "🏆",
    show_rank: bool = True,
    value_format: str = "{:,.1f}점",
    use_score_color: bool = True,
):
    """
    랭킹 리스트 표시
    
    Args:
        df: 데이터프레임
        title: 카드 제목
        value_col: 정렬·표시할 값 컬럼
        name_col: 센터명 컬럼
        n: 표시할 개수
        ascending: True면 하위 N개(낮은 순), False면 상위 N개(높은 순)
        icon: 제목 아이콘
        show_rank: 순위 번호 표시 여부
        value_format: 값 포맷 문자열
        use_score_color: True면 총점 기준 색상, False면 단일 색상
    """
    if df is None or df.empty or value_col not in df.columns:
        st.info(f"{title}: 표시할 데이터가 없습니다.")
        return

    df_sorted = df.dropna(subset=[value_col, name_col]).sort_values(value_col, ascending=ascending).head(n)

    if df_sorted.empty:
        st.info(f"{title}: 표시할 데이터가 없습니다.")
        return

    rows_html = ""
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        name = str(row[name_col])
        value = row[value_col]

        # 색상
        if use_score_color and value_col == "총점":
            value_color = get_score_color(value)
        elif ascending:
            value_color = Colors.DANGER
        else:
            value_color = Colors.SUCCESS

        # 순위 배지
        rank_html = ""
        if show_rank:
            if i == 1:
                rank_badge = "🥇"
            elif i == 2:
                rank_badge = "🥈"
            elif i == 3:
                rank_badge = "🥉"
            else:
                rank_badge = f"<span style='display:inline-block; width:22px; height:22px; border-radius:50%; background:{Colors.BG_CARD}; border:1px solid {Colors.BORDER}; text-align:center; font-size:12px; font-weight:600; color:{Colors.TEXT_SUB};'>{i}</span>"
            rank_html = f'<span style="width:30px; text-align:center;">{rank_badge}</span>'

        # 값 포맷
        try:
            value_str = value_format.format(value)
        except Exception:
            value_str = str(value)

        rows_html += f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            padding:10px 12px; border-bottom:1px solid {Colors.BG_GRAY};
        ">
            <div style="display:flex; align-items:center; gap:10px;">
                {rank_html}
                <span style="color:{Colors.TEXT_MAIN}; font-size:14px; font-weight:500;">{name}</span>
            </div>
            <span style="color:{value_color}; font-size:15px; font-weight:700;">{value_str}</span>
        </div>
        """

    html = f"""
    <div style="
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-radius: 12px;
        padding: 16px 8px 8px 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="
            padding: 0 12px 12px 12px;
            border-bottom: 2px solid {Colors.PRIMARY};
            margin-bottom: 4px;
            display:flex; align-items:center; gap:8px;
        ">
            <span style="font-size:18px;">{icon}</span>
            <span style="color:{Colors.TEXT_MAIN}; font-size:15px; font-weight:700;">{title}</span>
        </div>
        {rows_html}
    </div>
    """
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
    """
    전월 대비 변화량 랭킹
    
    Args:
        df_change: '센터명', '변화량', '총점'(현재) 컬럼이 있는 DF
        ascending: False=상승 Top, True=하락 Top
    """
    if df_change is None or df_change.empty or change_col not in df_change.columns:
        st.info(f"{title}: 비교할 전월 데이터가 없습니다.")
        return

    df_sorted = df_change.dropna(subset=[change_col]).sort_values(change_col, ascending=ascending).head(n)

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
            current_html = f'<span style="color:{Colors.TEXT_SUB}; font-size:12px; margin-left:6px;">(현재 {current:,.1f}점)</span>'

        rank_badge = f"<span style='display:inline-block; width:22px; height:22px; border-radius:50%; background:{Colors.BG_CARD}; border:1px solid {Colors.BORDER}; text-align:center; font-size:12px; font-weight:600; color:{Colors.TEXT_SUB};'>{i}</span>"

        rows_html += f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            padding:10px 12px; border-bottom:1px solid {Colors.BG_GRAY};
        ">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="width:30px; text-align:center;">{rank_badge}</span>
                <span>
                    <span style="color:{Colors.TEXT_MAIN}; font-size:14px; font-weight:500;">{name}</span>
                    {current_html}
                </span>
            </div>
            <span style="color:{change_color}; font-size:15px; font-weight:700;">
                {change_arrow} {change_sign}{change:,.1f}
            </span>
        </div>
        """

    html = f"""
    <div style="
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-radius: 12px;
        padding: 16px 8px 8px 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="
            padding: 0 12px 12px 12px;
            border-bottom: 2px solid {Colors.PRIMARY};
            margin-bottom: 4px;
            display:flex; align-items:center; gap:8px;
        ">
            <span style="font-size:18px;">{icon}</span>
            <span style="color:{Colors.TEXT_MAIN}; font-size:15px; font-weight:700;">{title}</span>
        </div>
        {rows_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
