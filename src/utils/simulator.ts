import { ScoredRecord } from '../types';
import { calcContractScore } from './scoreCalculator';

export interface SimulationResult {
  simulatedScore: number;
  gapToPass: number;
  isPassing: boolean;
  scoreDifferences: { [kpi: string]: number };
  recommendation: string;
}

export function runWhatIfSimulation(
  record: ScoredRecord,
  adjustments: {
    safetyRate: number;
    keyCustomerRate: number;
    contractRate: number;
    counselResponseRate: number;
    counselContribRate: number;
    satisfactionRate: number;
  }
): SimulationResult {
  const newSafetyScore = (adjustments.safetyRate / 100.0) * 550.0;
  const newKeyScore = (adjustments.keyCustomerRate / 100.0) * 100.0;
  const newContractScore = calcContractScore(adjustments.contractRate);
  const newResponseScore = (adjustments.counselResponseRate / 100.0) * 100.0;
  const newContribScore = (adjustments.counselContribRate / 100.0) * 100.0;
  const newSatisfactionScore = adjustments.satisfactionRate;

  const adj = (record.민원대응적정성 || 0) + (record.주의경고 || 0) + (record.가점 || 0);

  const simulatedTotal =
    newSafetyScore +
    newKeyScore +
    newContractScore +
    newResponseScore +
    newContribScore +
    newSatisfactionScore +
    adj;

  const gap = simulatedTotal - 911.0;
  const isPassing = gap >= 0;

  let recommendation = '';
  if (isPassing) {
    recommendation = `🎉 반기말 최종 합격선(911점)을 +${gap.toFixed(1)}점 상회합니다! 안전점검 및 중점안전점검 오더가 매월 정상 누적된다면 6월말 목표 달성이 유력합니다.`;
  } else {
    const needed = Math.abs(gap).toFixed(1);
    if (adjustments.safetyRate < 95) {
      recommendation = `⚠️ 6월말 911점 도달까지 ${needed}점이 부족합니다. 안전점검(550점)의 실점검율을 +${((Math.abs(gap) / 550) * 100).toFixed(1)}%p 더 달성할 수 있도록 점검 오더 처리 페이스를 보강해야 합니다.`;
    } else {
      recommendation = `⚠️ 6월말 911점 도달까지 ${needed}점이 부족합니다. 안전점검 외에 상담응대율이나 사용계약율 등 보조 지표(350점)의 집중 보강 관리가 필요합니다.`;
    }
  }

  return {
    simulatedScore: simulatedTotal,
    gapToPass: gap,
    isPassing,
    scoreDifferences: {
      안전점검: newSafetyScore - record.안전점검_점수,
      중점고객: newKeyScore - record.중점고객_점수,
      사용계약: newContractScore - record.사용계약_점수,
      상담응대: newResponseScore - record.상담응대_점수,
      상담기여: newContribScore - record.상담기여_점수,
      만족도: newSatisfactionScore - record.만족도_점수,
    },
    recommendation,
  };
}
