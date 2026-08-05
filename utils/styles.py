"""
디자인 시스템 - 색상, CSS, 스타일 상수
모든 페이지에서 공통으로 사용
"""

import streamlit as st


# ==================== 색상 팔레트 ====================

class Colors:
    """YESCO 업무 대시보드 공통 색상"""

    PRIMARY = "#0B4EA2"
    PRIMARY_DARK = "#073A7A"
    PRIMARY_LIGHT = "#EAF3FF"
    PRIMARY_SOFT = "#F4F8FC"

    SUCCESS = "#178A5B"
    SUCCESS_LIGHT = "#EAF7F1"
    WARNING = "#D48A00"
    WARNING_LIGHT = "#FFF6E5"
    ALERT = "#E66A1F"
    DANGER = "#D92D20"
    DANGER_LIGHT = "#FFF0EE"

    CURRENT = "#0B4EA2"
    PREDICTED = "#4E7FB8"
    REFERENCE = "#7B8794"

    BG_WHITE = "#FFFFFF"
    BG_GRAY = "#F5F7FA"
    BG_CARD = "#FFFFFF"
    TEXT_MAIN = "#172B4D"
    TEXT_SUB = "#5E6C84"
    TEXT_LIGHT = "#8993A4"
    BORDER = "#DCE3EA"

    GRADIENT_PRIMARY = "linear-gradient(135deg, #0B4EA2 0%, #1769C2 100%)"
    GRADIENT_SUCCESS = "linear-gradient(135deg, #178A5B 0%, #0F6D46 100%)"


# ==================== 점수 구간 ====================

class ScoreThresholds:
    """평가 점수 기준값"""

    TARGET = 911
    PERFECT = 1000

    SUCCESS_MIN = 911
    WARNING_MIN = 881
    ALERT_MIN = 851


def get_score_color(score: float) -> str:
    """점수에 해당하는 색상 반환"""
    if score >= ScoreThresholds.SUCCESS_MIN:
        return Colors.SUCCESS
    if score >= ScoreThresholds.WARNING_MIN:
        return Colors.WARNING
    if score >= ScoreThresholds.ALERT_MIN:
        return Colors.ALERT
    return Colors.DANGER


def get_score_grade(score: float) -> tuple:
    """점수 → (등급명, 색상, 이모지) 반환"""
    if score >= ScoreThresholds.SUCCESS_MIN:
        return ("달성", Colors.SUCCESS, "🟢")
    if score >= ScoreThresholds.WARNING_MIN:
        return ("주의", Colors.WARNING, "🟡")
    if score >= ScoreThresholds.ALERT_MIN:
        return ("경고", Colors.ALERT, "🟠")
    return ("위험", Colors.DANGER, "🔴")


# ==================== 전역 CSS ====================

GLOBAL_CSS = f"""
<style>
    .main-header {{
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1.0rem 1.5rem;
        background: {Colors.GRADIENT_PRIMARY};
        color: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(11, 78, 162, 0.15);
        letter-spacing: -0.5px;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            {Colors.BG_GRAY} 0%,
            {Colors.BG_WHITE} 100%
        );
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{
        color: {Colors.PRIMARY};
        font-weight: 700;
        font-size: 1.3rem;
        margin-top: 0.8rem;
    }}

    /* 사이드바 메뉴 크기·스타일 통일 */
    [data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 6px !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label {{
        width: 100% !important;
        min-height: 46px !important;
        margin: 0 !important;
        padding: 0 14px !important;
        border: 1px solid {Colors.BORDER} !important;
        border-radius: 8px !important;
        background: {Colors.BG_WHITE} !important;
        color: {Colors.TEXT_MAIN} !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        transition: background 0.15s ease, border-color 0.15s ease !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        border-color: {Colors.PRIMARY} !important;
        background: {Colors.PRIMARY_SOFT} !important;
        transform: none !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background: {Colors.PRIMARY} !important;
        border-color: {Colors.PRIMARY} !important;
        color: white !important;
        box-shadow: none !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label input {{
        position: absolute !important;
        opacity: 0 !important;
    }}

        /* 사이드바 기본 라디오 원형 숨김 */
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {{
        display: none !important;
    }}

    [data-testid="stSidebar"] [data-baseweb="radio"] {{
        padding-left: 0 !important;
        margin: 0 !important;
    }}

    [data-testid="stSidebar"] [data-baseweb="radio"] > div:last-child {{
        margin-left: 0 !important;
    }}


    .stAlert {{
        margin-top: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid {Colors.PRIMARY};
    }}

    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: {Colors.PRIMARY};
    }}

    [data-testid="stMetricLabel"] {{
        font-size: 1rem;
        font-weight: 600;
        color: {Colors.TEXT_SUB};
    }}

    [data-testid="stMetricDelta"] {{
        font-size: 0.9rem;
    }}

    .stButton > button {{
        background: {Colors.GRADIENT_PRIMARY};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(11, 78, 162, 0.2);
    }}

    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(11, 78, 162, 0.3);
    }}

    .stDownloadButton > button {{
        background: {Colors.GRADIENT_SUCCESS};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 15px;
    }}

    .custom-card {{
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
    }}

    .custom-card:hover {{
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }}

    .card-title {{
        font-size: 0.9rem;
        font-weight: 600;
        color: {Colors.TEXT_SUB};
        margin-bottom: 0.5rem;
    }}

    .card-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {Colors.TEXT_MAIN};
    }}

    /* 핵심지표 카드 공통 규격 */
    .yesco-metric-card {{
        min-height: 158px;
        height: 158px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(23, 43, 77, 0.05);
    }}

    .yesco-metric-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        min-height: 22px;
    }}

    .yesco-metric-label {{
        color: {Colors.TEXT_SUB};
        font-size: 13px;
        font-weight: 600;
        line-height: 1.3;
    }}

    .yesco-metric-value {{
        color: {Colors.TEXT_MAIN};
        font-size: 31px;
        font-weight: 750;
        line-height: 1.15;
        letter-spacing: -0.8px;
        white-space: nowrap;
    }}

    .yesco-metric-footer {{
        min-height: 22px;
        margin-top: 8px;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.45;
    }}


    @media (max-width: 768px) {{
        .main-header {{
            font-size: 1.6rem;
            padding: 1rem;
        }}

        .yesco-metric-card {{
            min-height: 142px;
            height: 142px;
            padding: 16px;
        }}

        .yesco-metric-value {{
            font-size: 27px;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 1.5rem;
        }}

        .card-value {{
            font-size: 1.4rem;
        }}
    }}

    @media (max-width: 480px) {{
        .main-header {{
            font-size: 1.3rem;
            padding: 0.8rem;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 1.2rem;
        }}
    }}
</style>
"""


def apply_global_styles():
    """전역 CSS 적용"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ==================== Plotly 공통 설정 ====================

PLOTLY_LAYOUT = {
    "font": {"family": "'Pretendard', sans-serif", "color": Colors.TEXT_MAIN},
    "plot_bgcolor": Colors.BG_WHITE,
    "paper_bgcolor": Colors.BG_WHITE,
    "colorway": [
        Colors.PRIMARY,
        Colors.PREDICTED,
        Colors.SUCCESS,
        Colors.WARNING,
        Colors.ALERT,
        Colors.DANGER,
    ],
}


HEATMAP_COLORSCALE = [
    [0.00, Colors.DANGER],
    [0.55, Colors.ALERT],
    [0.70, Colors.WARNING],
    [0.85, "#84CC16"],
    [1.00, Colors.SUCCESS],
]
