"""
점수 차트 컴포넌트
- 센터별 막대 차트
- 점수 게이지
- 레이더 차트
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.styles import (
    Colors, 
    ScoreThresholds, 
    get_score_color,
    PLOTLY_LAYOUT
)


def create_center_ranking_bar(df_sorted: pd.DataFrame, 
                                show_predicted: bool = True,
                                height: int = 600) -> go.Figure:
    """
    센터별 점수 막대 차트 (랭킹용)
    
    Args:
        df_sorted: '센터명', '총점' 컬럼 필수. '예측점수' 컬럼 있으면 함께 표시
        show_predicted: 예측 점수 마커 표시 여부
        height: 차트 높이
    """
    has_predicted = '예측점수' in df_sorted.columns and show_predicted
    
    # 색상: 예측점수 기준 (없으면 현재 점수 기준)
    score_col = '예측점수' if has_predicted else '총점'
    colors = [get_score_color(s) for s in df_sorted[score_col]]
    
    fig = go.Figure()
    
    # 현재 점수 막대
    fig.add_trace(go.Bar(
        y=df_sorted['센터명'],
        x=df_sorted['총점'],
        orientation='h',
        marker=dict(color=colors, opacity=0.65),
        name='현재 점수',
        text=df_sorted['총점'].round(1),
        textposition='inside',
        textfont=dict(color='white', size=11),
        hovertemplate='<b>%{y}</b><br>현재: %{x:.1f}점<extra></extra>'
    ))
    
    # 예측 점수 마커
    if has_predicted:
        fig.add_trace(go.Scatter(
            y=df_sorted['센터명'],
            x=df_sorted['예측점수'],
            mode='markers',
            marker=dict(
                size=14,
                color=colors,
                symbol='diamond',
                line=dict(width=2, color='white')
            ),
            name='예측 점수',
            hovertemplate='<b>%{y}</b><br>예측: %{x:.1f}점<extra></extra>'
        ))
    
    # 목표선
    fig.add_vline(
        x=ScoreThresholds.TARGET,
        line_dash="dash",
        line_color=Colors.WARNING,
        line_width=2,
        annotation_text=f"목표: {ScoreThresholds.TARGET}점",
        annotation_position="top right"
    )
    
    # 만점선
    fig.add_vline(
        x=ScoreThresholds.PERFECT,
        line_dash="dot",
        line_color=Colors.DANGER,
        line_width=1,
        annotation_text=f"만점: {ScoreThresholds.PERFECT}점",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        xaxis_title="점수",
        yaxis_title="",
        height=height,
        showlegend=True,
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(range=[0, 1050]),
        **PLOTLY_LAYOUT,
    )
    
    return fig


def create_kpi_radar_chart(scores: dict, center_name: str = "") -> go.Figure:
    """
    KPI 레이더 차트 (센터별 상세용)
    
    Args:
        scores: {'안전점검': 점수, '중점고객': 점수, ...} 형태
        center_name: 센터명
    """
    # 최대 점수 매핑
    max_scores = {
        '안전점검': 550,
        '중점고객': 100,
        '사용계약': 50,
        '상담응대': 100,
        '상담기여': 100,
        '만족도': 100,
    }
    
    categories = list(scores.keys())
    normalized = [scores[c] / max_scores.get(c, 100) * 100 for c in categories]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized,
        theta=categories,
        fill='toself',
        name=center_name,
        line_color=Colors.PRIMARY,
        fillcolor=f"{Colors.PRIMARY}33",
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color=Colors.TEXT_SUB),
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=Colors.TEXT_MAIN),
            ),
        ),
        showlegend=True,
        height=450,
        title=dict(
            text=f"{center_name} 항목별 달성률 (%)",
            font=dict(size=15, color=Colors.TEXT_MAIN),
        ),
        **PLOTLY_LAYOUT,
    )
    
    return fig


def create_score_gauge(score: float, target: float = 911, 
                        title: str = "총점") -> go.Figure:
    """
    점수 게이지 차트 (단일 점수 표시)
    
    Args:
        score: 점수
        target: 목표 점수
        title: 게이지 제목
    """
    color = get_score_color(score)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': Colors.TEXT_MAIN}},
        delta={'reference': target, 'increasing': {'color': Colors.SUCCESS},
               'decreasing': {'color': Colors.DANGER}},
        gauge={
            'axis': {'range': [0, 1000], 'tickwidth': 1, 'tickcolor': Colors.TEXT_SUB},
            'bar': {'color': color},
            'bgcolor': Colors.BG_GRAY,
            'borderwidth': 2,
            'bordercolor': Colors.BORDER,
            'steps': [
                {'range': [0, 850], 'color': f"{Colors.DANGER}22"},
                {'range': [850, 880], 'color': f"{Colors.ALERT}22"},
                {'range': [880, 910], 'color': f"{Colors.WARNING}22"},
                {'range': [910, 1000], 'color': f"{Colors.SUCCESS}22"},
            ],
            'threshold': {
                'line': {'color': Colors.WARNING, 'width': 3},
                'thickness': 0.8,
                'value': target,
            },
        },
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        **PLOTLY_LAYOUT,
    )
    
    return fig


def create_monthly_trend_line(df: pd.DataFrame, 
                                y_col: str = '총점',
                                title: str = "월별 추이") -> go.Figure:
    """
    월별 추이 라인 차트
    
    Args:
        df: '센터명', '평가월', y_col 컬럼 필수
        y_col: Y축에 표시할 컬럼명
        title: 차트 제목
    """
    fig = px.line(
        df,
        x='평가월',
        y=y_col,
        color='센터명',
        markers=True,
        title=title,
        labels={y_col: f'{y_col} (점)', '평가월': '평가월'},
    )
    
    # 목표선 (총점일 때만)
    if y_col == '총점':
        fig.add_hline(
            y=ScoreThresholds.TARGET,
            line_dash="dash",
            line_color=Colors.WARNING,
            line_width=2,
            annotation_text=f"목표: {ScoreThresholds.TARGET}점",
            annotation_position="right"
        )
    
    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        ),
        **PLOTLY_LAYOUT,
    )
    
    return fig
