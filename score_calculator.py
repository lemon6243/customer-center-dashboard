import pandas as pd
import numpy as np
from typing import Dict, List

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    누적 비율 기반 점수 계산
    
    핵심: 각 월의 "누적 비율"로 점수 계산
    예: 3월 = 1~3월 누적 실적
    """
    result_df = df.copy()
    
    # 1. 안전점검실점검율 (550점)
    result_df['안전점검_점수'] = (result_df['안전점검실점검율'] * 550).round(2)
    
    # 2. 중점고객안전점검율 (100점)
    result_df['중점고객_점수'] = (result_df['중점고객안전점검율'] * 100).round(2)
    
    # 3. 사용계약율 (등급제, 50점)
    def calculate_contract_score(rate):
        if pd.isna(rate):
            return 0
        if rate >= 0.90:
            return 50
        elif rate >= 0.80:
            return 45
        elif rate >= 0.70:
            return 40
        else:
            return 35
    
    result_df['사용계약_점수'] = result_df['사용계약율'].apply(calculate_contract_score)
    
    # 4. 상담응대율 (100점)
    result_df['상담응대_점수'] = (result_df['상담응대율'] * 100).round(2)
    
    # 5. 상담기여도 (100점)
    result_df['상담기여_점수'] = (result_df['상담기여도'] * 100).round(2)
    
    # 6. 고객서비스만족도 (100점)
    result_df['만족도_점수'] = result_df['고객서비스만족도'].fillna(0).round(2)
    
    # 총점 계산
    result_df['총점'] = (
        result_df['안전점검_점수'] +
        result_df['중점고객_점수'] +
        result_df['사용계약_점수'] +
        result_df['상담응대_점수'] +
        result_df['상담기여_점수'] +
        result_df['만족도_점수'] +
        result_df['민원대응적정성'] +
        result_df['주의경고'] +
        result_df['가점']
    ).round(2)
    
    # 목표 달성 여부 (911점)
    result_df['목표달성여부'] = result_df['총점'] >= 911
    result_df['목표대비'] = (result_df['총점'] - 911).round(2)
    
    # 각 지표의 달성률 (백분율)
    result_df['안전점검_달성률'] = (result_df['안전점검_점수'] / 550 * 100).round(1)
    result_df['중점고객_달성률'] = (result_df['중점고객_점수'] / 100 * 100).round(1)
    result_df['사용계약_달성률'] = (result_df['사용계약_점수'] / 50 * 100).round(1)
    result_df['상담응대_달성률'] = (result_df['상담응대_점수'] / 100 * 100).round(1)
    result_df['상담기여_달성률'] = (result_df['상담기여_점수'] / 100 * 100).round(1)
    result_df['만족도_달성률'] = (result_df['만족도_점수'] / 100 * 100).round(1)
    
    return result_df


def get_final_period_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    반기별 최종 점수 추출
    
    상반기: 6월 점수 = 1~6월 누적 최종
    하반기: 12월 점수 = 7~12월 누적 최종
    
    현재까지 데이터만 있으면 현재까지의 최종
    """
    # 반기별 마지막 월 데이터만 추출
    final_scores = df.loc[df.groupby(['센터명', '반기'])['평가월'].idxmax()]
    
    result = final_scores[[
        '센터명', '반기', '평가월', '월', '총점', 
        '목표달성여부', '목표대비',
        '안전점검_점수', '중점고객_점수', '사용계약_점수',
        '상담응대_점수', '상담기여_점수', '만족도_점수'
    ]].copy()
    
    result = result.sort_values(['반기', '총점'], ascending=[True, False])
    
    return result


def calculate_annual_evaluation(df: pd.DataFrame) -> pd.DataFrame:
    """
    연간 평가 (상반기 + 하반기 평균)
    
    재계약 기준: (상반기 최종 + 하반기 최종) / 2 >= 911
    """
    final_scores = get_final_period_score(df)
    
    # 반기별 피벗
    pivot = final_scores.pivot(
        index='센터명', 
        columns='반기', 
        values='총점'
    ).reset_index()
    
    # 연간 평균 계산
    if '상반기' in pivot.columns and '하반기' in pivot.columns:
        pivot['연간평균'] = ((pivot['상반기'] + pivot['하반기']) / 2).round(2)
        pivot['상반기'] = pivot['상반기'].round(2)
        pivot['하반기'] = pivot['하반기'].round(2)
    elif '상반기' in pivot.columns:
        pivot['연간평균'] = pivot['상반기'].round(2)
        pivot['하반기'] = None
    elif '하반기' in pivot.columns:
        pivot['연간평균'] = pivot['하반기'].round(2)
        pivot['상반기'] = None
    else:
        pivot['연간평균'] = 0
        pivot['상반기'] = None
        pivot['하반기'] = None
    
    pivot['재계약가능'] = pivot['연간평균'] >= 911
    pivot['목표대비'] = (pivot['연간평균'] - 911).round(2)
    
    # 정렬
    pivot = pivot.sort_values('연간평균', ascending=False)
    
    return pivot


def get_summary_stats(df: pd.DataFrame) -> Dict:
    """
    전체 통계 요약 (최신 월 기준)
    """
    # 각 센터의 최신 월 데이터만
    latest_data = df.loc[df.groupby('센터명')['평가월'].idxmax()]
    
    return {
        'total_centers': latest_data['센터명'].nunique(),
        'avg_score': round(latest_data['총점'].mean(), 2),
        'max_score': round(latest_data['총점'].max(), 2),
        'min_score': round(latest_data['총점'].min(), 2),
        'passed_centers': int(latest_data['목표달성여부'].sum()),
        'failed_centers': int((~latest_data['목표달성여부']).sum()),
        'pass_rate': round(latest_data['목표달성여부'].mean() * 100, 1),
        'at_risk_centers': latest_data[~latest_data['목표달성여부']]['센터명'].tolist(),
        'top_centers': latest_data.nlargest(3, '총점')[['센터명', '총점']].to_dict('records'),
        'bottom_centers': latest_data.nsmallest(3, '총점')[['센터명', '총점']].to_dict('records')
    }


def predict_period_achievement(df: pd.DataFrame, target: float = 911) -> Dict:
    """
    반기 목표 달성 예측
    
    현재까지의 누적 추세로 최종 점수 예측
    """
    predictions = {}
    
    for center in df['센터명'].unique():
        center_data = df[df['센터명'] == center].sort_values('평가월')
        
        if len(center_data) == 0:
            continue
        
        # 현재 반기
        current_period = center_data['반기'].iloc[-1]
        period_data = center_data[center_data['반기'] == current_period]
        
        # 현재까지 최신 점수
        current_score = period_data['총점'].iloc[-1]
        
        # 누적 개월
        months_data = len(period_data)
        total_months = 6
        remaining_months = total_months - months_data
        
        # 간단한 예측: 현재 점수가 최종 점수 (이미 누적이므로)
        predicted_final = current_score
        
        # 목표 대비
        gap = predicted_final - target
        
        if gap >= 0:
            status = "달성 예상 ✅"
            risk_level = "안전"
        elif gap >= -20:
            status = "주의 필요 ⚠️"
            risk_level = "주의"
        else:
            status = "위험 🚨"
            risk_level = "위험"
        
        predictions[center] = {
            'current_score': round(current_score, 2),
            'predicted_final': round(predicted_final, 2),
            'months_data': months_data,
            'remaining_months': remaining_months,
            'gap': round(gap, 2),
            'status': status,
            'risk_level': risk_level,
            'period': current_period
        }
    
    return predictions


def get_weak_kpis(row: pd.Series, threshold: float = 85.0) -> List[str]:
    """
    취약 지표 식별 (달성률 threshold% 미만)
    """
    weak_kpis = []
    
    kpi_dict = {
        '안전점검실점검율': row.get('안전점검_달성률', 0),
        '중점고객안전점검율': row.get('중점고객_달성률', 0),
        '사용계약율': row.get('사용계약_달성률', 0),
        '상담응대율': row.get('상담응대_달성률', 0),
        '상담기여도': row.get('상담기여_달성률', 0),
        '고객서비스만족도': row.get('만족도_달성률', 0)
    }
    
    for kpi_name, achievement_rate in kpi_dict.items():
        if achievement_rate < threshold:
            weak_kpis.append(f"{kpi_name} ({achievement_rate:.1f}%)")
    
    return weak_kpis
