import pandas as pd
import streamlit as st
from typing import Optional, Dict, List

def load_cumulative_data(uploaded_file) -> Optional[pd.DataFrame]:
    """
    누적 평가 데이터 로딩
    
    지원 방식:
    1. 당월 실적 입력 → 자동 누적 계산 (추천)
    2. 누적 실적 직접 입력
    3. 비율만 입력 (기존 방식)
    """
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # 필수 컬럼 확인
        required_columns = ['센터명', '평가월']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
            st.info("💡 필요한 컬럼: 센터명, 평가월, ...")
            return None
        
        # 날짜 변환
        df['평가월'] = pd.to_datetime(df['평가월'])
        df['연도'] = df['평가월'].dt.year
        df['월'] = df['평가월'].dt.month
        
        # 반기 자동 분류
        df['반기'] = df['월'].apply(lambda m: '상반기' if m <= 6 else '하반기')
        
        # 정렬 (센터명, 반기, 평가월 순)
        df = df.sort_values(['센터명', '반기', '평가월'])
        
        # 데이터 방식 자동 감지
        if '당월안전점검완료' in df.columns:
            # 방식 1: 당월 실적 → 누적 계산 (추천)
            st.success("✅ 당월 실적 데이터 감지 → 자동 누적 계산 모드")
            df = calculate_cumulative_from_monthly(df)
        elif '누적안전점검완료' in df.columns:
            # 방식 2: 누적 실적 직접 입력
            st.success("✅ 누적 실적 데이터 감지 → 직접 입력 모드")
            df = process_cumulative_data(df)
        else:
            # 방식 3: 기존 방식 (비율만)
            st.success("✅ 비율 데이터 감지 → 기존 방식 (월별 독립 평가)")
            df = process_percentage_data(df)
        
        return df
        
    except Exception as e:
        st.error(f"❌ 파일 로딩 실패: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def calculate_cumulative_from_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    당월 실적을 누적 실적으로 변환
    
    핵심 로직:
    - 반기별로 그룹화
    - 월별 누적 합계 계산
    - 누적 비율 = 누적 실적 / 총 오더수
    """
    # 각 지표별 매핑
    kpi_mapping = {
        '안전점검': {
            'monthly': '당월안전점검완료',
            'cumulative': '누적안전점검완료',
            'total': '안전점검총오더수',
            'rate': '안전점검실점검율'
        },
        '중점고객': {
            'monthly': '당월중점고객점검완료',
            'cumulative': '누적중점고객점검완료',
            'total': '중점고객총오더수',
            'rate': '중점고객안전점검율'
        },
        '사용계약': {
            'monthly': '당월사용계약체결',
            'cumulative': '누적사용계약체결',
            'total': '사용계약총오더수',
            'rate': '사용계약율'
        },
        '상담응대': {
            'monthly': '당월상담응대완료',
            'cumulative': '누적상담응대완료',
            'total': '상담응대총건수',
            'rate': '상담응대율'
        },
        '상담기여': {
            'monthly': '당월상담기여완료',
            'cumulative': '누적상담기여완료',
            'total': '상담기여총건수',
            'rate': '상담기여도'
        }
    }
    
    # 각 지표별 누적 계산
    for kpi_name, cols in kpi_mapping.items():
        if cols['monthly'] in df.columns and cols['total'] in df.columns:
            # 반기별로 그룹화하여 누적 합계
            df[cols['cumulative']] = df.groupby(['센터명', '반기'])[cols['monthly']].cumsum()
            
            # 누적 비율 계산
            df[cols['rate']] = (df[cols['cumulative']] / df[cols['total']]).fillna(0)
            
            # 0~1 범위로 제한
            df[cols['rate']] = df[cols['rate']].clip(0, 1)
            
            st.info(f"📊 {kpi_name} 누적 계산 완료")
    
    # 고객서비스만족도는 누적 평균
    if '당월만족도' in df.columns:
        df['고객서비스만족도'] = df.groupby(['센터명', '반기'])['당월만족도'].transform(
            lambda x: x.expanding().mean()
        )
        st.info("📊 고객서비스만족도 누적 평균 계산 완료")
    elif '고객서비스만족도' in df.columns:
        # 이미 만족도가 있으면 그대로 사용
        df['고객서비스만족도'] = pd.to_numeric(df['고객서비스만족도'], errors='coerce')
    
    # 감점/가점 처리
    adjustment_cols = ['민원대응적정성', '주의경고', '가점']
    for col in adjustment_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    
    return df


def process_cumulative_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    누적 실적이 직접 입력된 경우 처리
    """
    kpi_mapping = {
        '누적안전점검완료': ('안전점검총오더수', '안전점검실점검율'),
        '누적중점고객점검완료': ('중점고객총오더수', '중점고객안전점검율'),
        '누적사용계약체결': ('사용계약총오더수', '사용계약율'),
        '누적상담응대완료': ('상담응대총건수', '상담응대율'),
        '누적상담기여완료': ('상담기여총건수', '상담기여도'),
    }
    
    for cumulative_col, (total_col, rate_col) in kpi_mapping.items():
        if cumulative_col in df.columns and total_col in df.columns:
            df[rate_col] = (df[cumulative_col] / df[total_col]).fillna(0)
            df[rate_col] = df[rate_col].clip(0, 1)
    
    # 고객서비스만족도
    if '고객서비스만족도' in df.columns:
        df['고객서비스만족도'] = pd.to_numeric(df['고객서비스만족도'], errors='coerce')
    
    # 감점/가점
    adjustment_cols = ['민원대응적정성', '주의경고', '가점']
    for col in adjustment_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    
    return df


def process_percentage_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    기존 방식: 비율만 입력된 경우
    """
    percentage_cols = [
        '안전점검실점검율', '중점고객안전점검율', 
        '사용계약율', '상담응대율', '상담기여도'
    ]
    
    for col in percentage_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # 0~1 범위로 정규화
            if df[col].max() > 1.5:
                df[col] = df[col] / 100
    
    # 고객서비스만족도
    if '고객서비스만족도' in df.columns:
        df['고객서비스만족도'] = pd.to_numeric(df['고객서비스만족도'], errors='coerce')
    
    # 감점/가점
    adjustment_cols = ['민원대응적정성', '주의경고', '가점']
    for col in adjustment_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    
    return df


def validate_cumulative_data(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """
    누적 데이터 검증
    """
    errors = []
    warnings = []
    
    # 센터 수 확인
    center_count = df['센터명'].nunique()
    if center_count != 24:
        warnings.append(f"⚠️ 센터 수가 24개가 아닙니다 (현재: {center_count}개)")
    
    # 반기별 데이터 확인
    for center in df['센터명'].unique():
        center_data = df[df['센터명'] == center]
        
        for period in ['상반기', '하반기']:
            period_data = center_data[center_data['반기'] == period]
            
            if len(period_data) > 0:
                # 월이 순차적인지 확인
                months = sorted(period_data['월'].unique())
                expected_months = list(range(1, 7)) if period == '상반기' else list(range(7, 13))
                
                if months != expected_months[:len(months)]:
                    warnings.append(f"⚠️ {center} {period} 데이터가 순차적이지 않습니다: {months}")
    
    # 비율 범위 확인
    percentage_cols = [
        '안전점검실점검율', '중점고객안전점검율', 
        '사용계약율', '상담응대율', '상담기여도'
    ]
    
    for col in percentage_cols:
        if col in df.columns:
            if (df[col] < 0).any() or (df[col] > 1.1).any():
                errors.append(f"❌ {col}이 정상 범위(0~1)를 벗어났습니다")
    
    # 경고 메시지 표시
    for warning in warnings:
        st.warning(warning)
    
    return (len(errors) == 0, errors)


def get_data_summary(df: pd.DataFrame) -> Dict:
    """
    데이터 요약 정보
    """
    return {
        'total_centers': df['센터명'].nunique(),
        'center_list': sorted(df['센터명'].unique().tolist()),
        'latest_month': df['평가월'].max().strftime('%Y년 %m월'),
        'first_month': df['평가월'].min().strftime('%Y년 %m월'),
        'total_months': df['평가월'].nunique(),
        'first_half_months': df[df['반기'] == '상반기']['월'].nunique(),
        'second_half_months': df[df['반기'] == '하반기']['월'].nunique(),
        'has_first_half': '상반기' in df['반기'].values,
        'has_second_half': '하반기' in df['반기'].values,
    }
