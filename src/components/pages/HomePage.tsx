import React, { useMemo } from 'react';
import { ScoredRecord, PeriodInfo, PageKey } from '../../types';
import { MetricCard } from '../MetricCards';
import { Colors } from '../../utils/styles';
import { generateAutomatedInsights } from '../../utils/insights';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';

interface HomePageProps {
  dfLatest: ScoredRecord[];
  dfPrev: ScoredRecord[];
  periodInfo: PeriodInfo;
  onNavigate: (page: PageKey) => void;
  dfAll?: ScoredRecord[];
}

export const HomePage: React.FC<HomePageProps> = ({
  dfLatest,
  dfPrev,
  periodInfo,
  onNavigate,
  dfAll,
}) => {
  const totalCenters = dfLatest.length;
  const monthInHalf = periodInfo.month_in_half || (periodInfo.current_month <= 6 ? periodInfo.current_month : periodInfo.current_month - 6);
  const targetEndText = periodInfo.target_half_end_text || (periodInfo.current_month <= 6 ? '6월말' : '12월말');

  const avgScore = totalCenters > 0
    ? dfLatest.reduce((sum, r) => sum + r.총점, 0) / totalCenters
    : 0;

  // 전년 동월 평균 산출
  const yoyValidRecords = dfLatest.filter(r => r.전년동월_총점 != null);
  const prevYearAvg = yoyValidRecords.length > 0
    ? yoyValidRecords.reduce((sum, r) => sum + (r.전년동월_총점 || 0), 0) / yoyValidRecords.length
    : null;
  const yoyDiff = prevYearAvg != null ? avgScore - prevYearAvg : null;

  // 6월말 911점 도달 정상 궤도(On-track) 산출
  const onTrackCenters = dfLatest.filter(r => r.예상반기총점 >= 911.0);
  const onTrackCount = onTrackCenters.length;
  const onTrackRate = totalCenters > 0 ? ((onTrackCount / totalCenters) * 100).toFixed(1) : '0';

  // 누적 지연 / 중점 코칭 센터
  const lagCenters = dfLatest.filter(
    r =>
      (r.전년동월대비_증감 != null && r.전년동월대비_증감 < -10.0) ||
      r.예상반기총점 < 905.0 ||
      r.오더진척상태 === '지연'
  );

  // 안전점검 실점검율 (오더 누적형: 550점 만점)
  const avgSafetyRate = totalCenters > 0
    ? dfLatest.reduce((sum, r) => sum + r.안전점검_달성률, 0) / totalCenters
    : 0;
  const benchmarkSafety = (monthInHalf / 6.0) * 92.0;
  const safetyDiff = avgSafetyRate - benchmarkSafety;

  const sortedByScore = useMemo(() => {
    return [...dfLatest].sort((a, b) => b.총점 - a.총점);
  }, [dfLatest]);

  const top3 = sortedByScore.slice(0, 3);
  const bottom3 = sortedByScore.slice(-3).reverse();

  const insights = useMemo(() => {
    return generateAutomatedInsights(dfLatest, dfPrev, periodInfo, dfAll);
  }, [dfLatest, dfPrev, periodInfo, dfAll]);

  // 차트 dynamic domain 계산
  const { minVal, maxVal } = useMemo(() => {
    if (dfLatest.length === 0) return { minVal: 0, maxVal: 1000 };
    const scores = dfLatest.map(r => r.총점);
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    return {
      minVal: Math.max(0, Math.floor((min - 30) / 50) * 50),
      maxVal: Math.min(1000, Math.ceil((max + 30) / 50) * 50),
    };
  }, [dfLatest]);

  return (
    <div className="space-y-6" id="home-page-container">
      {/* 누적 구조 설명 알림 배너 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50/40 border border-blue-200/80 rounded-xl p-4 shadow-2xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div>
            <h4 className="text-xs font-bold text-[#0B4EA2] tracking-tight">
              고객센터 종합 진단 현황 ({monthInHalf}개월차)
            </h4>
            <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
              현재 <strong>{monthInHalf}개월차 기준 평균 실점검율은 {avgSafetyRate.toFixed(1)}%</strong>입니다. 계획 대비 양호하게 추진 중이며, 전년 동월 및 <strong>{targetEndText} 911점 달성 목표선</strong>을 기준으로 센터별 진척 페이스를 종합 모니터링하고 있습니다.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold px-3 py-1 bg-white border border-blue-200 text-[#0B4EA2] rounded-full shadow-2xs">
            {periodInfo.half} {monthInHalf}/6개월차 ({(periodInfo.progress_rate * 100).toFixed(0)}% 진척)
          </span>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="전체 센터 평균 총점"
          value={`${avgScore.toFixed(1)}점`}
          subValue={
            prevYearAvg != null
              ? `전년 동월(${prevYearAvg.toFixed(1)}점) 대비 ${yoyDiff! >= 0 ? '+' : ''}${yoyDiff!.toFixed(1)}점`
              : `${periodInfo.half} ${monthInHalf}개월차`
          }
          status={yoyDiff != null ? (yoyDiff >= 0 ? 'success' : 'warning') : 'info'}
          colorBorder={Colors.PRIMARY}
          icon="📊"
        />
        <MetricCard
          label={`${targetEndText} 911점 예상 달성률`}
          value={`${onTrackRate}%`}
          subValue={`총 ${totalCenters}개소 중 ${onTrackCount}개소 정상 궤도`}
          status={Number(onTrackRate) >= 70 ? 'success' : 'warning'}
          colorBorder={Colors.SUCCESS}
          icon="🎯"
        />
        <MetricCard
          label="누적 지연 / 중점 코칭 센터"
          value={`${lagCenters.length}개소`}
          subValue="전년비 지연 및 911점 미달 위험"
          status={lagCenters.length > 0 ? 'warning' : 'success'}
          colorBorder={Colors.WARNING}
          icon="⚠️"
        />
        <MetricCard
          label="안전점검 평균 실점검율"
          value={`${avgSafetyRate.toFixed(1)}%`}
          subValue={`계획(${benchmarkSafety.toFixed(1)}%) 대비 ${safetyDiff >= -3 ? '양호' : '관리 필요'}`}
          status={safetyDiff >= -3 ? 'success' : 'warning'}
          colorBorder="#0B4EA2"
          icon="⏱️"
        />
      </div>

      {/* Automated Realtime Insights Section */}
      <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#172B4D] flex items-center gap-2">
            <span>💡</span> 핵심 인사이트 및 자동 진단
          </h3>
          <span className="text-xs text-[#5E6C84] bg-slate-100 px-2.5 py-0.5 rounded-full font-semibold">
            전년 동월 및 {targetEndText} 벤치마크 연계
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {insights.map((item, idx) => {
            const bgClass =
              item.type === 'danger'
                ? 'bg-red-50/70 border-red-200 text-red-900'
                : item.type === 'warning'
                ? 'bg-amber-50/70 border-amber-200 text-amber-900'
                : item.type === 'success'
                ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                : 'bg-blue-50/70 border-blue-200 text-blue-900';

            return (
              <div key={idx} className={`p-3.5 rounded-lg border ${bgClass} text-xs space-y-1.5 flex flex-col justify-between`}>
                <div>
                  <div className="flex items-center justify-between font-bold mb-1">
                    <span className="text-[13px]">{item.title}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-white/80 font-bold border border-current/20">
                      {item.badge}
                    </span>
                  </div>
                  <p className="text-[11.5px] leading-relaxed opacity-95">{item.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Chart & Rankings Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Distribution Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-[#172B4D]">
                  전체 센터 누적 총점 분포 및 {targetEndText} 도달 궤도
                </h3>
                <p className="text-[11px] text-[#5E6C84] mt-0.5">
                  막대 색상: 🔵 정상 궤도(915점 이상 예상) | 🟠 주의(905~914점 예상) | 🔴 위험/지연(905점 미만)
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 rounded text-slate-700">
                {periodInfo.year}년 {periodInfo.current_month}월 ({monthInHalf}개월차)
              </span>
            </div>
            <div className="h-68 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sortedByScore} margin={{ top: 15, right: 10, left: -20, bottom: 25 }}>
                  <XAxis dataKey="센터명" tick={{ fontSize: 10 }} interval={0} angle={-35} textAnchor="end" />
                  <YAxis domain={[minVal, maxVal]} tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(val: any, name: any, item: any) => {
                      const r = item.payload as ScoredRecord;
                      return [
                        `${Number(val).toFixed(1)}점 (예상: ${r.예상반기총점.toFixed(1)}점 | 전년비: ${
                          r.전년동월대비_증감 != null ? (r.전년동월대비_증감 >= 0 ? '+' : '') + r.전년동월대비_증감.toFixed(1) + '점' : '-'
                        })`,
                        '총점',
                      ];
                    }}
                    labelFormatter={(label) => `센터: ${label}`}
                  />
                  <ReferenceLine
                    y={avgScore}
                    stroke="#0B4EA2"
                    strokeDasharray="3 3"
                    label={{ value: `당월평균 (${avgScore.toFixed(1)})`, fill: '#0B4EA2', fontSize: 10, position: 'top' }}
                  />
                  {prevYearAvg != null && (
                    <ReferenceLine
                      y={prevYearAvg}
                      stroke="#8E44AD"
                      strokeDasharray="4 2"
                      label={{ value: `전년동월 (${prevYearAvg.toFixed(1)})`, fill: '#8E44AD', fontSize: 10, position: 'bottom' }}
                    />
                  )}
                  {monthInHalf >= 5 && (
                    <ReferenceLine
                      y={911}
                      stroke="#178A5B"
                      strokeDasharray="2 2"
                      label={{ value: '최종목표 (911)', fill: '#178A5B', fontSize: 10, position: 'top' }}
                    />
                  )}
                  <Bar dataKey="총점" radius={[3, 3, 0, 0]}>
                    {sortedByScore.map((entry) => {
                      const isDanger = entry.도달판정 === '위험' || entry.예상반기총점 < 905;
                      const isWarning = entry.도달판정 === '주의' || (entry.예상반기총점 >= 905 && entry.예상반기총점 < 915);
                      return (
                        <Cell
                          key={`cell-${entry.센터명}`}
                          fill={isDanger ? '#D92D20' : isWarning ? '#D48A00' : '#0B4EA2'}
                        />
                      );
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Top / Bottom Rankings */}
        <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-bold text-[#172B4D] mb-3 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span>🏆</span> 센터별 성과 및 전년비 증감
              </span>
              <span className="text-[11px] text-slate-500 font-normal">누적 순위</span>
            </h3>

            {/* Top 3 */}
            <div className="space-y-2 mb-4">
              <div className="text-xs font-bold text-[#178A5B] flex items-center justify-between">
                <span>▲ 상위 우수 센터 (Top 3)</span>
                <span className="text-[10px] text-slate-500 font-normal">전년 동월 대비</span>
              </div>
              {top3.map((r, i) => (
                <div key={r.센터명} className="flex items-center justify-between p-2 rounded bg-emerald-50/50 border border-emerald-100 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-4 text-center font-bold text-emerald-800">{i + 1}</span>
                    <span className="font-semibold text-slate-800">{r.센터명}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-[#178A5B]">{r.총점.toFixed(1)}점</div>
                    <div className="text-[10px] text-emerald-700">
                      {r.전년동월대비_증감 != null ? `YoY ${r.전년동월대비_증감 >= 0 ? '+' : ''}${r.전년동월대비_증감.toFixed(1)}` : `안전: ${r.안전점검_달성률.toFixed(0)}%`}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Bottom 3 */}
            <div className="space-y-2">
              <div className="text-xs font-bold text-[#D48A00] flex items-center justify-between">
                <span>▼ 코칭 집중 관리 센터 (Bottom 3)</span>
                <span className="text-[10px] text-slate-500 font-normal">오더 보강 대상</span>
              </div>
              {bottom3.map((r, i) => (
                <div key={r.센터명} className="flex items-center justify-between p-2 rounded bg-amber-50/50 border border-amber-100 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-4 text-center font-bold text-amber-800">{totalCenters - i}</span>
                    <span className="font-semibold text-slate-800">{r.센터명}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-[#D48A00]">{r.총점.toFixed(1)}점</div>
                    <div className="text-[10px] text-amber-800">
                      {r.전년동월대비_증감 != null ? `YoY ${r.전년동월대비_증감 >= 0 ? '+' : ''}${r.전년동월대비_증감.toFixed(1)}` : `안전: ${r.안전점검_달성률.toFixed(0)}%`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Nav Buttons */}
          <div className="pt-2 border-t border-slate-100 flex gap-2">
            <button
              onClick={() => onNavigate('📊 성과 분석')}
              className="flex-1 py-2 px-3 bg-[#0B4EA2] hover:bg-[#073A7A] text-white rounded-lg text-xs font-bold transition-colors cursor-pointer text-center"
            >
              📊 전체 성과 분석
            </button>
            <button
              onClick={() => onNavigate('🎯 센터 진단')}
              className="flex-1 py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-colors cursor-pointer text-center"
            >
              🎯 센터 상세 진단
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
