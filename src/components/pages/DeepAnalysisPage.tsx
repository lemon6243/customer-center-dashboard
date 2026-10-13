import React, { useState, useMemo } from 'react';
import { ScoredRecord } from '../../types';
import * as XLSX from 'xlsx';

interface DeepAnalysisPageProps {
  df: ScoredRecord[];
}

const SCORE_COLS = [
  { key: '안전점검_점수', label: '안전점검' },
  { key: '중점고객_점수', label: '중점고객' },
  { key: '사용계약_점수', label: '사용계약' },
  { key: '상담응대_점수', label: '상담응대' },
  { key: '상담기여_점수', label: '상담기여' },
  { key: '만족도_점수', label: '만족도' },
  { key: '총점', label: '총점' },
];

function calculatePearsonCorrelation(x: number[], y: number[]): number {
  const n = x.length;
  if (n === 0) return 0;
  const avgX = x.reduce((a, b) => a + b, 0) / n;
  const avgY = y.reduce((a, b) => a + b, 0) / n;

  let numerator = 0;
  let denomX = 0;
  let denomY = 0;

  for (let i = 0; i < n; i++) {
    const dx = x[i] - avgX;
    const dy = y[i] - avgY;
    numerator += dx * dy;
    denomX += dx * dx;
    denomY += dy * dy;
  }

  const denominator = Math.sqrt(denomX * denomY);
  if (denominator === 0) return 0;
  return Math.round((numerator / denominator) * 100) / 100;
}

export const DeepAnalysisPage: React.FC<DeepAnalysisPageProps> = ({ df }) => {
  const [activeTab, setActiveTab] = useState<'stats' | 'raw'>('stats');
  const [searchFilter, setSearchFilter] = useState('');
  const [centerFilter, setCenterFilter] = useState('ALL');
  const [monthFilter, setMonthFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 25;

  const allCenters = useMemo(() => Array.from(new Set(df.map(r => r.센터명))).sort(), [df]);
  const allMonths = useMemo(() => Array.from(new Set(df.map(r => String(r.평가월 || '').substring(0, 7)))).sort(), [df]);

  const correlationMatrix = useMemo(() => {
    return SCORE_COLS.map(rowCol => {
      return {
        label: rowCol.label,
        values: SCORE_COLS.map(colCol => {
          const x = df.map(r => (r as any)[rowCol.key] || 0);
          const y = df.map(r => (r as any)[colCol.key] || 0);
          return calculatePearsonCorrelation(x, y);
        }),
      };
    });
  }, [df]);

  const filteredRecords = useMemo(() => {
    return df.filter(r => {
      const matchCenter = centerFilter === 'ALL' || r.센터명 === centerFilter;
      const matchMonth = monthFilter === 'ALL' || String(r.평가월 || '').startsWith(monthFilter);
      const matchSearch =
        !searchFilter ||
        r.센터명.toLowerCase().includes(searchFilter.toLowerCase()) ||
        String(r.평가월 || '').includes(searchFilter);
      return matchCenter && matchMonth && matchSearch;
    });
  }, [df, centerFilter, monthFilter, searchFilter]);

  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;
  const currentRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, currentPage]);

  const handleExportExcel = () => {
    const ws = XLSX.utils.json_to_sheet(filteredRecords);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Data');
    XLSX.writeFile(wb, `yesco_dashboard_data_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  return (
    <div className="space-y-6" id="deep-analysis-container">
      {/* Tabs */}
      <div className="flex border-b border-[#DCE3EA]">
        <button
          onClick={() => setActiveTab('stats')}
          className={`py-2.5 px-5 font-bold text-sm border-b-2 transition-colors cursor-pointer ${
            activeTab === 'stats'
              ? 'border-[#0B4EA2] text-[#0B4EA2]'
              : 'border-transparent text-[#5E6C84] hover:text-[#172B4D]'
          }`}
        >
          📊 지표 간 상관관계 및 통계
        </button>
        <button
          onClick={() => setActiveTab('raw')}
          className={`py-2.5 px-5 font-bold text-sm border-b-2 transition-colors cursor-pointer ${
            activeTab === 'raw'
              ? 'border-[#0B4EA2] text-[#0B4EA2]'
              : 'border-transparent text-[#5E6C84] hover:text-[#172B4D]'
          }`}
        >
          📋 원본 데이터 및 엑셀 다운로드
        </button>
      </div>

      {activeTab === 'stats' ? (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-[#172B4D] flex items-center gap-1.5">
                <span>🔍</span> 6대 핵심 KPI 및 총점 간 피어슨 상관계수 행렬
              </h3>
              <p className="text-xs text-[#5E6C84] mt-0.5">
                1.00에 가까울수록 강한 양의 상관관계, -1.00에 가까울수록 강한 음의 상관관계를 나타냅니다.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-center border-collapse">
                <thead>
                  <tr className="bg-[#F8FAFC] text-[#5E6C84] border-b border-[#DCE3EA]">
                    <th className="py-2.5 px-3 text-left">항목</th>
                    {SCORE_COLS.map(c => (
                      <th key={c.key} className="py-2.5 px-3 font-semibold">{c.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EEF2F6]">
                  {correlationMatrix.map((row, rIdx) => (
                    <tr key={row.label} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 text-left font-bold text-[#172B4D]">{row.label}</td>
                      {row.values.map((val, cIdx) => {
                        let bg = '#F8FAFC';
                        let text = '#172B4D';
                        if (rIdx === cIdx) {
                          bg = '#E2E8F0';
                          text = '#64748B';
                        } else if (val >= 0.5) {
                          bg = '#DCFCE7';
                          text = '#15803D';
                        } else if (val >= 0.2) {
                          bg = '#F0FDF4';
                          text = '#166534';
                        } else if (val <= -0.3) {
                          bg = '#FEE2E2';
                          text = '#B91C1C';
                        }
                        return (
                          <td key={cIdx} className="p-1">
                            <div
                              className="py-1.5 px-2 rounded font-bold text-xs"
                              style={{ backgroundColor: bg, color: text }}
                            >
                              {val.toFixed(2)}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="bg-[#F8FAFC] p-3 rounded-lg border border-[#EEF2F6] text-xs text-[#5E6C84] space-y-1">
              <div className="font-bold text-[#172B4D]">💡 상관관계 주요 분석 포인트:</div>
              <div>• 안전점검(550점)과 총점 간 상관관계가 가장 높아 전체 종합 순위 결정력이 큽니다.</div>
              <div>• 상담응대율과 고객만족도 간 상호보완적 상관성이 존재하여 통합 관리가 필수적입니다.</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#DCE3EA] pb-3">
            <div className="flex flex-wrap items-center gap-3">
              <input
                type="text"
                placeholder="검색어 입력..."
                value={searchFilter}
                onChange={e => { setSearchFilter(e.target.value); setCurrentPage(1); }}
                className="px-3 py-1.5 text-xs border border-[#DCE3EA] rounded-md focus:outline-none focus:border-[#0B4EA2] w-40"
              />

              <select
                value={centerFilter}
                onChange={e => { setCenterFilter(e.target.value); setCurrentPage(1); }}
                className="px-2.5 py-1.5 text-xs border border-[#DCE3EA] rounded-md bg-white text-[#172B4D]"
              >
                <option value="ALL">전체 센터</option>
                {allCenters.map(c => <option key={c} value={c}>{c}</option>)}
              </select>

              <select
                value={monthFilter}
                onChange={e => { setMonthFilter(e.target.value); setCurrentPage(1); }}
                className="px-2.5 py-1.5 text-xs border border-[#DCE3EA] rounded-md bg-white text-[#172B4D]"
              >
                <option value="ALL">전체 평가월</option>
                {allMonths.map(m => <option key={m} value={m}>{m}</option>)}
              </select>

              <span className="text-xs text-[#5E6C84]">
                총 <strong>{filteredRecords.length.toLocaleString()}</strong>건
              </span>
            </div>

            <button
              onClick={handleExportExcel}
              className="px-3.5 py-1.5 text-xs font-bold bg-[#178A5B] hover:bg-[#137149] text-white rounded-md flex items-center gap-1.5 cursor-pointer shadow-xs transition-colors"
            >
              <span>💾</span> 엑셀(Excel) 다운로드
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#F8FAFC] text-[#5E6C84] border-y border-[#DCE3EA]">
                <tr>
                  <th className="py-2.5 px-3">평가월</th>
                  <th className="py-2.5 px-3">센터명</th>
                  <th className="py-2.5 px-3 text-right">총점</th>
                  <th className="py-2.5 px-3 text-right">안전점검(550)</th>
                  <th className="py-2.5 px-3 text-right">중점고객(100)</th>
                  <th className="py-2.5 px-3 text-right">사용계약(50)</th>
                  <th className="py-2.5 px-3 text-right">상담응대(100)</th>
                  <th className="py-2.5 px-3 text-right">상담기여(100)</th>
                  <th className="py-2.5 px-3 text-right">만족도(100)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF2F6]">
                {currentRecords.map((r, i) => (
                  <tr key={`${r.센터명}_${r.평가월}_${i}`} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 text-[#5E6C84]">{r.평가월.slice(0, 7)}</td>
                    <td className="py-2.5 px-3 font-bold text-[#172B4D]">{r.센터명}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-[#0B4EA2]">{r.총점.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-[#5E6C84]">{r.안전점검_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-[#5E6C84]">{r.중점고객_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-[#5E6C84]">{r.사용계약_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-[#5E6C84]">{r.상담응대_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-[#5E6C84]">{r.상담기여_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-[#5E6C84]">{r.만족도_점수.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-[#5E6C84] pt-2">
            <div>
              페이지 {currentPage} / {totalPages} (전체 {filteredRecords.length}건)
            </div>
            <div className="flex items-center gap-1.5">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                className="px-2.5 py-1 border border-[#DCE3EA] rounded disabled:opacity-40 cursor-pointer"
              >
                이전
              </button>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 border border-[#DCE3EA] rounded disabled:opacity-40 cursor-pointer"
              >
                다음
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
