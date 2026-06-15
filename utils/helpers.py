"""
공통 헬퍼 함수
- 센터명 안전 처리
- 데이터프레임 정리
- Excel 변환 등
"""

import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
from typing import Optional


def safe_unique_centers(df: pd.DataFrame) -> list:
    """
    '센터명' 컬럼에서 NaN/공백/'nan' 문자열을 제외하고
    안전하게 정렬된 고유 센터명 리스트를 반환.
    
    sorted()가 float(NaN)과 str을 비교할 때 발생하는
    TypeError를 원천 차단.
    """
    if '센터명' not in df.columns:
        return []
    
    series = df['센터명'].dropna().astype(str).str.strip()
    series = series[~series.str.lower().isin(['nan', 'none', ''])]
    return sorted(series.unique().tolist())


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    '센터명'과 '평가월' 컬럼을 정규화하고 잘못된 행을 제거.
    """
    if df is None or df.empty:
        return df
    
    if '센터명' not in df.columns or '평가월' not in df.columns:
        return df
    
    before = len(df)
    df = df.copy()
    
    # 센터명 정규화
    df['센터명'] = df['센터명'].astype(str).str.strip()
    df = df[~df['센터명'].str.lower().isin(['nan', 'none', ''])]
    
    # 평가월 정규화
    df['평가월'] = pd.to_datetime(df['평가월'], errors='coerce')
    df = df.dropna(subset=['평가월'])
    
    after = len(df)
    if before != after:
        st.warning(
            f"⚠️ 센터명 또는 평가월이 비어있는 {before - after}개 행을 자동으로 제외했습니다."
        )
    
    return df.reset_index(drop=True)


def convert_df_to_excel(df: pd.DataFrame, sheet_name: str = '성과데이터') -> Optional[bytes]:
    """DataFrame을 Excel 바이트로 변환"""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        st.error(f"❌ Excel 변환 실패: {e}")
        return None


def get_filename_with_timestamp(prefix: str = "data", ext: str = "xlsx") -> str:
    """타임스탬프가 포함된 파일명 생성"""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}"


def format_period(month: int, is_first_half: bool = True) -> str:
    """월 → '상반기 5월' 형식 변환"""
    period_month = month if is_first_half else month - 6
    half = "상반기" if is_first_half else "하반기"
    return f"{half} {period_month}월"


def get_period_info(latest_month) -> dict:
    """평가월에서 반기 정보 추출"""
    current_month = latest_month.month
    is_first_half = current_month <= 6
    period_month = current_month if is_first_half else current_month - 6
    
    return {
        "current_month": current_month,
        "is_first_half": is_first_half,
        "period_month": period_month,
        "progress_rate": period_month / 6,
        "period_text": format_period(current_month, is_first_half),
    }
