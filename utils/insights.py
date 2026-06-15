"""
자동 인사이트 생성 로직
- 데이터 기반 텍스트 자동 생성
- 월별 비교, 랭킹, 변화 감지 등
"""

import pandas as pd
from typing import List, Dict, Optional
from utils.styles import ScoreThresholds


# ==================== 인사이트 데이터 클래스 ====================

class Insight:
    """단일 인사이트 데이터 컨테이너"""
    
    def __init__(self, icon: str, title: str, message: str, 
                 category: str = "info", priority: int = 5):
        """
        Args:
            icon: 이모지 아이콘 (🏆, 📈, ⚠️ 등)
            title: 짧은 제목
            message: 본문 메시지 (HTML 가능)
            category: 'success' | 'warning' | 'danger' | 'info'
            priority: 1(낮음) ~ 10(높음). 정렬용
        """
        self.icon = icon
        self.title = title
        self.message = message
        self.category = category
        self.priority = priority
    
    def to_html(self) -> str:
        """HTML 텍스트로 변환"""
        return f"{self.icon} <b>{self.title}</b>: {self.message}"


# ==================== 기본 인사이트 생성 ====================

def get_basic_insights(df_latest: pd.DataFrame) -> List[Insight]:
    """
    최신 월 데이터에서 기본 인사이트 추출
    
    Args:
        df_latest: 최신 월 1개월치 데이터 (모든 센터)
    
    Returns:
        Insight 객체 리스트 (priority 내림차순 정렬)
    """
    insights = []
    
    if df_latest is None or df_latest.empty or '총점' not in df_latest.columns:
        return insights
    
    try:
        # 🏆 최고 성과
        top = df_latest.nlargest(1, '총점').iloc[0]
        insights.append(Insight(
            icon="🏆",
            title="최고 성과",
            message=f"{top['센터명']} ({top['총점']:.1f}점)",
            category="success",
            priority=8
        ))
        
        # ⚠️ 최저 성과 (911점 미만일 때만)
        bottom = df_latest.nsmallest(1, '총점').iloc[0]
        if bottom['총점'] < ScoreThresholds.TARGET:
            insights.append(Insight(
                icon="⚠️",
                title="가장 낮은 점수",
                message=f"{bottom['센터명']} ({bottom['총점']:.1f}점)",
                category="warning",
                priority=7
            ))
        
        # 📊 전체 평균 vs 목표
        avg = df_latest['총점'].mean()
        gap = avg - ScoreThresholds.TARGET
        if gap >= 0:
            insights.append(Insight(
                icon="📊",
                title="전체 평균",
                message=f"{avg:.1f}점 (목표 +{gap:.1f}점 ✅)",
                category="success",
                priority=6
            ))
        else:
            insights.append(Insight(
                icon="📊",
                title="전체 평균",
                message=f"{avg:.1f}점 (목표 {gap:.1f}점 미달)",
                category="warning",
                priority=6
            ))
        
        # 🎯 목표 달성 비율
        if '목표달성여부' in df_latest.columns:
            achieved = df_latest['목표달성여부'].sum()
            total = len(df_latest)
            rate = achieved / total * 100 if total > 0 else 0
            
            category = "success" if rate >= 80 else "warning" if rate >= 50 else "danger"
            insights.append(Insight(
                icon="🎯",
                title="목표 달성률",
                message=f"{achieved}/{total}개 센터 ({rate:.1f}%)",
                category=category,
                priority=7
            ))
        
        # 📏 점수 격차
        score_range = df_latest['총점'].max() - df_latest['총점'].min()
        if score_range > 100:
            insights.append(Insight(
                icon="📏",
                title="점수 격차",
                message=f"최고-최저 차이 {score_range:.1f}점 (편차 큼)",
                category="info",
                priority=4
            ))
    
    except Exception:
        pass
    
    # 우선순위 내림차순 정렬
    insights.sort(key=lambda x: x.priority, reverse=True)
    return insights


# ==================== 월간 변화 인사이트 ====================

def get_monthly_change_insights(df: pd.DataFrame, top_n: int = 3) -> List[Insight]:
    """
    이번 달 vs 지난 달 변화 분석
    
    Args:
        df: 전체 데이터 (여러 월)
        top_n: 상위/하위 몇 개를 인사이트로 뽑을지
    
    Returns:
        Insight 객체 리스트
    """
    insights = []
    
    if df is None or df.empty:
        return insights
    
    try:
        # 평가월별 정렬
        months = sorted(df['평가월'].unique())
        if len(months) < 2:
            return insights
        
        latest_month = months[-1]
        prev_month = months[-2]
        
        df_latest = df[df['평가월'] == latest_month][['센터명', '총점']].copy()
        df_prev = df[df['평가월'] == prev_month][['센터명', '총점']].copy()
        
        df_latest = df_latest.rename(columns={'총점': '이번달'})
        df_prev = df_prev.rename(columns={'총점': '지난달'})
        
        merged = pd.merge(df_latest, df_prev, on='센터명', how='inner')
        merged['변화'] = merged['이번달'] - merged['지난달']
        
        if merged.empty:
            return insights
        
        # 📈 최대 상승
        top_riser = merged.nlargest(1, '변화').iloc[0]
        if top_riser['변화'] > 0:
            insights.append(Insight(
                icon="📈",
                title="최대 상승",
                message=f"{top_riser['센터명']} (+{top_riser['변화']:.1f}점)",
                category="success",
                priority=9
            ))
        
        # 📉 최대 하락 (10점 이상 하락 시에만)
        top_faller = merged.nsmallest(1, '변화').iloc[0]
        if top_faller['변화'] < -10:
            insights.append(Insight(
                icon="📉",
                title="주의 - 큰 하락",
                message=f"{top_faller['센터명']} ({top_faller['변화']:.1f}점)",
                category="danger",
                priority=9
            ))
        
        # 평균 변화
        avg_change = merged['변화'].mean()
        if abs(avg_change) > 5:
            direction = "상승" if avg_change > 0 else "하락"
            icon = "📈" if avg_change > 0 else "📉"
            category = "success" if avg_change > 0 else "warning"
            insights.append(Insight(
                icon=icon,
                title=f"전체 평균 {direction}",
                message=f"전월 대비 {avg_change:+.1f}점",
                category=category,
                priority=5
            ))
    
    except Exception:
        pass
    
    insights.sort(key=lambda x: x.priority, reverse=True)
    return insights


# ==================== Top/Bottom 랭킹 ====================

def get_ranking_data(df_latest: pd.DataFrame, 
                     n: int = 5, 
                     mode: str = "score") -> Dict[str, pd.DataFrame]:
    """
    Top N / Bottom N 랭킹 데이터 추출
    
    Args:
        df_latest: 최신 월 데이터
        n: 몇 개 추출할지
        mode: 'score' (점수 순) | 'change' (변동 순)
    
    Returns:
        {'top': DataFrame, 'bottom': DataFrame}
    """
    result = {'top': pd.DataFrame(), 'bottom': pd.DataFrame()}
    
    if df_latest is None or df_latest.empty:
        return result
    
    try:
        if mode == "score":
            # 점수 기준
            result['top'] = (
                df_latest.nlargest(n, '총점')[['센터명', '총점']]
                .reset_index(drop=True)
            )
            result['bottom'] = (
                df_latest.nsmallest(n, '총점')[['센터명', '총점']]
                .reset_index(drop=True)
            )
        # 'change' 모드는 get_change_ranking으로 별도 호출
    except Exception:
        pass
    
    return result


def get_change_ranking(df: pd.DataFrame, n: int = 5) -> Dict[str, pd.DataFrame]:
    """
    전월 대비 변동 기준 Top/Bottom 랭킹
    
    Args:
        df: 전체 데이터 (여러 월)
        n: 몇 개 추출할지
    
    Returns:
        {'top': 상승 Top N, 'bottom': 하락 Top N}
    """
    result = {'top': pd.DataFrame(), 'bottom': pd.DataFrame()}
    
    if df is None or df.empty:
        return result
    
    try:
        months = sorted(df['평가월'].unique())
        if len(months) < 2:
            return result
        
        latest_month = months[-1]
        prev_month = months[-2]
        
        df_latest = df[df['평가월'] == latest_month][['센터명', '총점']].rename(
            columns={'총점': '이번달'}
        )
        df_prev = df[df['평가월'] == prev_month][['센터명', '총점']].rename(
            columns={'총점': '지난달'}
        )
        
        merged = pd.merge(df_latest, df_prev, on='센터명', how='inner')
        merged['변화'] = merged['이번달'] - merged['지난달']
        
        result['top'] = (
            merged.nlargest(n, '변화')[['센터명', '이번달', '변화']]
            .reset_index(drop=True)
        )
        result['bottom'] = (
            merged.nsmallest(n, '변화')[['센터명', '이번달', '변화']]
            .reset_index(drop=True)
        )
    
    except Exception:
        pass
    
    return result


# ==================== KPI별 취약점 분석 ====================

def get_kpi_weak_points(df_latest: pd.DataFrame, threshold: float = 85.0) -> List[Insight]:
    """
    KPI별 평균 달성률이 낮은 영역 식별
    
    Args:
        df_latest: 최신 월 데이터
        threshold: 취약 기준 (기본 85%)
    
    Returns:
        Insight 객체 리스트
    """
    insights = []
    
    kpi_mapping = {
        '안전점검': '안전점검_달성률',
        '중점고객': '중점고객_달성률',
        '사용계약': '사용계약_달성률',
        '상담응대': '상담응대_달성률',
        '상담기여': '상담기여_달성률',
        '만족도': '만족도_달성률',
    }
    
    try:
        for kpi_name, col_name in kpi_mapping.items():
            if col_name not in df_latest.columns:
                continue
            
            avg_rate = df_latest[col_name].mean()
            
            if avg_rate < threshold:
                weak_count = (df_latest[col_name] < threshold).sum()
                insights.append(Insight(
                    icon="🔍",
                    title=f"{kpi_name} 취약",
                    message=f"평균 {avg_rate:.1f}% ({weak_count}개 센터 {threshold:.0f}% 미만)",
                    category="warning",
                    priority=6
                ))
    except Exception:
        pass
    
    return insights


# ==================== 통합 인사이트 ====================

def get_all_insights(df: pd.DataFrame, max_count: int = 5) -> List[Insight]:
    """
    모든 인사이트를 통합해서 상위 N개 반환
    
    Args:
        df: 전체 데이터프레임
        max_count: 최대 표시할 인사이트 개수
    
    Returns:
        우선순위 정렬된 Insight 리스트
    """
    if df is None or df.empty:
        return []
    
    try:
        latest_month = df['평가월'].max()
        df_latest = df[df['평가월'] == latest_month]
        
        all_insights = []
        all_insights.extend(get_basic_insights(df_latest))
        all_insights.extend(get_monthly_change_insights(df))
        all_insights.extend(get_kpi_weak_points(df_latest))
        
        # 우선순위 정렬 후 상위 N개
        all_insights.sort(key=lambda x: x.priority, reverse=True)
        return all_insights[:max_count]
    
    except Exception:
        return []
