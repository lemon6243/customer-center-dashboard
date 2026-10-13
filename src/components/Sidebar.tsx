import React, { useRef } from 'react';
import { PageKey, PeriodInfo } from '../types';

interface SidebarProps {
  currentPage: PageKey;
  onPageChange: (page: PageKey) => void;
  periodInfo: PeriodInfo;
  totalCenters: number;
  totalRows: number;
  onUploadData: (file: File) => void;
  onResetData: () => void;
  onOpenRulesModal: () => void;
}

const MENU_ITEMS: Array<{ key: PageKey; icon: string; label: string; badge?: string }> = [
  { key: '🏠 홈', icon: '🏠', label: '홈' },
  { key: '📊 성과 분석', icon: '📊', label: '성과 분석' },
  { key: '🎯 센터 진단', icon: '🎯', label: '센터 진단' },
  { key: '⚠️ 위험 관리', icon: '⚠️', label: '위험 관리' },
  { key: '🌡️ KPI 히트맵', icon: '🌡️', label: 'KPI 히트맵' },
  { key: '🔬 심화 분석', icon: '🔬', label: '심화 분석' },
  { key: '📑 상반기 보고', icon: '📑', label: '상반기 보고' },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onPageChange,
  periodInfo,
  totalCenters,
  totalRows,
  onUploadData,
  onResetData,
  onOpenRulesModal,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadData(file);
    }
  };

  return (
    <aside className="no-print w-64 bg-[#F8FAFC] border-r border-[#DCE3EA] flex flex-col justify-between shrink-0 h-screen sticky top-0 overflow-y-auto">
      <div className="p-4 space-y-6">
        {/* Brand Header */}
        <div className="flex items-center gap-2.5 px-2">
          <div className="w-8 h-8 rounded-lg bg-[#0B4EA2] text-white font-bold flex items-center justify-center text-sm shadow-xs">
            Y
          </div>
          <div>
            <h1 className="text-sm font-bold text-[#0B4EA2] tracking-tight">예스코 고객센터</h1>
            <p className="text-[11px] text-[#5E6C84]">성과 평가 관리 시스템</p>
          </div>
        </div>

        {/* Navigation Menu */}
        <div className="space-y-1">
          <div className="text-[11px] font-bold text-[#5E6C84] uppercase tracking-wider px-2 mb-2">
            메인 메뉴
          </div>
          {MENU_ITEMS.map(item => {
            const isActive = currentPage === item.key;
            return (
              <button
                key={item.key}
                onClick={() => onPageChange(item.key)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-bold transition-all text-left cursor-pointer ${
                  isActive
                    ? 'bg-[#0B4EA2] text-white shadow-xs'
                    : item.badge
                    ? 'bg-blue-50/60 text-[#0B4EA2] hover:bg-blue-100/60 border border-blue-200/60'
                    : 'text-[#172B4D] hover:bg-[#EAF3FF] hover:text-[#0B4EA2]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-base leading-none">{item.icon}</span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                    isActive ? 'bg-white/20 text-white' : 'bg-blue-600 text-white'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Data Status Section */}
        <div className="p-3 bg-white rounded-lg border border-[#DCE3EA] space-y-2 text-xs">
          <div className="font-bold text-[#172B4D] flex items-center justify-between">
            <span>📊 데이터 현황</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          </div>
          <div className="space-y-1 text-[#5E6C84] text-[11px]">
            <div className="flex justify-between">
              <span>기준월:</span>
              <strong className="text-[#172B4D]">{periodInfo.year}년 {periodInfo.current_month}월</strong>
            </div>
            <div className="flex justify-between">
              <span>진행 경과:</span>
              <span className="text-[#0B4EA2] font-semibold">{periodInfo.period_text}</span>
            </div>
            <div className="flex justify-between">
              <span>대상 센터:</span>
              <strong className="text-[#172B4D]">{totalCenters}개소</strong>
            </div>
            <div className="flex justify-between">
              <span>전체 데이터:</span>
              <span>{totalRows.toLocaleString()}건</span>
            </div>
          </div>
        </div>

        {/* Excel Upload Section */}
        <div className="space-y-2">
          <div className="text-[11px] font-bold text-[#5E6C84] uppercase tracking-wider px-2">
            데이터 관리
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx, .xls, .csv"
            onChange={handleFileChange}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full py-2 px-3 bg-white hover:bg-slate-50 border border-[#DCE3EA] rounded-lg text-xs font-semibold text-[#172B4D] flex items-center justify-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <span>📁</span> 엑셀 데이터 교체
          </button>
          <button
            onClick={onResetData}
            className="w-full py-1.5 px-3 text-[11px] text-gray-500 hover:text-gray-700 hover:underline cursor-pointer text-center"
          >
            기본 데이터로 복원
          </button>
        </div>
      </div>

      {/* Footer / Rules trigger */}
      <div className="p-4 border-t border-[#DCE3EA] bg-white space-y-2">
        <button
          onClick={onOpenRulesModal}
          className="w-full py-2 px-3 bg-[#EAF3FF] hover:bg-[#D8EAFF] text-[#073A7A] rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <span>⚖️</span> 배점 규칙 & 기준 안내
        </button>
        <div className="text-[10px] text-center text-gray-400">
          YESCO Customer Dashboard v2.1
        </div>
      </div>
    </aside>
  );
};
