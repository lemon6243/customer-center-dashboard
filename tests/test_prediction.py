import pandas as pd

from utils.prediction import calculate_predicted_score, add_predictions_to_df


def test_first_month_prediction_scales_cumulative_kpis():
    """반기 1개월차: 누적형 KPI는 6배 환산, 변동형 KPI는 현재점수 유지"""
    row = pd.Series({
        "총점": 470,
        "안전점검_점수": 90,
        "중점고객_점수": 15,
        "사용계약_점수": 35,
        "상담응대_점수": 90,
        "상담기여_점수": 90,
        "만족도_점수": 90,
        "민원대응적정성": 0,
        "주의경고": 0,
        "가점": 0,
    })

    result = calculate_predicted_score(row, period_month=1)

    # 안전점검 90×6=540
    # 중점고객 15×6=90
    # 사용계약 35×1.1=38.5
    # 변동형 90+90+90
    assert result["예측총점"] == 938.5


def test_prediction_never_exceeds_1000():
    """예측점수는 반기 만점 1,000점을 넘지 않는다."""
    row = pd.Series({
        "총점": 950,
        "안전점검_점수": 550,
        "중점고객_점수": 100,
        "사용계약_점수": 50,
        "상담응대_점수": 100,
        "상담기여_점수": 100,
        "만족도_점수": 100,
        "민원대응적정성": 30,
        "주의경고": 0,
        "가점": 30,
    })

    result = calculate_predicted_score(row, period_month=1)

    assert result["예측총점"] == 1000


def test_half_end_prediction_equals_actual_score():
    """반기 마감월(6개월차)은 예측점수 대신 실제 총점을 사용한다."""
    row = pd.Series({
        "총점": 927.4,
        "안전점검_점수": 500,
        "중점고객_점수": 85,
        "사용계약_점수": 45,
        "상담응대_점수": 90,
        "상담기여_점수": 92,
        "만족도_점수": 95,
        "민원대응적정성": 0,
        "주의경고": 0,
        "가점": 0,
    })

    result = calculate_predicted_score(row, period_month=6)

    assert result["예측총점"] == 927.4


def test_add_predictions_creates_prediction_column():
    """센터별 예측점수 컬럼이 정상 추가된다."""
    df = pd.DataFrame([{
        "센터명": "테스트센터",
        "총점": 470,
        "안전점검_점수": 90,
        "중점고객_점수": 15,
        "사용계약_점수": 35,
        "상담응대_점수": 90,
        "상담기여_점수": 90,
        "만족도_점수": 90,
        "민원대응적정성": 0,
        "주의경고": 0,
        "가점": 0,
    }])

    result_df = add_predictions_to_df(df, period_month=1)

    assert "예측점수" in result_df.columns
    assert result_df.loc[0, "예측점수"] == 938.5
