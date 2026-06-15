"""
예측 점수 계산 로직
- 반기 진행률 기반 예측
- 캐시 적용으로 성능 개선
"""

import pandas as pd
import streamlit as st
from utils.styles import Colors, ScoreThresholds


def calculate_predicted_score(row: pd.Series, period_month: int) -> dict:
    """
    개선된 예측 점수 계산
    
    Args:
        row: 센터 1개월치 데이터 (pd.Series)
        period_month: 반기 내 진행 월 (1~6)
    
    Returns:
        {'예측총점': float, '안전점검_예측': float, ...}
    """
    try:
        # 6월(반기 마지막)이면 현재값 그대로
        if period_month >= 6:
            return {
                '예측총점': row.get('총점', 0),
                '안전점검_예측': row.get('안전점검_점수', 0),
                '중점고객_예측': row.get('중점고객_점수', 0),
                '사용계약_예측': row.get('사용계약_점수', 0),
                '상담응대_예측': row.get('상담응대_점수', 0),
                '상담기여_예측': row.get('상담기여_점수', 0),
                '만족도_예측': row.get('만족도_점수', 0),
                '조정항목': (
                    row.get('민원대응적정성', 0) 
                    + row.get('주의경고', 0) 
                    + row.get('가점', 0)
                )
            }
        
        progress_rate = period_month / 6
        
        # 누적형 지표 (진행률 기반 예측)
        안전점검_현재 = row.get('안전점검_점수', 0)
        중점고객_현재 = row.get('중점고객_점수', 0)
        사용계약_현재 = row.get('사용계약_점수', 0)
        
        안전점검_예측 = min(안전점검_현재 / progress_rate, 550)
        중점고객_예측 = min(중점고객_현재 / progress_rate, 100)
        사용계약_예측 = min(사용계약_현재 * 1.1, 50)
        
        # 비누적형 지표 (현재값 유지)
        상담응대_예측 = row.get('상담응대_점수', 0)
        상담기여_예측 = row.get('상담기여_점수', 0)
        만족도_예측 = row.get('만족도_점수', 0)
        
        # 조정 항목
        조정항목 = (
            row.get('민원대응적정성', 0) 
            + row.get('주의경고', 0) 
            + row.get('가점', 0)
        )
        
        예측총점 = (
            안전점검_예측 + 중점고객_예측 + 사용계약_예측 
            + 상담응대_예측 + 상담기여_예측 + 만족도_예측 
            + 조정항목
        )
        
        예측총점 = min(예측총점, ScoreThresholds.PERFECT)
        
        return {
            '예측총점': 예측총점,
            '안전점검_예측': 안전점검_예측,
            '중점고객_예측': 중점고객_예측,
            '사용계약_예측': 사용계약_예측,
            '상담응대_예측': 상담응대_예측,
            '상담기여_예측': 상담기여_예측,
            '만족도_예측': 만족도_예측,
            '조정항목': 조정항목
        }
    except Exception as e:
        st.error(f"❌ 예측 점수 계산 오류: {e}")
        return {
            '예측총점': 0,
            '안전점검_예측': 0,
            '중점고객_예측': 0,
            '사용계약_예측': 0,
            '상담응대_예측': 0,
            '상담기여_예측': 0,
            '만족도_예측': 0,
            '조정항목': 0
        }


def add_predictions_to_df(df: pd.DataFrame, period_month: int) -> pd.DataFrame:
    """
    데이터프레임에 예측 점수 컬럼들을 추가
    
    Args:
        df: 최신 월 데이터프레임
        period_month: 반기 내 진행 월
    
    Returns:
        예측 컬럼이 추가된 데이터프레임
    """
    df = df.copy()
    
    predictions = df.apply(
        lambda row: calculate_predicted_score(row, period_month),
        axis=1
    )
    
    df['예측점수'] = predictions.apply(lambda x: x['예측총점'])
    df['안전점검_예측'] = predictions.apply(lambda x: x['안전점검_예측'])
    df['중점고객_예측'] = predictions.apply(lambda x: x['중점고객_예측'])
    df['사용계약_예측'] = predictions.apply(lambda x: x['사용계약_예측'])
    df['상담응대_예측'] = predictions.apply(lambda x: x['상담응대_예측'])
    df['상담기여_예측'] = predictions.apply(lambda x: x['상담기여_예측'])
    df['만족도_예측'] = predictions.apply(lambda x: x['만족도_예측'])
    
    return df


def get_risk_level(predicted_score: float, period_month: int) -> tuple:
    """
    예측 점수 기반 위험도 판정
    
    Returns:
        (위험도명, 색상, 이모지)
    """
    gap = predicted_score - ScoreThresholds.TARGET
    
    if period_month >= 6:
        # 6월: 최종 평가 기준
        if gap >= 0:
            return ("안전", Colors.SUCCESS, "🟢")
        elif gap >= -30:
            return ("주의", Colors.WARNING, "🟡")
        elif gap >= -60:
            return ("경고", Colors.ALERT, "🟠")
        else:
            return ("심각", Colors.DANGER, "🔴")
    else:
        # 진행 중: 여유 구간 더 인정
        if gap >= 50:
            return ("안전", Colors.SUCCESS, "🟢")
        elif gap >= 0:
            return ("양호", Colors.SUCCESS, "🟢")
        elif gap >= -30:
            return ("주의", Colors.WARNING, "🟡")
        elif gap >= -60:
            return ("경고", Colors.ALERT, "🟠")
        else:
            return ("위험", Colors.DANGER, "🔴")
