"""
디자인 시스템 - 색상, CSS, 스타일 상수
모든 페이지에서 공통으로 사용
"""

import streamlit as st


# ==================== 색상 팔레트 ====================

class Colors:
    """디자인 시스템 색상 (도시가스 신뢰감 파랑 톤)"""
    
    # 주조색 (Primary)
    PRIMARY = "#2563eb"          # 메인 파랑
    PRIMARY_DARK = "#1e40af"     # 진한 파랑 (호버)
    PRIMARY_LIGHT = "#dbeafe"    # 연한 파랑 (배경)
    
    # 의미색 (Semantic) - 점수 구간별
    SUCCESS = "#16a34a"          # 달성/우수 (911점 이상)
    WARNING = "#eab308"          # 주의 (881~910점)
    ALERT = "#f97316"            # 경고 (851~880점)
    DANGER = "#dc2626"           # 위험 (850점 미만)
    
    # 데이터 시각화
    CURRENT = "#2563eb"          # 현재/실측
    PREDICTED = "#7c3aed"        # 예측값
    REFERENCE = "#64748b"        # 비교/기준선
    
    # 배경/텍스트
    BG_WHITE = "#ffffff"
    BG_GRAY = "#f8fafc"
    BG_CARD = "#ffffff"
    TEXT_MAIN = "#1e293b"        # 본문
    TEXT_SUB = "#64748b"         # 보조
    TEXT_LIGHT = "#94a3b8"       # 약한 텍스트
    BORDER = "#e2e8f0"           # 테두리
    
    # 그라데이션
    GRADIENT_PRIMARY = "linear-gradient(135deg, #2563eb 0%, #1e40af 100%)"
    GRADIENT_SUCCESS = "linear-gradient(135deg, #16a34a 0%, #15803d 100%)"


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
</style>
"""


def apply_global_styles():
    """전역 CSS 적용 - app.py 최상단에서 호출"""
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


# Plotly 점수 히트맵용 색상 스케일
HEATMAP_COLORSCALE = [
    [0.00, Colors.DANGER],       # 0%   빨강
    [0.55, Colors.ALERT],        # 55%  주황
    [0.70, Colors.WARNING],      # 70%  노랑
    [0.85, "#84cc16"],           # 85%  연두
    [1.00, Colors.SUCCESS],      # 100% 진초록
]
