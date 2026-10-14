import { RawRecord, ScoredRecord, PeriodInfo } from '../types';

export function normalizeDateString(val: any): string {
  if (val === null || val === undefined) return '2026-08-01';
  if (typeof val === 'number') {
    if (val > 30000 && val < 70000) {
      // Excel serial date code
      const d = new Date(Math.round((val - 25569) * 86400 * 1000));
      const y = d.getUTCFullYear();
      const m = String(d.getUTCMonth() + 1).padStart(2, '0');
      const day = String(d.getUTCDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }
    const s = String(val);
    if (s.length === 6) return `${s.slice(0, 4)}-${s.slice(4, 6)}-01`;
    return s;
  }
  if (val instanceof Date && !isNaN(val.getTime())) {
    const y = val.getFullYear();
    const m = String(val.getMonth() + 1).padStart(2, '0');
    const day = String(val.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  const str = String(val).trim();
  if (/^\d{5}$/.test(str)) {
    const num = Number(str);
    const d = new Date(Math.round((num - 25569) * 86400 * 1000));
    const y = d.getUTCFullYear();
    const m = String(d.getUTCMonth() + 1).padStart(2, '0');
    const day = String(d.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  if (/^\d{4}[-./]\d{1,2}([-./]\d{1,2})?$/.test(str)) {
    const parts = str.split(/[-./]/);
    const y = parts[0];
    const m = parts[1].padStart(2, '0');
    const day = (parts[2] || '01').padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  return str || '2026-08-01';
}

export function getPeriodInfo(dateInput: any): PeriodInfo {
  const dateStr = normalizeDateString(dateInput);
  const parts = dateStr.split('-');
  const year = parseInt(parts[0], 10) || 2026;
  const current_month = parseInt(parts[1], 10) || 2;
  const is_first_half = current_month <= 6;
  const half: '상반기' | '하반기' = is_first_half ? '상반기' : '하반기';
  const month_in_half = is_first_half ? current_month : current_month - 6;
  const progress_rate = month_in_half / 6.0;
  const is_half_end = current_month === 6 || current_month === 12;
  const period_text = is_first_half ? `상반기 (${current_month}/6개월)` : `하반기 (${current_month - 6}/6개월)`;
  const target_half_end_text = is_first_half ? '6월말' : '12월말';

  return {
    year,
    current_month,
    month_in_half,
    half,
    progress_rate,
    is_half_end,
    period_text,
    target_half_end_text,
  };
}

export function toPercentage(rate: number | null | undefined): number {
  if (rate === null || rate === undefined || isNaN(Number(rate))) return 0;
  const num = Number(rate);
  if (num <= 1.05 && num >= 0) return num * 100.0;
  return num;
}

export function calcSafetyInspectionScore(rate: number | null | undefined): number {
  const p = toPercentage(rate);
  return (p / 100.0) * 550.0;
}

export function calcKeyCustomerScore(rate: number | null | undefined): number {
  const p = toPercentage(rate);
  return (p / 100.0) * 100.0;
}

export function calcContractScore(rate: number | null | undefined): number {
  const p = toPercentage(rate);
  if (p >= 90.0) return 50.0;
  if (p >= 80.0) return 45.0;
  if (p >= 70.0) return 40.0;
  return 35.0;
}

export function calcCounselResponseScore(rate: number | null | undefined): number {
  const p = toPercentage(rate);
  return (p / 100.0) * 100.0;
}

export function calcCounselContribScore(rate: number | null | undefined): number {
  const p = toPercentage(rate);
  return (p / 100.0) * 100.0;
}

export function calcSatisfactionScore(rate: number | null | undefined): number {
  if (rate === null || rate === undefined || isNaN(Number(rate))) return 0;
  return Number(rate);
}

/**
 * 6월말(또는 12월말) 반기 마감 예상 점수 산출
 * - 안전점검(550점)과 중점고객(100점)은 모수(총 대상 오더) 고정 하에 분자(처리건수)가 매월 누적되는 오더 지표 (합산 650점)
 * - 비누적 지표(사용계약 50점, 상담응대 100점, 상담기여 100점, CS만족도 100점 = 총 350점)는 비율 유지 특성
 */
export function predictHalfEndScore(
  currentScore: number,
  month: number,
  safetyScore?: number,
  nonCumulativeScore?: number,
  keyScore?: number,
  adjustScore?: number
): number {
  const m = month <= 6 ? month : month - 6;
  if (m >= 6) return currentScore;
  const paceRatio = Math.max(0.1, m / 6.0);

  if (safetyScore !== undefined && keyScore !== undefined && nonCumulativeScore !== undefined) {
    const projectedSafety = Math.min(550.0, safetyScore / paceRatio);
    const projectedKey = Math.min(100.0, keyScore / paceRatio);
    const projectedTotal = projectedSafety + projectedKey + nonCumulativeScore + (adjustScore || 0);
    return Math.round(Math.min(1000.0, Math.max(0, projectedTotal)) * 10) / 10;
  }

  return Math.round(((currentScore * 0.85) + ((currentScore / paceRatio) * 0.15)) * 10) / 10;
}

export function processAndScoreRecord(raw: RawRecord): ScoredRecord {
  const dateStr = normalizeDateString(raw.평가월);
  const parts = dateStr.split('-');
  const year = parseInt(parts[0], 10) || 2026;
  const month = parseInt(parts[1], 10) || 2;
  const half: '상반기' | '하반기' = month <= 6 ? '상반기' : '하반기';

  const safetyRate = toPercentage(raw.안전점검실점검율);
  const keyRate = toPercentage(raw.중점고객안전점검율);
  const contractRate = toPercentage(raw.사용계약율);
  const responseRate = toPercentage(raw.상담응대율);
  const contribRate = toPercentage(raw.상담기여도);
  const satisfactionRate = raw.고객서비스만족도 != null ? Number(raw.고객서비스만족도) : 0;

  const safetyScore = (safetyRate / 100.0) * 550.0;
  const keyScore = (keyRate / 100.0) * 100.0;
  const contractScore = calcContractScore(contractRate);
  const responseScore = (responseRate / 100.0) * 100.0;
  const contribScore = (contribRate / 100.0) * 100.0;
  const satisfactionScore = satisfactionRate;

  const adjustScore = (raw.민원대응적정성 || 0) + (raw.주의경고 || 0) + (raw.가점 || 0);

  const calculatedTotal =
    safetyScore +
    keyScore +
    contractScore +
    responseScore +
    contribScore +
    satisfactionScore +
    adjustScore;

  const totalScore = raw.총점 !== null && raw.총점 !== undefined && !isNaN(Number(raw.총점))
    ? Number(raw.총점)
    : calculatedTotal;

  // 비누적 지속 유지 지표 (총 350점)
  const nonCumulative = contractScore + responseScore + contribScore + satisfactionScore;
  const expectedHalf = predictHalfEndScore(totalScore, month, safetyScore, nonCumulative, keyScore, adjustScore);

  return {
    ...raw,
    평가월: dateStr,
    연도: year,
    월: month,
    반기: half,
    총점: totalScore,
    안전점검_점수: safetyScore,
    중점고객_점수: keyScore,
    사용계약_점수: contractScore,
    상담응대_점수: responseScore,
    상담기여_점수: contribScore,
    만족도_점수: satisfactionScore,
    안전점검_달성률: safetyRate,
    중점고객_달성률: keyRate,
    사용계약_달성률: contractRate,
    상담응대_달성률: responseRate,
    상담기여_달성률: contribRate,
    만족도_달성률: satisfactionRate,
    예상반기총점: expectedHalf,
  };
}

/**
 * 전년 동월 및 전년 반기말 실적과 연계하여 ScoredRecord에 비교 메타데이터를 추가
 */
export function enrichRecordsWithYoYAndBenchmark(
  currentRecords: ScoredRecord[],
  allRecords: ScoredRecord[],
  periodInfo: PeriodInfo
): ScoredRecord[] {
  const prevYear = periodInfo.year - 1;
  const targetHalfEndMonth = periodInfo.half === '상반기' ? 6 : 12;

  // 전년 동월 레코드 맵
  const prevYearSameMonthMap = new Map<string, ScoredRecord>();
  allRecords
    .filter(r => r.연도 === prevYear && r.월 === periodInfo.current_month)
    .forEach(r => prevYearSameMonthMap.set(r.센터명, r));

  // 전년 반기말(6월말 또는 12월말) 레코드 맵
  const prevYearHalfEndMap = new Map<string, ScoredRecord>();
  allRecords
    .filter(r => r.연도 === prevYear && r.월 === targetHalfEndMonth)
    .forEach(r => prevYearHalfEndMap.set(r.센터명, r));

  // 전월 레코드 맵
  const prevMonth = periodInfo.current_month === 1 ? 12 : periodInfo.current_month - 1;
  const prevMonthYear = periodInfo.current_month === 1 ? periodInfo.year - 1 : periodInfo.year;
  const prevMonthMap = new Map<string, ScoredRecord>();
  allRecords
    .filter(r => r.연도 === prevMonthYear && r.월 === prevMonth)
    .forEach(r => prevMonthMap.set(r.센터명, r));

  // 기준 누적치: 6개월 동안 92% 달성이 목표선일 때 현재 경과월 기준 기대치
  const benchmarkSafetyRate = (periodInfo.month_in_half / 6.0) * 92.0;

  return currentRecords.map(rec => {
    const py = prevYearSameMonthMap.get(rec.센터명);
    const pyEnd = prevYearHalfEndMap.get(rec.센터명);
    const pm = prevMonthMap.get(rec.센터명);

    const yoyDiff = py ? rec.총점 - py.총점 : null;
    const momDiff = pm ? rec.총점 - pm.총점 : null;

    // 전년 12월말(또는 6월말) 실적과 전년 동월 대비 증감을 100% 기준으로 연계 예측
    let updatedExpectedHalf = rec.예상반기총점;
    if (periodInfo.month_in_half < 6) {
      if (pyEnd && yoyDiff !== null) {
        updatedExpectedHalf = Math.round(Math.min(1000, Math.max(0, pyEnd.총점 + yoyDiff)) * 10) / 10;
      } else if (pyEnd) {
        updatedExpectedHalf = Math.round(pyEnd.총점 * 10) / 10;
      }
    }

    let 도달판정: '정상궤도' | '주의' | '위험' = '정상궤도';
    if (updatedExpectedHalf < 905) {
      도달판정 = '위험';
    } else if (updatedExpectedHalf < 915) {
      도달판정 = '주의';
    }

    let 오더진척상태: '양호' | '보통' | '지연' = '양호';
    if (rec.안전점검_달성률 < benchmarkSafetyRate - 3.0) {
      오더진척상태 = '지연';
    } else if (rec.안전점검_달성률 < benchmarkSafetyRate) {
      오더진척상태 = '보통';
    }

    return {
      ...rec,
      전년대비증감: yoyDiff,
      전년동월_총점: py ? py.총점 : null,
      전년동월_안전점검달성률: py ? py.안전점검_달성률 : null,
      전년동월대비_증감: yoyDiff,
      전년반기말_총점: pyEnd ? pyEnd.총점 : null,
      예상반기총점: updatedExpectedHalf,
      도달판정,
      오더진척상태,
    };
  });
}

