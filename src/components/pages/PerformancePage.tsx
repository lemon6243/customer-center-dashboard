import React, { useState, useMemo } from 'react';
import { ScoredRecord, PeriodInfo } from '../../types';
import { ScoreThresholds, getScoreBadge } from '../../utils/styles';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface PerformancePageProps {
  df: ScoredRecord[];
  dfLatest: ScoredRecord[];
  periodInfo: PeriodInfo;
}

export const PerformancePage: React.FC<PerformancePageProps> = ({
  df,
  dfLatest,
  periodInfo,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<'총점' | '센터명' | '안전점검_달성률'>('총점');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedCenterForTrend, setSelectedCenterForTrend] = useState<string>('전체평균');

  const filteredRecords = useMemo(() => {
    return dfLatest.filter(r => r.센터명.includes(searchTerm));
  }, [dfLatest, searchTerm]);

  const sortedRecords = useMemo(() => {
    return [...filteredRecords].sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];
      if (typeof valA === 'string') {
        return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortOrder === 'asc' ? valA - valB : valB - valA;
    });
  }, [filteredRecords, sortField, sortOrder]);

  const allMonths = useMemo(() => {
    return Array.from(new Set(df.map(r => String(r.평가월 || '').substring(0, 7)))).sort();
  }, [df]);

  const trendData = useMemo(() => {
    return allMonths.map(month => {
      const monthRecords = df.filter(r => String(r.평가월 || '').startsWith(month));
      const count = monthRecords.length;
      if (count === 0) return { month, score: null, avgScore: null };

      const avg = monthRecords.reduce((s, r) => s + r.총점, 0) / count;

      if (selectedCenterForTrend === '전체평균') {
        return {
          month,
          '전체평균': Math.round(avg * 10) / 10,
        };
      } else {
        const centerRec = monthRecords.find(r => r.센터명 === selectedCenterForTrend);
        return {
          month,
          '센터점수': centerRec ? Math.round(centerRec.총점 * 10) / 10 : null,
          '전체평균': Math.round(avg * 10) / 10,
        };
      }
    });
  }, [df, allMonths, selectedCenterForTrend]);

  const centerList = useMemo(() => {
    return ['전체평균', ...Array.from(new Set(dfLatest.map(r => r.센터명))).sort()];
  }, [dfLatest]);

  return (
    <div className="space-y-6" id="performance-page-container">
      {/* Monthly Trend Section */}
      <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-[#172B4D]">
              📈 센터별 월별 총점 추이 그래프
            </h3>
            <p className="text-xs text-[#5E6C84]">전체 평균 및 개별 센터의 월별 성과 궤적 비교</p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold text-[#5E6C84]">비교 센터:</span>
            <select
              value={selectedCenterForTrend}
              onChange={e => setSelectedCenterForTrend(e.target.value)}
              className="px-3 py-1.5 border border-[#DCE3EA] rounded-md bg-white text-[#172B4D] focus:outline-none focus:border-[#0B4EA2]"
            >
              {centerList.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis domain={[820, 960]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line
                type="monotone"
                dataKey="전체평균"
                stroke="#64748B"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={{ r: 3 }}
              />
              {selectedCenterForTrend !== '전체평균' && (
                <Line
                  type="monotone"
                  dataKey="센터점수"
                  stroke="#0B4EA2"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Center Table */}
      <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-[#172B4D]">
              📋 {periodInfo.year}년 {periodInfo.current_month}월 고객센터별 종합 평가표
            </h3>
            <p className="text-xs text-[#5E6C84]">전체 20개 센터 실적 데이터 및 6대 KPI 달성 현황</p>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="센터명 검색..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="px-3 py-1.5 text-xs border border-[#DCE3EA] rounded-md focus:outline-none focus:border-[#0B4EA2]"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#F8FAFC] text-[#5E6C84] border-y border-[#DCE3EA]">
              <tr>
                <th className="py-2.5 px-3">순위</th>
                <th className="py-2.5 px-3 font-semibold">센터명</th>
                <th className="py-2.5 px-3 text-right font-semibold">총점</th>
                <th className="py-2.5 px-3 text-center">상태</th>
                <th className="py-2.5 px-3 text-right">안전점검 (550)</th>
                <th className="py-2.5 px-3 text-right">중점고객 (100)</th>
                <th className="py-2.5 px-3 text-right">사용계약 (50)</th>
                <th className="py-2.5 px-3 text-right">상담응대 (100)</th>
                <th className="py-2.5 px-3 text-right">상담기여 (100)</th>
                <th className="py-2.5 px-3 text-right">만족도 (100)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF2F6]">
              {sortedRecords.map((r, i) => {
                const isInterim = periodInfo.month_in_half < 6;
                const badge = getScoreBadge(r.총점, r.예상반기총점, isInterim);
                return (
                  <tr key={r.센터명} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-gray-500">{i + 1}</td>
                    <td className="py-2.5 px-3 font-bold text-[#172B4D]">{r.센터명}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-[#0B4EA2]">{r.총점.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-bold border"
                        style={{ backgroundColor: badge.bg, color: badge.color, borderColor: badge.border }}
                      >
                        {badge.text}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-600">
                      {r.안전점검_점수.toFixed(1)} <span className="text-[10px] text-gray-400">({r.안전점검_달성률.toFixed(0)}%)</span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-600">
                      {r.중점고객_점수.toFixed(1)} <span className="text-[10px] text-gray-400">({r.중점고객_달성률.toFixed(0)}%)</span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-600">{r.사용계약_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-gray-600">{r.상담응대_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-gray-600">{r.상담기여_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-gray-600">{r.만족도_점수.toFixed(1)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
