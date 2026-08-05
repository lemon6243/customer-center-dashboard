"""
디자인 시스템 - 색상, CSS, 스타일 상수
모든 페이지에서 공통으로 사용
"""

import streamlit as st


# ==================== 색상 팔레트 ====================

class Colors:
    """YESCO 업무 대시보드 공통 색상"""

    # 브랜드 기반 기본색
    PRIMARY = "#0B4EA2"          # 신뢰감 있는 블루
    PRIMARY_DARK = "#073A7A"
    PRIMARY_LIGHT = "#EAF3FF"
    PRIMARY_SOFT = "#F4F8FC"

    # 의미색
    SUCCESS = "#178A5B"          # 안전/달성
    SUCCESS_LIGHT = "#EAF7F1"
    WARNING = "#D48A00"          # 주의
    WARNING_LIGHT = "#FFF6E5"
    ALERT = "#E66A1F"
    DANGER = "#D92D20"           # 위험
    DANGER_LIGHT = "#FFF0EE"

    # 데이터 시각화
    CURRENT = "#0B4EA2"
    PREDICTED = "#4E7FB8"
    REFERENCE = "#7B8794"

    # 배경/텍스트
    BG_WHITE = "#FFFFFF"
    BG_GRAY = "#F5F7FA"
    BG_CARD = "#FFFFFF"
    TEXT_MAIN = "#172B4D"
    TEXT_SUB = "#5E6C84"
    TEXT_LIGHT = "#8993A4"
    BORDER = "#DCE3EA"

    # 그라데이션
    GRADIENT_PRIMARY = "linear-gradient(135deg, #0B4EA2 0%, #1769C2 100%)"
    GRADIENT_SUCCESS = "linear-gradient(135deg, #178A5B 0%, #0F6D46 100%)"


# ==================== 점수 구간 ====================

class ScoreThresholds:
    """평가 점수 기준값"""
    TARGET = 911                  # 목표 점수
    PERFECT = 1000                # 만점
    
    # 위험도 구간 (현재 점수 기준)
    SUCCESS_MIN = 911             # 달성
    WARNING_MIN = 881             # 주의
    ALERT_MIN = 851               # 경고
    # DANGER: 850 이하


def get_score_color(score: float) -> str:
    """점수에 해당하는 색상 반환"""
    if score >= ScoreThresholds.SUCCESS_MIN:
        return Colors.SUCCESS
    elif score >= ScoreThresholds.WARNING_MIN:
        return Colors.WARNING
    elif score >= ScoreThresholds.ALERT_MIN:
        return Colors.ALERT
    else:
        return Colors.DANGER


def get_score_grade(score: float) -> tuple:
    """점수 → (등급명, 색상, 이모지) 반환"""
    if score >= ScoreThresholds.SUCCESS_MIN:
        return ("달성", Colors.SUCCESS, "🟢")
    elif score >= ScoreThresholds.WARNING_MIN:
        return ("주의", Colors.WARNING, "🟡")
    elif score >= ScoreThresholds.ALERT_MIN:
        return ("경고", Colors.ALERT, "🟠")
    else:
        return ("위험", Colors.DANGER, "🔴")


# ==================== 전역 CSS ====================

GLOBAL_CSS = f"""
<style>
    /* ========== 메인 헤더 ========== */
    .main-header {{
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        background: {Colors.GRADIENT_PRIMARY};
        color: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
        letter-spacing: -0.5px;
    }}
    
    /* ========== 사이드바 네비게이션 ========== */
    div.row-widget.stRadio > div {{
        flex-direction: column;
        gap: 8px;
    }}
    
    div.row-widget.stRadio > div > label {{
        background-color: {Colors.BG_WHITE};
        padding: 14px 18px;
        border-radius: 10px;
        border: 2px solid {Colors.BORDER};
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 600;
        font-size: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    
    div.row-widget.stRadio > div > label:hover {{
        border-color: {Colors.PRIMARY};
        background-color: {Colors.PRIMARY_LIGHT};
        transform: translateX(3px);
    }}
    
    div.row-widget.stRadio > div > label[data-checked="true"] {{
        background: {Colors.GRADIENT_PRIMARY};
        color: white !important;
        border-color: {Colors.PRIMARY};
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }}
    
    /* ========== 알림 메시지 ========== */
    .stAlert {{
        margin-top: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid {Colors.PRIMARY};
    }}
    
    /* ========== 메트릭 카드 ========== */
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
    
    /* ========== 사이드바 ========== */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {Colors.BG_GRAY} 0%, {Colors.BG_WHITE} 100%);
    }}
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{
        color: {Colors.PRIMARY};
        font-weight: 700;
        font-size: 1.3rem;
        margin-top: 0.8rem;
    }}
    
    /* ========== 일반 버튼 ========== */
    .stButton > button {{
        background: {Colors.GRADIENT_PRIMARY};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }}
    
    /* ========== 다운로드 버튼 ========== */
    .stDownloadButton > button {{
        background: {Colors.GRADIENT_SUCCESS};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 15px;
        box-shadow: 0 2px 6px rgba(22, 163, 74, 0.2);
    }}
    
    .stDownloadButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);
    }}
    
    /* ========== 카드 컴포넌트 ========== */
    .custom-card {{
        background: {Colors.BG_CARD};
        border: 1px solid {Colors.BORDER};
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }}
    
    .custom-card:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
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
    
    /* ========== 위험도 박스 ========== */
    .risk-box {{
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    
    /* ========== 모바일 반응형 ========== */
    @media (max-width: 768px) {{
        .main-header {{
            font-size: 1.6rem;
            padding: 1rem;
        }}
        
        div.row-widget.stRadio > div > label {{
            padding: 12px 14px;
            font-size: 14px;
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

        /* ========== YESCO 사이드바 메뉴 통일 ========== */
    [data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 6px !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label {{
        width: 100% !important;
        min-height: 46px !important;
        margin: 0 !important;
        padding: 0 14px !important;
        border: 1px solid #DCE3EA !important;
        border-radius: 8px !important;
        background: #FFFFFF !important;
        color: #172B4D !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        border-color: #0B4EA2 !important;
        background: #F4F8FC !important;
    }}

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background: #0B4EA2 !important;
        border-color: #0B4EA2 !important;
        color: #FFFFFF !important;
    }}

    /* ========== 핵심지표 카드 공통 규격 ========== */
    .yesco-metric-card {{
        min-height: 158px;
        height: 158px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid #DCE3EA;
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
        color: #5E6C84;
        font-size: 13px;
        font-weight: 600;
    }}

    .yesco-metric-value {{
        color: #172B4D;
        font-size: 31px;
        font-weight: 750;
        line-height: 1.15;
        letter-spacing: -0.8px;
        white-space: nowrap;
    }}

    .yesco-metric-footer {{
        min-height: 20px;
        margin-top: 6px;
        font-size: 12px;
        line-height: 1.4;
    }}

    @media (max-width: 768px) {{
        .yesco-metric-card {{
            min-height: 142px;
            height: 142px;
            padding: 16px;
        }}

        .yesco-metric-value {{
            font-size: 27px;
        }}
    }}



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


# Plotly 점수 히트맵용 색상 스케일
HEATMAP_COLORSCALE = [
    [0.00, Colors.DANGER],       # 0%   빨강
    [0.55, Colors.ALERT],        # 55%  주황
    [0.70, Colors.WARNING],      # 70%  노랑
    [0.85, "#84cc16"],           # 85%  연두
    [1.00, Colors.SUCCESS],      # 100% 진초록
]
