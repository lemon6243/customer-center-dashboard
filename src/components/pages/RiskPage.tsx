import React, { useMemo } from 'react';
import { ScoredRecord, PeriodInfo } from '../../types';

interface RiskPageProps {
  dfLatest: ScoredRecord[];
  periodInfo: PeriodInfo;
}

export const RiskPage: React.FC<RiskPageProps> = ({ dfLatest, periodInfo }) => {
  const monthInHalf = periodInfo.month_in_half || (periodInfo.current_month <= 6 ? periodInfo.current_month : periodInfo.current_month - 6);
  const targetEndText = periodInfo.target_half_end_text || (periodInfo.current_month <= 6 ? '6월말' : '12월말');

  // 위험 진단 그룹 분류:
  // 1. 고위험 미달 예상: 6월말 예상 < 911점 또는 전년 동월 대비 심각한 오더 지연(YoY < -15점)
  const highRiskCenters = useMemo(() => {
    return dfLatest.filter(
      r => r.예상반기총점 < 911.0 || (r.전년동월대비_증감 != null && r.전년동월대비_증감 < -20.0)
    );
  }, [dfLatest]);

  // 2. 주의 / 911점 근접 관리: 예상 911 ~ 930점 사이 또는 오더 진척 지연
  const warningCenters = useMemo(() => {
    return dfLatest.filter(
      r =>
        !highRiskCenters.includes(r) &&
        (r.예상반기총점 < 930.0 || r.오더진척상태 === '지연' || (r.전년동월대비_증감 != null && r.전년동월대비_증감 < -5.0))
    );
  }, [dfLatest, highRiskCenters]);

  // 3. 안정 / 911점 달성 유력
  const safeCenters = useMemo(() => {
    return dfLatest.filter(r => !highRiskCenters.includes(r) && !warningCenters.includes(r));
  }, [dfLatest, highRiskCenters, warningCenters]);

  return (
    <div className="space-y-6" id="risk-page-container">
      {/* Alert Top Banner */}
      <div className="bg-white border-l-4 border-[#0B4EA2] rounded-xl p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-[#172B4D] flex items-center gap-2">
            <span>⚠️</span> {targetEndText} 911점 도달 궤도 및 누적 오더 진척 위험 진단
          </h3>
          <p className="text-xs text-[#5E6C84] mt-1.5 leading-relaxed">
            현재 <strong>{monthInHalf}개월차 기준 평균 실점검율</strong>은 계획 대비 양호한 수준을 유지하고 있습니다.<br />
            고객센터 종합 평가는 단순 현재 점수가 아닌 <strong>'전년 동월 대비 진척도'</strong> 및 <strong>'전년 반기말 실적 대비 {targetEndText} 911점 도달 가능성'</strong>을 기준으로 선제적 코칭 및 지원 대상 센터를 정밀 진단합니다.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
            집중 코칭 대상: {highRiskCenters.length + warningCenters.length}개소
          </span>
          <span className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
            정상 궤도: {safeCenters.length}개소
          </span>
        </div>
      </div>

      {/* 3 Categories Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* High Risk (< 911 or Severe Lag) */}
        <div className="bg-white rounded-xl border border-red-200 shadow-xs p-5 space-y-4" style={{ borderTop: '4px solid #D92D20' }}>
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-sm text-[#D92D20] flex items-center gap-1.5">
              <span>🚨</span> {targetEndText} 911점 미달 위험 ({highRiskCenters.length}개소)
            </h4>
            <span className="text-[11px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200">
              긴급 오더 보강
            </span>
          </div>
          <p className="text-xs text-slate-500">
            전년 동월 대비 누적 오더 처리가 크게 지연되어, 잔여 기간 특단의 안전점검 보강이 필요한 센터입니다.
          </p>

          <div className="space-y-3">
            {highRiskCenters.length === 0 ? (
              <div className="text-xs text-gray-400 py-6 text-center">해당 위험 센터가 없습니다. 전 센터 정상 진척 중입니다.</div>
            ) : (
              highRiskCenters.map(r => (
                <div key={r.센터명} className="p-3 bg-red-50/70 border border-red-200 rounded-lg space-y-1.5 text-xs">
                  <div className="flex justify-between font-bold">
                    <span className="text-slate-800 text-sm">{r.센터명} 센터</span>
                    <span className="text-red-700 font-extrabold">{targetEndText} 예상 {r.예상반기총점.toFixed(1)}점</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-600 py-1 border-y border-red-100">
                    <div>현재 총점: <span className="font-semibold text-slate-800">{r.총점.toFixed(1)}점</span></div>
                    <div>안전점검율: <span className="font-semibold text-slate-800">{r.안전점검_달성률.toFixed(1)}%</span></div>
                    <div>전년 동월 대비: <span className={`font-semibold ${r.전년동월대비_증감 && r.전년동월대비_증감 < 0 ? 'text-red-700' : 'text-emerald-700'}`}>
                      {r.전년동월대비_증감 != null ? `${r.전년동월대비_증감 >= 0 ? '+' : ''}${r.전년동월대비_증감.toFixed(1)}점` : '자료없음'}
                    </span></div>
                    <div>전년 {targetEndText}: <span className="font-semibold text-slate-800">{r.전년반기말_총점 != null ? `${r.전년반기말_총점.toFixed(1)}점` : '-'}</span></div>
                  </div>
                  <div className="text-[11.5px] text-red-900 font-medium pt-1">
                    👉 <strong>처방 의견:</strong> 911점 달성까지 예상 {(911 - r.예상반기총점).toFixed(1)}점 부족. 매월 안전점검 오더 건수 +100건 이상 집중 처리 긴급 코칭 필요.
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Warning / Near Target */}
        <div className="bg-white rounded-xl border border-amber-200 shadow-xs p-5 space-y-4" style={{ borderTop: '4px solid #D48A00' }}>
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-sm text-[#D48A00] flex items-center gap-1.5">
              <span>⚠️</span> 주의 / 집중 코칭 대상 ({warningCenters.length}개소)
            </h4>
            <span className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              오더 페이스 관리
            </span>
          </div>
          <p className="text-xs text-slate-500">
            현재 911점 경계선에 위치하거나 전년비 소폭 지연되어, 월별 오더 누적 속도 유지가 필요한 센터입니다.
          </p>

          <div className="space-y-3">
            {warningCenters.length === 0 ? (
              <div className="text-xs text-gray-400 py-6 text-center">해당 주의 센터가 없습니다.</div>
            ) : (
              warningCenters.map(r => (
                <div key={r.센터명} className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg space-y-1.5 text-xs">
                  <div className="flex justify-between font-bold">
                    <span className="text-slate-800 text-sm">{r.센터명} 센터</span>
                    <span className="text-amber-800 font-extrabold">{targetEndText} 예상 {r.예상반기총점.toFixed(1)}점</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-600 py-1 border-y border-amber-100">
                    <div>현재 총점: <span className="font-semibold text-slate-800">{r.총점.toFixed(1)}점</span></div>
                    <div>안전점검율: <span className="font-semibold text-slate-800">{r.안전점검_달성률.toFixed(1)}%</span></div>
                    <div>전년 동월 대비: <span className={`font-semibold ${r.전년동월대비_증감 && r.전년동월대비_증감 < 0 ? 'text-amber-800' : 'text-emerald-700'}`}>
                      {r.전년동월대비_증감 != null ? `${r.전년동월대비_증감 >= 0 ? '+' : ''}${r.전년동월대비_증감.toFixed(1)}점` : '자료없음'}
                    </span></div>
                    <div>전년 {targetEndText}: <span className="font-semibold text-slate-800">{r.전년반기말_총점 != null ? `${r.전년반기말_총점.toFixed(1)}점` : '-'}</span></div>
                  </div>
                  <div className="text-[11.5px] text-amber-950 font-medium pt-1">
                    👉 <strong>처방 의견:</strong> 월별 오더 처리 누적 페이스를 상시 모니터링하여 {targetEndText} 911점 합격선 안정적 수성 유도.
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Safe (On-track) */}
        <div className="bg-white rounded-xl border border-emerald-200 shadow-xs p-5 space-y-4" style={{ borderTop: '4px solid #178A5B' }}>
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-sm text-[#178A5B] flex items-center gap-1.5">
              <span>✅</span> 안정 / 911점 달성 유력 ({safeCenters.length}개소)
            </h4>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              우수 누적 궤도
            </span>
          </div>
          <p className="text-xs text-slate-500">
            전년 동월을 상회하는 견고한 오더 누적 속도로 {targetEndText} 911점을 무난히 초과 달성할 것으로 예상됩니다.
          </p>

          <div className="space-y-3">
            {safeCenters.map(r => (
              <div key={r.센터명} className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg space-y-1 text-xs">
                <div className="flex justify-between font-bold">
                  <span className="text-slate-800 font-semibold">{r.센터명} 센터</span>
                  <span className="text-emerald-800 font-bold">{targetEndText} 예상 {r.예상반기총점.toFixed(1)}점</span>
                </div>
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>현재: {r.총점.toFixed(1)}점 (안전: {r.안전점검_달성률.toFixed(0)}%)</span>
                  <span className="text-emerald-700 font-medium">
                    {r.전년동월대비_증감 != null ? `YoY ${r.전년동월대비_증감 >= 0 ? '+' : ''}${r.전년동월대비_증감.toFixed(1)}점` : '순항'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
