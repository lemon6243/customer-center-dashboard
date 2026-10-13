import React, { useState, useMemo } from 'react';
import { initialScoredData } from './data/initialData';
import { ScoredRecord, PageKey, RawRecord } from './types';
import {
  getPeriodInfo,
  processAndScoreRecord,
  normalizeDateString,
  enrichRecordsWithYoYAndBenchmark,
} from './utils/scoreCalculator';
import { Sidebar } from './components/Sidebar';
import { HomePage } from './components/pages/HomePage';
import { PerformancePage } from './components/pages/PerformancePage';
import { CenterDetailPage } from './components/pages/CenterDetailPage';
import { RiskPage } from './components/pages/RiskPage';
import { HeatmapPage } from './components/pages/HeatmapPage';
import { DeepAnalysisPage } from './components/pages/DeepAnalysisPage';
import { HalfReportPage } from './components/pages/HalfReportPage';
import { RulesModal } from './components/RulesModal';
import * as XLSX from 'xlsx';

export const App: React.FC = () => {
  const [records, setRecords] = useState<ScoredRecord[]>(initialScoredData);
  const [currentPage, setCurrentPage] = useState<PageKey>('🏠 홈');
  const [isRulesModalOpen, setIsRulesModalOpen] = useState(false);
  const [uploadToast, setUploadToast] = useState<string | null>(null);

  // 사용 가능한 모든 평가월 목록 추출 (오름차순 정렬)
  const allAvailableMonths = useMemo(() => {
    const monthsSet = new Set(records.map(r => String(r.평가월 || '').substring(0, 7)));
    return Array.from(monthsSet).filter(Boolean).sort();
  }, [records]);

  // 최신월 추출 (데이터셋의 가장 마지막 최신 월)
  const latestMonth = useMemo(() => {
    return allAvailableMonths.length > 0
      ? allAvailableMonths[allAvailableMonths.length - 1]
      : '2026-08';
  }, [allAvailableMonths]);

  // 사용자가 수동 선택한 월 (기본값 빈 문자열 -> 항상 최신월을 디폴트로 표시)
  const [selectedMonth, setSelectedMonth] = useState<string>('');

  const activeMonth = useMemo(() => {
    if (selectedMonth && allAvailableMonths.includes(selectedMonth)) {
      return selectedMonth;
    }
    return latestMonth;
  }, [selectedMonth, allAvailableMonths, latestMonth]);

  const periodInfo = useMemo(() => {
    return getPeriodInfo(activeMonth + '-01');
  }, [activeMonth]);

  const dfLatest = useMemo(() => {
    const rawLatest = records.filter(r => String(r.평가월 || '').startsWith(activeMonth));
    return enrichRecordsWithYoYAndBenchmark(rawLatest, records, periodInfo);
  }, [records, activeMonth, periodInfo]);

  const dfPrev = useMemo(() => {
    const currentIdx = allAvailableMonths.indexOf(activeMonth);
    if (currentIdx > 0) {
      const prevMonthStr = allAvailableMonths[currentIdx - 1];
      return records.filter(r => String(r.평가월 || '').startsWith(prevMonthStr));
    }
    return [];
  }, [records, allAvailableMonths, activeMonth]);

  const totalCenters = dfLatest.length;

  const handleUploadExcel = async (file: File) => {
    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      const rawRows: any[] = XLSX.utils.sheet_to_json(firstSheet);

      if (!rawRows || rawRows.length === 0) {
        alert('엑셀 파일에 데이터가 없습니다.');
        return;
      }

      const parsedRecords: ScoredRecord[] = rawRows.map(row => {
        const raw: RawRecord = {
          센터명: row['센터명'] || row['센터'] || '미상',
          평가월: normalizeDateString(row['평가월'] || '2026-02-01'),
          안전점검실점검율: row['안전점검실점검율'] ?? null,
          중점고객안전점검율: row['중점고객안전점검율'] ?? null,
          사용계약율: row['사용계약율'] ?? null,
          상담응대율: row['상담응대율'] ?? null,
          상담기여도: row['상담기여도'] ?? null,
          고객서비스만족도: row['고객서비스만족도'] ?? null,
          민원대응적정성: Number(row['민원대응적정성'] || 0),
          주의경고: Number(row['주의경고'] || 0),
          가점: Number(row['가점'] || 0),
          총점: row['총점'] !== undefined && row['총점'] !== null ? Number(row['총점']) : null,
        };
        return processAndScoreRecord(raw);
      });

      setRecords(parsedRecords);
      setSelectedMonth('');
      setUploadToast(`성공적으로 ${parsedRecords.length}건의 데이터를 불러왔습니다. (최신월 기준 반영)`);
      setTimeout(() => setUploadToast(null), 4000);
    } catch (err: any) {
      alert(`파일 처리 오류: ${err.message}`);
    }
  };

  const handleResetData = () => {
    setRecords(initialScoredData);
    setSelectedMonth('');
    setUploadToast('기본 데이터셋으로 복원되었습니다. (최신월 기준)');
    setTimeout(() => setUploadToast(null), 3000);
  };

  return (
    <div className="min-h-screen flex bg-[#F5F7FA] text-[#172B4D]">
      {/* Left Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        periodInfo={periodInfo}
        totalCenters={totalCenters}
        totalRows={records.length}
        onUploadData={handleUploadExcel}
        onResetData={handleResetData}
        onOpenRulesModal={() => setIsRulesModalOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Main Header Banner */}
        <header className="no-print yesco-header-banner text-white p-5 px-8 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight">예스코 고객센터 성과 대시보드</h1>
            <p className="text-xs text-blue-100 opacity-90 mt-0.5">
              도시가스 고객센터 월별 KPI 성과, 반기 마감(911점) 전망 및 전년 동월 대비 위험관리 분석
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* 평가월 선택 드롭다운 */}
            <div className="flex items-center gap-1.5 bg-white/15 backdrop-blur-xs px-3 py-1.5 rounded-lg border border-white/25">
              <label htmlFor="month-select" className="text-xs font-semibold text-blue-100">평가월:</label>
              <select
                id="month-select"
                value={activeMonth}
                onChange={e => setSelectedMonth(e.target.value)}
                className="bg-transparent text-white text-xs font-bold focus:outline-none cursor-pointer"
              >
                {allAvailableMonths.map(ym => {
                  const [y, m] = ym.split('-');
                  const mNum = parseInt(m, 10);
                  const isH1 = mNum <= 6;
                  const mInH = isH1 ? mNum : mNum - 6;
                  const halfName = isH1 ? '상반기' : '하반기';
                  const isLatest = ym === latestMonth;
                  return (
                    <option key={ym} value={ym} className="text-slate-900 bg-white font-medium">
                      {y}년 {mNum}월 ({halfName} {mInH}개월차){isLatest ? ' ★최신' : ''}
                    </option>
                  );
                })}
              </select>
            </div>

            <button
              onClick={() => setIsRulesModalOpen(true)}
              className="text-xs font-semibold px-3 py-1.5 bg-white text-[#0B4EA2] rounded-md hover:bg-blue-50 transition-colors cursor-pointer shadow-2xs"
            >
              평가 기준 ℹ️
            </button>
          </div>
        </header>

        {/* Toast Alert */}
        {uploadToast && (
          <div className="no-print mx-6 mt-4 p-3 bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold rounded-lg flex items-center justify-between shadow-xs">
            <span>✅ {uploadToast}</span>
            <button onClick={() => setUploadToast(null)} className="text-emerald-900 font-bold">✕</button>
          </div>
        )}

        {/* Page Content Container */}
        <div className="p-6 md:p-8 max-w-7xl w-full mx-auto space-y-6">
          {currentPage === '🏠 홈' && (
            <HomePage
              dfLatest={dfLatest}
              dfPrev={dfPrev}
              periodInfo={periodInfo}
              onNavigate={setCurrentPage}
              dfAll={records}
            />
          )}

          {currentPage === '📊 성과 분석' && (
            <PerformancePage
              df={records}
              dfLatest={dfLatest}
              periodInfo={periodInfo}
            />
          )}

          {currentPage === '🎯 센터 진단' && (
            <CenterDetailPage
              dfLatest={dfLatest}
              periodInfo={periodInfo}
            />
          )}

          {currentPage === '⚠️ 위험 관리' && (
            <RiskPage
              dfLatest={dfLatest}
              periodInfo={periodInfo}
            />
          )}

          {currentPage === '🌡️ KPI 히트맵' && (
            <HeatmapPage
              df={records}
              dfLatest={dfLatest}
            />
          )}

          {currentPage === '🔬 심화 분석' && (
            <DeepAnalysisPage
              df={records}
            />
          )}

          {currentPage === '📑 상반기 보고' && (
            <HalfReportPage
              df={records}
            />
          )}
        </div>
      </main>

      {/* Scoring Rules Modal */}
      <RulesModal
        isOpen={isRulesModalOpen}
        onClose={() => setIsRulesModalOpen(false)}
      />
    </div>
  );
};
