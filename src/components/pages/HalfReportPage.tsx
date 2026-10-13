import React, { useMemo } from 'react';
import { ScoredRecord } from '../../types';
import * as XLSX from 'xlsx';
import { Colors } from '../../utils/styles';

interface HalfReportPageProps {
  df: ScoredRecord[];
}

export const HalfReportPage: React.FC<HalfReportPageProps> = ({ df }) => {
  const h1Records = useMemo(() => {
    const recs2026_06 = df.filter(r => r.평가월.startsWith('2026-06'));
    if (recs2026_06.length > 0) return recs2026_06;
    const half1 = df.filter(r => r.월 === 6);
    if (half1.length > 0) return half1;
    return df.filter(r => r.연도 === 2026 && r.반기 === '상반기');
  }, [df]);

  const lastYearH1Records = useMemo(() => {
    return df.filter(r => r.연도 === 2025 && r.월 === 6);
  }, [df]);

  const totalCenters = h1Records.length;
  const avgH1Score = totalCenters > 0 ? h1Records.reduce((s, r) => s + r.총점, 0) / totalCenters : 0;
  const passCount = h1Records.filter(r => r.총점 >= 911).length;
  const passRate = totalCenters > 0 ? ((passCount / totalCenters) * 100).toFixed(1) : '0';

  const lastYearAvg = lastYearH1Records.length > 0
    ? lastYearH1Records.reduce((s, r) => s + r.총점, 0) / lastYearH1Records.length
    : 0;

  const yoyDiff = lastYearAvg > 0 ? avgH1Score - lastYearAvg : 0;

  const sortedH1 = useMemo(() => {
    const list = [...h1Records].sort((a, b) => b.총점 - a.총점);
    const lastMap = new Map(lastYearH1Records.map(r => [r.센터명, r.총점]));

    return list.map((r, i) => {
      const lastScore = lastMap.get(r.센터명);
      const diff = lastScore !== undefined ? r.총점 - lastScore : null;
      return {
        ...r,
        rank: i + 1,
        lastScore,
        diff,
      };
    });
  }, [h1Records, lastYearH1Records]);

  const handleExportReport = () => {
    const exportData = sortedH1.map(r => ({
      순위: r.rank,
      센터명: r.센터명,
      '2026상반기 총점': r.총점,
      '2025상반기 총점': r.lastScore ?? 'N/A',
      전년대비증감: r.diff !== null ? r.diff.toFixed(1) : 'N/A',
      안전점검: r.안전점검_점수,
      중점고객: r.중점고객_점수,
      사용계약: r.사용계약_점수,
      상담응대: r.상담응대_점수,
      상담기여: r.상담기여_점수,
      만족도: r.만족도_점수,
    }));
    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '2026상반기결과');
    XLSX.writeFile(wb, `yesco_2026_h1_report.xlsx`);
  };

  return (
    <div className="space-y-6" id="half-report-container">
      <div className="bg-[#EAF3FF] border border-[#BFDBFE] rounded-xl p-5 flex flex-wrap items-center justify-between gap-3 shadow-xs">
        <div>
          <h3 className="text-base font-bold text-[#073A7A] flex items-center gap-2">
            <span>📑</span> 2026년 상반기 종합 평가 결과 리포트
          </h3>
          <p className="text-xs text-[#5E6C84] mt-1">
            2026년 상반기(1~6월) 마감 실적 및 전년(2025년) 상반기 대비 증감 분석
          </p>
        </div>
        <button
          onClick={handleExportReport}
          className="px-3.5 py-1.5 text-xs font-bold bg-[#0B4EA2] hover:bg-[#073A7A] text-white rounded-lg flex items-center gap-1.5 cursor-pointer shadow-xs transition-colors"
        >
          <span>📥</span> 종합 보고서 다운로드 (Excel)
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-[#DCE3EA] p-4 shadow-xs" style={{ borderTop: `3px solid ${Colors.PRIMARY}` }}>
          <div className="text-xs text-[#5E6C84] font-medium">상반기 평균 총점</div>
          <div className="text-2xl font-extrabold mt-1 text-[#0B4EA2]">{avgH1Score.toFixed(1)}점</div>
          <div className="text-xs text-[#5E6C84] mt-2">
            {lastYearAvg > 0 ? (
              <span className={yoyDiff >= 0 ? 'text-[#166534] font-bold' : 'text-[#991B1B] font-bold'}>
                전년 대비 {yoyDiff >= 0 ? `+${yoyDiff.toFixed(1)}` : yoyDiff.toFixed(1)}점
              </span>
            ) : (
              '기준 목표 911점'
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#DCE3EA] p-4 shadow-xs" style={{ borderTop: `3px solid ${Colors.SUCCESS}` }}>
          <div className="text-xs text-[#5E6C84] font-medium">911점 달성률</div>
          <div className="text-2xl font-extrabold mt-1 text-[#166534]">{passRate}%</div>
          <div className="text-xs text-[#166534] mt-2 font-medium">
            {passCount}개 센터 달성 / 총 {totalCenters}개소
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#DCE3EA] p-4 shadow-xs" style={{ borderTop: `3px solid #F59E0B` }}>
          <div className="text-xs text-[#5E6C84] font-medium">미달 센터 현황</div>
          <div className="text-2xl font-extrabold mt-1 text-[#D92D20]">{totalCenters - passCount}개소</div>
          <div className="text-xs text-gray-500 mt-2">
            하반기 재계약 보강 대상
          </div>
        </div>
      </div>

      <div className="bg-[#FFFDF5] border border-[#FDE68A] rounded-xl p-4 text-xs text-[#92400E] space-y-1">
        <div className="font-bold flex items-center gap-1.5">
          <span>ℹ️</span> 권역 조정 및 센터 통합 안내:
        </div>
        <div>• <strong>퇴계원/별내</strong>: 2026년 통합 운영 센터로 단일 실적으로 평가됩니다.</div>
        <div>• <strong>구리</strong>: 2026년 4월 권역조정으로 행정동을 흡수하였으나, 안전점검은 기존 관리세대 기준으로 공정하게 평가되었습니다.</div>
      </div>

      <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-3">
        <h4 className="text-sm font-bold text-[#172B4D]">
          🏢 센터별 2026년 상반기 평가 종합 순위
        </h4>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#F8FAFC] text-[#5E6C84] border-y border-[#DCE3EA]">
              <tr>
                <th className="py-2.5 px-3">순위</th>
                <th className="py-2.5 px-3">센터명</th>
                <th className="py-2.5 px-3 text-right">상반기 총점</th>
                <th className="py-2.5 px-3 text-right">목표(911) 대비</th>
                <th className="py-2.5 px-3 text-right">전년 대비</th>
                <th className="py-2.5 px-3 text-right">안전점검(550)</th>
                <th className="py-2.5 px-3 text-right">중점고객(100)</th>
                <th className="py-2.5 px-3 text-right">사용계약(50)</th>
                <th className="py-2.5 px-3 text-right">상담응대(100)</th>
                <th className="py-2.5 px-3 text-right">상담기여(100)</th>
                <th className="py-2.5 px-3 text-right">만족도(100)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF2F6]">
              {sortedH1.map(r => {
                const targetGap = r.총점 - 911;
                return (
                  <tr key={r.센터명} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-bold text-gray-500">{r.rank}</td>
                    <td className="py-2.5 px-3 font-bold text-[#172B4D]">{r.센터명}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-[#0B4EA2]">{r.총점.toFixed(1)}</td>
                    <td className={`py-2.5 px-3 text-right font-semibold ${targetGap >= 0 ? 'text-[#166534]' : 'text-[#991B1B]'}`}>
                      {targetGap >= 0 ? `+${targetGap.toFixed(1)}` : targetGap.toFixed(1)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-medium">
                      {r.diff !== null ? (
                        <span className={r.diff >= 0 ? 'text-[#166534]' : 'text-[#991B1B]'}>
                          {r.diff >= 0 ? `+${r.diff.toFixed(1)}` : r.diff.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-600">{r.안전점검_점수.toFixed(1)}</td>
                    <td className="py-2.5 px-3 text-right text-gray-600">{r.중점고객_점수.toFixed(1)}</td>
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
