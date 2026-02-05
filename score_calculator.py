import pandas as pd
import numpy as np
from typing import Dict, List

def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    누적 비율 기반 점수 계산
    
    핵심: 각 월의 "누적 비율"로 점수 계산
    예: 3월 = 1~3월 누적 실적
    
    수정된 사용계약 등급제:
    - A등급 (90% 이상): 50점
    - B등급 (80~90% 미만): 45점
    - C등급 (70~80% 미만): 40점
    - D등급 (70% 미만): 35점
    """
    result_df = df.copy()
    
    # 1. 안전점검실점검율 (550점)
    result_df['안전점검_점수'] = (result_df['안전점검실점검율'] * 550).round(2)
    
    # 2. 중점고객안전점검율 (100점)
    result_df['중점고객_점수'] = (result_df['중점고객안전점검율'] * 100).round(2)
    
    # 3. 사용계약율 (등급제, 50점) - 수정됨
    def calculate_contract_score(rate):
        """
        수정된 사용계약 등급제:
        - A등급 (90% 이상): 50점
        - B등급 (80~90% 미만): 45점
        - C등급 (70~80% 미만): 40점
        - D등급 (70% 미만): 35점
        """
        if pd.isna(rate):
            return 35
        if rate >= 0.90:      # 90% 이상
            return 50  # A등급
        elif rate >= 0.80:    # 80% 이상 ~ 90% 미만
            return 45  # B등급
        elif rate >= 0.70:    # 70% 이상 ~ 80% 미만
            return 40  # C등급
        else:                 # 70% 미만
            return 35  # D등급
    
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


def get_contract_grade(rate: float) -> str:
    """
    사용계약율 등급 반환
    
    수정된 기준:
    - A등급: 90% 이상
    - B등급: 80~90% 미만
    - C등급: 70~80% 미만
    - D등급: 70% 미만
    """
    if pd.isna(rate):
        return 'D'
    if rate >= 0.90:
        return 'A'
    elif rate >= 0.80:
        return 'B'
    elif rate >= 0.70:
        return 'C'
    else:
        return 'D'


def add_contract_grades(df: pd.DataFrame) -> pd.DataFrame:
    """
    사용계약 등급 컬럼 추가
    """
    df = df.copy()
    df['사용계약등급'] = df['사용계약율'].apply(get_contract_grade)
    return df


def get_improvement_suggestions(row: pd.Series, target: float = 911) -> Dict[str, any]:
    """
    개선 제안 생성
    
    목표 점수 달성을 위한 구체적 제안
    """
    current_score = row['총점']
    gap = target - current_score
    
    if gap <= 0:
        return {
            'status': '목표 달성',
            'message': f'현재 {current_score:.1f}점으로 목표({target}점)를 달성했습니다! 🎉',
            'suggestions': []
        }
    
    suggestions = []
    
    # 각 KPI별 개선 가능 점수 계산
    kpi_improvements = {
        '안전점검': {
            'current': row['안전점검_점수'],
            'max': 550,
            'potential': 550 - row['안전점검_점수']
        },
        '중점고객': {
            'current': row['중점고객_점수'],
            'max': 100,
            'potential': 100 - row['중점고객_점수']
        },
        '사용계약': {
            'current': row['사용계약_점수'],
            'max': 50,
            'potential': 50 - row['사용계약_점수']
        },
        '상담응대': {
            'current': row['상담응대_점수'],
            'max': 100,
            'potential': 100 - row['상담응대_점수']
        },
        '상담기여': {
            'current': row['상담기여_점수'],
            'max': 100,
            'potential': 100 - row['상담기여_점수']
        },
        '만족도': {
            'current': row['만족도_점수'],
            'max': 100,
            'potential': 100 - row['만족도_점수']
        }
    }
    
    # 개선 가능성 높은 순으로 정렬
    sorted_kpis = sorted(
        kpi_improvements.items(),
        key=lambda x: x[1]['potential'],
        reverse=True
    )
    
    # 상위 3개 KPI에 대한 제안
    for kpi_name, kpi_data in sorted_kpis[:3]:
        if kpi_data['potential'] > 0:
            improvement_needed = min(gap, kpi_data['potential'])
            target_score = kpi_data['current'] + improvement_needed
            achievement_rate = (target_score / kpi_data['max']) * 100
            
            suggestions.append({
                'kpi': kpi_name,
                'current': round(kpi_data['current'], 1),
                'target': round(target_score, 1),
                'improvement': round(improvement_needed, 1),
                'max': kpi_data['max'],
                'target_rate': round(achievement_rate, 1)
            })
    
    return {
        'status': '개선 필요',
        'message': f'목표 달성까지 {gap:.1f}점 부족합니다.',
        'gap': round(gap, 1),
        'suggestions': suggestions
    }


def calculate_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    월별 추이 계산
    
    전월 대비 증감, 누적 추세 등
    """
    df = df.copy()
    df = df.sort_values(['센터명', '평가월'])
    
    # 센터별 전월 대비 증감
    df['전월대비_총점'] = df.groupby('센터명')['총점'].diff()
    df['전월대비_안전점검'] = df.groupby('센터명')['안전점검_점수'].diff()
    df['전월대비_중점고객'] = df.groupby('센터명')['중점고객_점수'].diff()
    df['전월대비_사용계약'] = df.groupby('센터명')['사용계약_점수'].diff()
    df['전월대비_상담응대'] = df.groupby('센터명')['상담응대_점수'].diff()
    df['전월대비_상담기여'] = df.groupby('센터명')['상담기여_점수'].diff()
    df['전월대비_만족도'] = df.groupby('센터명')['만족도_점수'].diff()
    
    # 추세 방향
    df['추세'] = df['전월대비_총점'].apply(
        lambda x: '상승 ↑' if x > 0 else ('하락 ↓' if x < 0 else '유지 →') if pd.notna(x) else '-'
    )
    
    return df


def get_ranking_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    월별 순위 변동 추적
    """
    df = df.copy()
    df = df.sort_values(['평가월', '총점'], ascending=[True, False])
    
    # 월별 순위 계산
    df['순위'] = df.groupby('평가월')['총점'].rank(ascending=False, method='min').astype(int)
    
    # 전월 순위
    df = df.sort_values(['센터명', '평가월'])
    df['전월순위'] = df.groupby('센터명')['순위'].shift(1)
    
    # 순위 변동
    df['순위변동'] = df['전월순위'] - df['순위']
    df['순위변동_표시'] = df['순위변동'].apply(
        lambda x: f'↑{int(x)}' if x > 0 else (f'↓{int(abs(x))}' if x < 0 else '→') if pd.notna(x) else '-'
    )
    
    return df


def export_summary_report(df: pd.DataFrame, filepath: str = None) -> pd.DataFrame:
    """
    요약 리포트 생성 (엑셀 내보내기용)
    """
    # 최신 월 데이터
    latest = df.loc[df.groupby('센터명')['평가월'].idxmax()].copy()
    
    report = latest[[
        '센터명', '평가월', '총점', '목표달성여부', '목표대비',
        '안전점검_점수', '안전점검_달성률',
        '중점고객_점수', '중점고객_달성률',
        '사용계약_점수', '사용계약_달성률',
        '상담응대_점수', '상담응대_달성률',
        '상담기여_점수', '상담기여_달성률',
        '만족도_점수', '만족도_달성률',
        '민원대응적정성', '주의경고', '가점'
    ]].copy()
    
    # 사용계약 등급 추가
    report['사용계약등급'] = report['사용계약율'].apply(get_contract_grade) if '사용계약율' in report.columns else '-'
    
    # 순위
    report = report.sort_values('총점', ascending=False)
    report.insert(0, '순위', range(1, len(report) + 1))
    
    # 위험도
    report['위험도'] = report['목표대비'].apply(
        lambda x: '안전 🟢' if x >= 0 else ('주의 🟡' if x >= -20 else '위험 🔴')
    )
    
    if filepath:
        report.to_excel(filepath, index=False)
    
    return report
