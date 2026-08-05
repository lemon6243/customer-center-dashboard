import pandas as pd
import streamlit as st
from typing import Optional, Dict, List


def _clean_center_and_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    '센터명'과 '평가월' 컬럼을 정규화하고 결측 행을 제거하는 공통 전처리.
    - 센터명: 문자열로 강제 변환, 공백 제거, 빈 문자열/'nan' 제거
    - 평가월: 날짜 변환 실패 시 NaT 처리 후 제거
    """
    before_rows = len(df)

    # 1) 센터명 정규화
    df['센터명'] = df['센터명'].astype(str).str.strip()
    # pandas가 NaN을 'nan' 문자열로 바꾸는 경우 대비
    df = df[~df['센터명'].str.lower().isin(['nan', 'none', ''])]

    # 2) 평가월 변환 (실패 시 NaT)
    df['평가월'] = pd.to_datetime(df['평가월'], errors='coerce')
    df = df.dropna(subset=['평가월'])

    after_rows = len(df)
    removed = before_rows - after_rows

    if removed > 0:
        st.warning(
            f"⚠️ 센터명 또는 평가월이 비어있거나 잘못된 {removed}개 행을 자동으로 제외했습니다."
        )

    return df.reset_index(drop=True)
    
def add_period_columns(df: pd.DataFrame) -> pd.DataFrame:
    """평가월에서 연도·월·반기 파생 컬럼 생성"""
    result = df.copy()

    result["평가월"] = pd.to_datetime(
        result["평가월"],
        errors="coerce",
    )

    result["연도"] = result["평가월"].dt.year
    result["월"] = result["평가월"].dt.month
    result["반기"] = result["월"].apply(
        lambda month: "상반기"
        if pd.notna(month) and month <= 6
        else "하반기"
    )

    return result


def validate_ratio_scale_mixing(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """
    비율 컬럼에 0~1 형식과 0~100 형식이 섞였는지 검사.

    예:
    - 정상: 0.95, 0.88
    - 정상: 95, 88
    - 오류: 0.95, 88  ← 혼재
    """
    ratio_cols = [
        "안전점검실점검율",
        "중점고객안전점검율",
        "사용계약율",
        "상담응대율",
        "상담기여도",
    ]

    errors = []

    for col in ratio_cols:
        if col not in df.columns:
            continue

        values = pd.to_numeric(df[col], errors="coerce").dropna()

        if values.empty:
            continue

        has_fraction = ((values >= 0) & (values <= 1.2)).any()
        has_percent = (values > 1.5).any()

        if has_fraction and has_percent:
            errors.append(
                f"❌ '{col}' 컬럼에 비율 형식이 혼재되어 있습니다. "
                f"0~1 형식 또는 0~100 형식 중 하나로 통일해주세요."
            )

    return len(errors) == 0, errors




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
            st.info(
                "💡 엑셀 파일의 첫 행(헤더)에 다음 컬럼이 포함되어 있어야 합니다:\n"
                "   - **센터명** (각 행마다 24개 센터 이름 중 하나)\n"
                "   - **평가월** (예: 2026-05-01)\n"
                "   - 그 외 안전점검실점검율, 중점고객안전점검율 등 KPI 컬럼"
            )
            return None

        # ▼ 핵심 방어 로직: 센터명/평가월 결측 또는 잘못된 값 제거
        df = _clean_center_and_month(df)

        if df.empty:
            st.error(
                "❌ 유효한 데이터가 없습니다. "
                "엑셀 파일의 '센터명' 컬럼에 실제 센터명이 입력되어 있는지 확인해주세요."
            )
            return None

        # 비율값 형식 혼재 확인: 0.95와 95가 같이 있으면 자동 변환 시 오류 발생
        is_ratio_valid, ratio_errors = validate_ratio_scale_mixing(df)
        
        if not is_ratio_valid:
            for msg in ratio_errors:
                st.error(msg)
            return None
        
        # 연도·월·반기 공통 컬럼 생성
        df = add_period_columns(df)
        
        # 정렬
        df = df.sort_values(["센터명", "연도", "반기", "평가월"]).reset_index(drop=True)


        # 데이터 방식 자동 감지
        if '당월안전점검완료' in df.columns:
            st.success("✅ 당월 실적 데이터 감지 → 자동 누적 계산 모드")
            df = calculate_cumulative_from_monthly(df)
        elif '누적안전점검완료' in df.columns:
            st.success("✅ 누적 실적 데이터 감지 → 직접 입력 모드")
            df = process_cumulative_data(df)
        else:
            st.success("✅ 비율 데이터 감지 → 기존 방식 (월별 독립 평가)")
            df = process_percentage_data(df)

        return df

    except Exception as e:
        st.error(f"❌ 파일 로딩 실패: {str(e)}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
        return None


def calculate_cumulative_from_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    당월 실적을 누적 실적으로 변환

    핵심 로직:
    - 반기별로 그룹화
    - 월별 누적 합계 계산
    - 누적 비율 = 누적 실적 / 총 오더수
    """
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

    for kpi_name, cols in kpi_mapping.items():
        if cols['monthly'] in df.columns and cols['total'] in df.columns:
            # 숫자형 강제 변환
            df[cols['monthly']] = pd.to_numeric(df[cols['monthly']], errors='coerce').fillna(0)
            df[cols['total']] = pd.to_numeric(df[cols['total']], errors='coerce').fillna(0)

            # 반기별 누적 합계
            df[cols['cumulative']] = df.groupby(['센터명', '반기'])[cols['monthly']].cumsum()

            # 누적 비율 (0으로 나누기 방지)
            df[cols['rate']] = (df[cols['cumulative']] / df[cols['total']].replace(0, pd.NA)).fillna(0)
            df[cols['rate']] = df[cols['rate']].clip(0, 1)

            st.info(f"📊 {kpi_name} 누적 계산 완료")

    # 고객서비스만족도
    if '당월만족도' in df.columns:
        df['당월만족도'] = pd.to_numeric(df['당월만족도'], errors='coerce')
        df['고객서비스만족도'] = df.groupby(['센터명', '반기'])['당월만족도'].transform(
            lambda x: x.expanding().mean()
        )
        st.info("📊 고객서비스만족도 누적 평균 계산 완료")
    elif '고객서비스만족도' in df.columns:
        df['고객서비스만족도'] = pd.to_numeric(df['고객서비스만족도'], errors='coerce')

    # 감점/가점
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
            df[cumulative_col] = pd.to_numeric(df[cumulative_col], errors='coerce').fillna(0)
            df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
            df[rate_col] = (df[cumulative_col] / df[total_col].replace(0, pd.NA)).fillna(0)
            df[rate_col] = df[rate_col].clip(0, 1)

    if '고객서비스만족도' in df.columns:
        df['고객서비스만족도'] = pd.to_numeric(df['고객서비스만족도'], errors='coerce')

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
            # 0~1 범위로 정규화 (퍼센트로 입력된 경우 대비)
            if df[col].max(skipna=True) is not pd.NA and df[col].max(skipna=True) > 1.5:
                df[col] = df[col] / 100

    if '고객서비스만족도' in df.columns:
        df['고객서비스만족도'] = pd.to_numeric(df['고객서비스만족도'], errors='coerce')

    adjustment_cols = ['민원대응적정성', '주의경고', '가점']
    for col in adjustment_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    return df


def validate_cumulative_data(df: pd.DataFrame) -> tuple[bool, List[str], List[str]]:

    """
    처리 완료 데이터 검증

    오류(error)
    - 필수 컬럼 누락
    - 센터명·평가월 중복
    - 비율 범위 이상

    경고(warning)
    - 센터 수 변동
    - 반기 내 월 누락
    - 반기 시작월인데 총점이 지나치게 높은 경우
    """
    errors: List[str] = []
    warnings: List[str] = []

    if df is None or df.empty:
        return False, ["❌ 검증할 데이터가 없습니다."]

    required_cols = ["센터명", "평가월"]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, [f"❌ 필수 컬럼 누락: {', '.join(missing_cols)}"]

    work = add_period_columns(df)

    # 1. 센터명·평가월 중복 검사
    duplicates = work.duplicated(
        subset=["센터명", "평가월"],
        keep=False,
    )

    if duplicates.any():
        duplicate_rows = work.loc[
            duplicates,
            ["센터명", "평가월"],
        ].sort_values(["센터명", "평가월"])

        examples = [
            f"{row['센터명']}({pd.Timestamp(row['평가월']).strftime('%Y-%m')})"
            for _, row in duplicate_rows.head(5).iterrows()
        ]

        errors.append(
            "❌ 동일 센터·동일 평가월 데이터가 중복되었습니다: "
            + ", ".join(examples)
            + (" 외" if len(duplicate_rows) > 5 else "")
        )

    # 2. 센터 수 확인
    center_count = work["센터명"].nunique()

    if center_count != 24:
        warnings.append(
            f"⚠️ 전체 센터 수가 24개가 아닙니다. 현재 {center_count}개입니다."
        )

    # 3. 반기별 월 순서/누락 확인
    for (center, year, half), group in work.groupby(["센터명", "연도", "반기"]):
        months = sorted(group["월"].dropna().astype(int).unique().tolist())

        if not months:
            continue

        start_month = 1 if half == "상반기" else 7
        expected_months = list(range(start_month, max(months) + 1))

        if months != expected_months:
            warnings.append(
                f"⚠️ {center} {int(year)}년 {half} 월 데이터가 순차적이지 않습니다: "
                f"현재 {months} / 예상 {expected_months}"
            )

    # 4. 비율 범위 검사
    percentage_cols = [
        "안전점검실점검율",
        "중점고객안전점검율",
        "사용계약율",
        "상담응대율",
        "상담기여도",
    ]

    for col in percentage_cols:
        if col not in work.columns:
            continue

        values = pd.to_numeric(work[col], errors="coerce").dropna()

        if ((values < 0) | (values > 1.1)).any():
            errors.append(
                f"❌ {col} 값이 정상 범위(0~1)를 벗어났습니다. "
                "업로드 데이터의 비율 형식을 확인해주세요."
            )

    # 5. 최신 월 센터 누락 확인
    latest_month = work["평가월"].max()

    if pd.notna(latest_month):
        latest_df = work[work["평가월"] == latest_month]
        latest_center_count = latest_df["센터명"].nunique()

        if latest_center_count != center_count:
            warnings.append(
                f"⚠️ 최신 평가월({latest_month.strftime('%Y-%m')})의 센터 수는 "
                f"{latest_center_count}개이며, 전체 센터 수 {center_count}개와 다릅니다."
            )

        # 6. 반기 시작월 리셋 의심 경고
        latest_month_num = latest_month.month

        if latest_month_num in (1, 7) and "총점" in latest_df.columns:
            scores = pd.to_numeric(latest_df["총점"], errors="coerce").dropna()
            high_score_centers = latest_df.loc[
                pd.to_numeric(latest_df["총점"], errors="coerce") >= 850,
                "센터명",
            ].dropna().astype(str).tolist()

            if high_score_centers:
                preview = ", ".join(high_score_centers[:5])
                suffix = " 외" if len(high_score_centers) > 5 else ""

                warnings.append(
                    f"⚠️ 반기 시작월({latest_month.strftime('%Y-%m')})인데 "
                    f"850점 이상 센터가 {len(high_score_centers)}개입니다: "
                    f"{preview}{suffix}. "
                    "상반기/하반기 누적점수가 정상적으로 리셋되었는지 확인해주세요."
                )

    # 화면에는 직접 출력하지 않음
    # 관리자 화면에서만 별도로 표시
    return len(errors) == 0, errors, warnings



def get_data_summary(df: pd.DataFrame) -> Dict:
    """
    데이터 요약 정보
    """
    # 방어적으로 센터명 정리
    valid_centers = df['센터명'].dropna().astype(str).str.strip()
    valid_centers = valid_centers[valid_centers != '']

    return {
        'total_centers': valid_centers.nunique(),
        'center_list': sorted(valid_centers.unique().tolist()),
        'latest_month': df['평가월'].max().strftime('%Y년 %m월') if df['평가월'].notna().any() else '-',
        'first_month': df['평가월'].min().strftime('%Y년 %m월') if df['평가월'].notna().any() else '-',
        'total_months': df['평가월'].nunique(),
        'first_half_months': df[df['반기'] == '상반기']['월'].nunique(),
        'second_half_months': df[df['반기'] == '하반기']['월'].nunique(),
        'has_first_half': '상반기' in df['반기'].values,
        'has_second_half': '하반기' in df['반기'].values,
    }
