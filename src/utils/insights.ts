import { ScoredRecord, PeriodInfo } from '../types';

export interface AutomatedInsight {
  type: 'danger' | 'warning' | 'success' | 'info';
  title: string;
  message: string;
  badge: string;
}

export function generateAutomatedInsights(
  dfLatest: ScoredRecord[],
  dfPrev: ScoredRecord[],
  periodInfo?: PeriodInfo,
  dfAll?: ScoredRecord[]
): AutomatedInsight[] {
  const insights: AutomatedInsight[] = [];
  if (!dfLatest || dfLatest.length === 0) return insights;

  const totalCenters = dfLatest.length;
  const currentMonth = periodInfo?.current_month || dfLatest[0]?.월 || 2;
  const monthInHalf = periodInfo?.month_in_half || (currentMonth <= 6 ? currentMonth : currentMonth - 6);
  const targetEndText = periodInfo?.target_half_end_text || (currentMonth <= 6 ? '6월말' : '12월말');
  const halfText = periodInfo?.half || (currentMonth <= 6 ? '상반기' : '하반기');

  const avgScore = dfLatest.reduce((sum, r) => sum + r.총점, 0) / totalCenters;
  const avgSafety = dfLatest.reduce((sum, r) => sum + r.안전점검_달성률, 0) / totalCenters;
  const avgKey = dfLatest.reduce((sum, r) => sum + r.중점고객_달성률, 0) / totalCenters;

  // 누적 기대 목표선 (6개월 차에 92%~95% 달성 기준)
  const benchmarkSafetyRate = (monthInHalf / 6.0) * 92.0;

  // 1. 6월말 911점 도달 가능성 및 누적 페이스 진단
  const onTrackCount = dfLatest.filter(r => r.예상반기총점 >= 911.0).length;
  const onTrackRate = ((onTrackCount / totalCenters) * 100).toFixed(1);
  const cautionCount = totalCenters - onTrackCount;

  if (onTrackCount >= totalCenters * 0.8) {
    insights.push({
      type: 'success',
      title: `${targetEndText} 911점 도달 정상 궤도 (${onTrackCount}개소)`,
      message: `현재 ${monthInHalf}개월차 기준 전체 ${totalCenters}개 센터 중 ${onTrackCount}개소(${onTrackRate}%)가 ${targetEndText} 911점 달성 목표선 대비 안정적인 추진 페이스를 보이고 있습니다.`,
      badge: '911점 궤도 정상',
    });
  } else {
    insights.push({
      type: 'warning',
      title: `${targetEndText} 911점 도달 집중 관리 (${cautionCount}개소 보강 필요)`,
      message: `현재 ${monthInHalf}개월차 기준 ${cautionCount}개 센터가 ${targetEndText} 911점 도달 페이스에 다소 지연을 보이고 있습니다. 안전점검 오더 처리 속도를 조기 보강해야 합니다.`,
      badge: '페이스 관리 필요',
    });
  }

  // 2. 전년 동월(YoY) 종합 비교 진단
  const yoyValidRecords = dfLatest.filter(r => r.전년동월_총점 != null);
  if (yoyValidRecords.length > 0) {
    const prevYearAvg =
      yoyValidRecords.reduce((sum, r) => sum + (r.전년동월_총점 || 0), 0) / yoyValidRecords.length;
    const yoyDiff = avgScore - prevYearAvg;

    const sortedByYoY = [...yoyValidRecords].sort(
      (a, b) => (b.전년동월대비_증감 || 0) - (a.전년동월대비_증감 || 0)
    );
    const topGain = sortedByYoY[0];

    if (yoyDiff >= 0) {
      insights.push({
        type: 'success',
        title: '전년 동월 대비 종합 성과 상승',
        message: `현재 ${monthInHalf}월차 평균 총점(${avgScore.toFixed(1)}점)은 전년 동월(${prevYearAvg.toFixed(1)}점) 대비 +${yoyDiff.toFixed(1)}점 상회하여 우수한 누적 흐름을 보이고 있습니다.${
          topGain ? ` 특히 ${topGain.센터명} 센터가 전년 대비 +${(topGain.전년동월대비_증감 || 0).toFixed(1)}점 상승하여 가장 두드러집니다.` : ''
        }`,
        badge: `YoY +${yoyDiff.toFixed(1)}점`,
      });
    } else {
      insights.push({
        type: 'warning',
        title: '전년 동월 대비 성과 지연 감지',
        message: `현재 ${monthInHalf}월차 평균 총점(${avgScore.toFixed(1)}점)이 전년 동월(${prevYearAvg.toFixed(1)}점) 대비 ${yoyDiff.toFixed(1)}점 다소 뒤처져 있어, ${targetEndText} 911점 달성을 위한 조기 오더 드라이브가 필요합니다.`,
        badge: `YoY ${yoyDiff.toFixed(1)}점`,
      });
    }
  }

  // 3. 안전점검 실점검율 진척 현황 진단
  const safetyDiff = avgSafety - benchmarkSafetyRate;
  const isSafetyGood = safetyDiff >= -3.0;
  insights.push({
    type: isSafetyGood ? 'success' : 'info',
    title: '안전점검 실점검율 진척 현황',
    message: `현재 ${monthInHalf}개월차 기준 평균 실점검율은 ${avgSafety.toFixed(1)}%(중점안전점검 ${avgKey.toFixed(1)}%)입니다. 계획 대비 ${isSafetyGood ? '양호하게 추진되고 있습니다.' : '일부 센터의 추가 점검 관리가 필요합니다.'}`,
    badge: isSafetyGood ? '계획대비 양호' : '진척 관리 필요',
  });

  // 4. 전년 동월 대비 누적 오더 처리 지연 센터 진단 (집중 코칭 대상)
  const lagCenters = dfLatest.filter(
    r =>
      (r.전년동월대비_증감 != null && r.전년동월대비_증감 < -10.0) ||
      r.예상반기총점 < 905.0 ||
      r.오더진척상태 === '지연'
  );

  if (lagCenters.length > 0) {
    const lagNames = lagCenters.map(r => r.센터명).slice(0, 3).join(', ');
    const worstYoY = [...lagCenters].sort(
      (a, b) => (a.전년동월대비_증감 || 0) - (b.전년동월대비_증감 || 0)
    )[0];

    insights.push({
      type: 'warning',
      title: '전년 동월 대비 누적 지연 센터 코칭 필요',
      message: `${lagNames} 등 ${lagCenters.length}개 센터는 전년 동월 대비 오더 누적 페이스가 지연되고 있거나 ${targetEndText} 911점 도달에 주의가 요구됩니다.${
        worstYoY?.전년동월대비_증감 != null
          ? ` (${worstYoY.센터명} 센터 전년비 ${(worstYoY.전년동월대비_증감).toFixed(1)}점)`
          : ''
      } 해당 센터의 원활한 오더 처리를 위한 맞춤형 현장 지원이 권장됩니다.`,
      badge: `코칭 대상 ${lagCenters.length}개소`,
    });
  } else {
    insights.push({
      type: 'success',
      title: '전 센터 누적 오더 정상 진척',
      message: `모든 고객센터가 전년 동월 페이스를 상회하며 순조롭게 ${targetEndText} 911점 달성 궤도에 안착해 있습니다.`,
      badge: '전체 순항',
    });
  }

  // 5. 전년 반기말(6월말) 실적 연계 911점 도달 진단
  const prevHalfEndRecords = dfLatest.filter(r => r.전년반기말_총점 != null);
  if (prevHalfEndRecords.length > 0) {
    const prevEndAvg =
      prevHalfEndRecords.reduce((sum, r) => sum + (r.전년반기말_총점 || 0), 0) /
      prevHalfEndRecords.length;
    insights.push({
      type: 'info',
      title: `전년 ${targetEndText} 실적 연계 911점 도달 진단`,
      message: `전년도 ${targetEndText} 최종 실적(평균 ${prevEndAvg.toFixed(1)}점, 전 센터 911점 도달)을 벤치마크할 때, 현재 ${monthInHalf}개월차 추세 유지 시 센터별 평균 ${targetEndText} 예상 점수는 ${(
        dfLatest.reduce((s, r) => s + r.예상반기총점, 0) / totalCenters
      ).toFixed(1)}점으로 911점 목표선을 충분히 달성할 수 있습니다.`,
      badge: '반기말 벤치마크',
    });
  }

  return insights;
}
