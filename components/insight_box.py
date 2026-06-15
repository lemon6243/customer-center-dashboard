"""
인사이트 박스 컴포넌트
- 자동 인사이트 텍스트 생성 (Phase 3에서 본격 활용)
- 액션 가이드 박스
"""

import streamlit as st
import pandas as pd
from utils.styles import Colors


def insight_text(content: str, icon: str = "💡", color: str = None):
    """
    심플한 인사이트 텍스트 박스
    
    Args:
        content: 표시할 텍스트 (HTML 가능)
        icon: 아이콘
        color: 강조 색상
    """
    if color is None:
        color = Colors.PRIMARY
    
    st.markdown(f"""
    <div style="
        background-color: {color}0d;
        border: 1px solid {color}33;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: {Colors.TEXT_MAIN};
        font-size: 0.95rem;
        line-height: 1.6;
    ">
        <span style="color: {color}; font-weight: 600;">{icon}</span> {content}
    </div>
    """, unsafe_allow_html=True)


def action_guide(title: str, items: list, color: str = None):
    """
    액션 가이드 박스 (할 일 리스트)
    
    Args:
        title: 박스 제목
        items: 액션 아이템 리스트 (문자열)
        color: 강조 색상
    """
    if color is None:
        color = Colors.PRIMARY
    
    items_html = "".join([
        f'<li style="margin-bottom: 0.4rem;">{item}</li>' 
        for item in items
    ])
    
    st.markdown(f"""
    <div style="
        background-color: {Colors.BG_GRAY};
        border-left: 4px solid {color};
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    ">
        <div style="
            font-weight: 700;
            color: {color};
            font-size: 1rem;
            margin-bottom: 0.6rem;
        ">🎯 {title}</div>
        <ul style="
            margin: 0;
            padding-left: 1.2rem;
            color: {Colors.TEXT_MAIN};
            font-size: 0.95rem;
            line-height: 1.6;
        ">
            {items_html}
        </ul>
    </div>
    """, unsafe_allow_html=True)


def auto_insight_summary(df_latest: pd.DataFrame) -> list:
    """
    자동 인사이트 텍스트 리스트 생성 (Phase 3에서 확장)
    
    현재는 기본 통계 기반 간단 인사이트만 제공.
    
    Args:
        df_latest: 최신 월 데이터프레임 ('센터명', '총점' 필수)
    
    Returns:
        인사이트 문자열 리스트
    """
    insights = []
    
    if df_latest is None or df_latest.empty:
        return insights
    
    try:
        # 최고/최저
        top = df_latest.nlargest(1, '총점').iloc[0]
        bottom = df_latest.nsmallest(1, '총점').iloc[0]
        
        insights.append(
            f"🏆 <b>최고 성과</b>: {top['센터명']} ({top['총점']:.1f}점)"
        )
        insights.append(
            f"⚠️ <b>최저 성과</b>: {bottom['센터명']} ({bottom['총점']:.1f}점)"
        )
        
        # 평균
        avg = df_latest['총점'].mean()
        target = 911
        gap = avg - target
        if gap >= 0:
            insights.append(
                f"📊 <b>전체 평균</b>: {avg:.1f}점 (목표 +{gap:.1f}점 ✅)"
            )
        else:
            insights.append(
                f"📊 <b>전체 평균</b>: {avg:.1f}점 (목표 {gap:.1f}점 미달)"
            )
        
        # 달성 비율
        if '목표달성여부' in df_latest.columns:
            achieved = df_latest['목표달성여부'].sum()
            total = len(df_latest)
            rate = achieved / total * 100 if total > 0 else 0
            insights.append(
                f"🎯 <b>목표 달성</b>: {achieved}/{total}개 센터 ({rate:.1f}%)"
            )
    
    except Exception as e:
        insights.append(f"⚠️ 인사이트 생성 중 오류: {e}")
    
    return insights
