import React, { useState, useMemo } from 'react';
import { ScoredRecord } from '../../types';

interface HeatmapPageProps {
  df: ScoredRecord[];
  dfLatest: ScoredRecord[];
}

const KPIS = [
  { key: '안전점검_달성률', label: '안전점검 (550)', isCumulative: true },
  { key: '중점고객_달성률', label: '중점고객 (100)', isCumulative: true },
  { key: '사용계약_달성률', label: '사용계약 (50)', isCumulative: false },
  { key: '상담응대_달성률', label: '상담응대 (100)', isCumulative: false },
  { key: '상담기여_달성률', label: '상담기여 (100)', isCumulative: false },
  { key: '만족도_달성률', label: '만족도 (100)', isCumulative: false },
];

function getRateColor(rate: number, isCumulative: boolean = false, monthInHalf: number = 6): { bg: string; text: string; grade: string } {
  let effectiveRate = rate;
  if (isCumulative && monthInHalf < 6) {
    const pace = Math.max(0.1, monthInHalf / 6.0);
    effectiveRate = (rate / pace);
  }
  if (effectiveRate >= 95) return { bg: '#178A5B', text: '#FFFFFF', grade: 'S' };
  if (effectiveRate >= 90) return { bg: '#84CC16', text: '#1E293B', grade: 'A' };
  if (effectiveRate >= 85) return { bg: '#F59E0B', text: '#1E293B', grade: 'B' };
  if (effectiveRate >= 75) return { bg: '#E66A1F', text: '#FFFFFF', grade: 'C' };
  return { bg: '#D92D20', text: '#FFFFFF', grade: 'D' };
}

function getScoreColorStyle(score: number, monthStr: string = ''): { bg: string; text: string } {
  const parts = monthStr.split('-');
  const m = parseInt(parts[1], 10) || 6;
  const monthInHalf = m <= 6 ? m : m - 6;

  // 반기 중간 월(1~5개월차)의 경우 누적 페이스로 정규화 평가
  let evalScore = score;
  if (monthInHalf < 6) {
    // 0점 시작 누적 체계: 기대 페이스(m/6) 감안 정규화
    const expectedBase = (monthInHalf / 6.0) * 600.0 + 340.0;
    const diff = score - expectedBase;
    if (diff >= 15) return { bg: '#15803D', text: '#FFFFFF' };
    if (diff >= 0) return { bg: '#178A5B', text: '#FFFFFF' };
    if (diff >= -15) return { bg: '#F59E0B', text: '#1E293B' };
    if (diff >= -30) return { bg: '#E66A1F', text: '#FFFFFF' };
    return { bg: '#D92D20', text: '#FFFFFF' };
  }

  if (evalScore >= 930) return { bg: '#15803D', text: '#FFFFFF' };
  if (evalScore >= 911) return { bg: '#178A5B', text: '#FFFFFF' };
  if (evalScore >= 895) return { bg: '#F59E0B', text: '#1E293B' };
  if (evalScore >= 870) return { bg: '#E66A1F', text: '#FFFFFF' };
  return { bg: '#D92D20', text: '#FFFFFF' };
}


export const HeatmapPage: React.FC<HeatmapPageProps> = ({ df, dfLatest }) => {
  const [activeTab, setActiveTab] = useState<'kpi' | 'monthly' | 'kpiAvg'>('kpi');

  const allMonths = useMemo(() => {
    return Array.from(new Set(df.map(r => String(r.평가월 || '').substring(0, 7)))).sort();
  }, [df]);

  const centers = useMemo(() => {
    return Array.from(new Set(dfLatest.map(r => r.센터명))).sort();
  }, [dfLatest]);

  const centerMonthMap = useMemo(() => {
    const map = new Map<string, number>();
    df.forEach(r => {
      map.set(`${r.센터명}_${String(r.평가월 || '').substring(0, 7)}`, r.총점);
    });
    return map;
  }, [df]);

  const monthKpiAvg = useMemo(() => {
    return allMonths.map(month => {
      const records = df.filter(r => String(r.평가월 || '').startsWith(month));
      const count = records.length;
      if (count === 0) return { month, count: 0 };

      return {
        month,
        count,
        총점: records.reduce((s, r) => s + r.총점, 0) / count,
        안전점검: records.reduce((s, r) => s + r.안전점검_달성률, 0) / count,
        중점고객: records.reduce((s, r) => s + r.중점고객_달성률, 0) / count,
        사용계약: records.reduce((s, r) => s + r.사용계약_달성률, 0) / count,
        상담응대: records.reduce((s, r) => s + r.상담응대_달성률, 0) / count,
        상담기여: records.reduce((s, r) => s + r.상담기여_달성률, 0) / count,
        만족도: records.reduce((s, r) => s + r.만족도_달성률, 0) / count,
      };
    });
  }, [df, allMonths]);

  return (
    <div className="space-y-6" id="heatmap-page-container">
      {/* Tabs */}
      <div className="flex border-b border-[#DCE3EA]">
        <button
          onClick={() => setActiveTab('kpi')}
          className={`py-2.5 px-5 font-bold text-sm border-b-2 transition-colors cursor-pointer ${
            activeTab === 'kpi'
              ? 'border-[#0B4EA2] text-[#0B4EA2]'
              : 'border-transparent text-[#5E6C84] hover:text-[#172B4D]'
          }`}
        >
          Tab 1 - 센터 × KPI 달성률 (최신월)
        </button>
        <button
          onClick={() => setActiveTab('monthly')}
          className={`py-2.5 px-5 font-bold text-sm border-b-2 transition-colors cursor-pointer ${
            activeTab === 'monthly'
              ? 'border-[#0B4EA2] text-[#0B4EA2]'
              : 'border-transparent text-[#5E6C84] hover:text-[#172B4D]'
          }`}
        >
          Tab 2 - 센터 × 월별 총점 (전체 월 추이)
        </button>
        <button
          onClick={() => setActiveTab('kpiAvg')}
          className={`py-2.5 px-5 font-bold text-sm border-b-2 transition-colors cursor-pointer ${
            activeTab === 'kpiAvg'
              ? 'border-[#0B4EA2] text-[#0B4EA2]'
              : 'border-transparent text-[#5E6C84] hover:text-[#172B4D]'
          }`}
        >
          Tab 3 - 월별 KPI 평균 (전체 센터)
        </button>
      </div>

      {/* Legend Bar */}
      <div className="bg-white p-3 rounded-lg border border-[#DCE3EA] flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="font-bold text-[#172B4D]">색상 기준:</div>
        {activeTab === 'kpi' || activeTab === 'kpiAvg' ? (
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#178A5B' }}></span> S (95%+)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#84CC16' }}></span> A (90~94%)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#F59E0B' }}></span> B (85~89%)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#E66A1F' }}></span> C (75~84%)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#D92D20' }}></span> D (&lt;75%)</span>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#15803D' }}></span> 930점+</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#178A5B' }}></span> 911~929점</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#F59E0B' }}></span> 895~910점 (주의)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#E66A1F' }}></span> 870~894점 (경고)</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded" style={{ backgroundColor: '#D92D20' }}></span> 870점 미만 (위험)</span>
          </div>
        )}
      </div>

      {/* Tab 1: Center x KPI */}
      {activeTab === 'kpi' && (
        <div className="bg-white rounded-lg border border-[#DCE3EA] p-4 shadow-xs overflow-x-auto">
          <table className="w-full text-xs text-center border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] text-[#5E6C84] border-b border-[#DCE3EA]">
                <th className="py-2.5 px-3 text-left">센터명</th>
                {KPIS.map(kpi => (
                  <th key={kpi.key} className="py-2.5 px-3 font-semibold">{kpi.label}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF2F6]">
              {dfLatest.map(r => (
                <tr key={r.센터명} className="hover:bg-slate-50">
                  <td className="py-2 px-3 text-left font-bold text-[#172B4D]">{r.센터명}</td>
                  {KPIS.map(kpi => {
                    const rate = (r as any)[kpi.key] || 0;
                    const m = r.월 || 2;
                    const monthInHalf = m <= 6 ? m : m - 6;
                    const style = getRateColor(rate, kpi.isCumulative, monthInHalf);
                    return (
                      <td key={kpi.key} className="p-1">
                        <div
                          className="py-1.5 px-2 rounded font-bold text-xs"
                          style={{ backgroundColor: style.bg, color: style.text }}
                          title={`${kpi.label}: ${rate.toFixed(1)}% (${style.grade}등급)`}
                        >
                          {rate.toFixed(1)}%
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Center x Month */}
      {activeTab === 'monthly' && (
        <div className="bg-white rounded-lg border border-[#DCE3EA] p-4 shadow-xs overflow-x-auto">
          <table className="w-full text-xs text-center border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] text-[#5E6C84] border-b border-[#DCE3EA]">
                <th className="py-2.5 px-3 text-left">센터명</th>
                {allMonths.map(month => (
                  <th key={month} className="py-2.5 px-3 font-semibold">{month}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF2F6]">
              {centers.map(center => (
                <tr key={center} className="hover:bg-slate-50">
                  <td className="py-2 px-3 text-left font-bold text-[#172B4D]">{center}</td>
                  {allMonths.map(month => {
                    const score = centerMonthMap.get(`${center}_${month}`);
                    if (score === undefined) {
                      return <td key={month} className="p-1 text-gray-300">-</td>;
                    }
                    const style = getScoreColorStyle(score, month);
                    return (
                      <td key={month} className="p-1">
                        <div
                          className="py-1.5 px-2 rounded font-bold text-xs"
                          style={{ backgroundColor: style.bg, color: style.text }}
                          title={`${center} (${month}): ${score.toFixed(1)}점`}
                        >
                          {score.toFixed(0)}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Monthly KPI Average */}
      {activeTab === 'kpiAvg' && (
        <div className="bg-white rounded-lg border border-[#DCE3EA] p-4 shadow-xs overflow-x-auto">
          <table className="w-full text-xs text-center border-collapse">
            <thead>
              <tr className="bg-[#F8FAFC] text-[#5E6C84] border-b border-[#DCE3EA]">
                <th className="py-2.5 px-3 text-left">평가월</th>
                <th className="py-2.5 px-3">대상 센터 수</th>
                <th className="py-2.5 px-3">전체 평균 총점</th>
                <th className="py-2.5 px-3">안전점검 달성률</th>
                <th className="py-2.5 px-3">중점고객 달성률</th>
                <th className="py-2.5 px-3">사용계약 달성률</th>
                <th className="py-2.5 px-3">상담응대 달성률</th>
                <th className="py-2.5 px-3">상담기여 달성률</th>
                <th className="py-2.5 px-3">만족도 달성률</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF2F6]">
              {monthKpiAvg.map(item => (
                <tr key={item.month} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 text-left font-bold text-[#172B4D]">{item.month}</td>
                  <td className="py-2.5 px-3 text-gray-600">{item.count}개소</td>
                  <td className="py-2.5 px-3 font-bold text-[#0B4EA2]">{item.총점 ? item.총점.toFixed(1) : '-'}점</td>
                  {['안전점검', '중점고객', '사용계약', '상담응대', '상담기여', '만족도'].map(kpi => {
                    const rate = (item as any)[kpi] || 0;
                    const style = getRateColor(rate);
                    return (
                      <td key={kpi} className="p-1.5">
                        <div
                          className="py-1 px-2 rounded font-bold text-xs"
                          style={{ backgroundColor: style.bg, color: style.text }}
                        >
                          {rate.toFixed(1)}%
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
