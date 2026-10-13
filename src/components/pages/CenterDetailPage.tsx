import React, { useState, useMemo } from 'react';
import { ScoredRecord, PeriodInfo } from '../../types';
import { getScoreBadge } from '../../utils/styles';
import { runWhatIfSimulation } from '../../utils/simulator';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

interface CenterDetailPageProps {
  dfLatest: ScoredRecord[];
  periodInfo: PeriodInfo;
}

export const CenterDetailPage: React.FC<CenterDetailPageProps> = ({
  dfLatest,
  periodInfo,
}) => {
  const monthInHalf = periodInfo.month_in_half || (periodInfo.current_month <= 6 ? periodInfo.current_month : periodInfo.current_month - 6);
  const targetEndText = periodInfo.target_half_end_text || (periodInfo.current_month <= 6 ? '6월말' : '12월말');

  const [selectedCenterName, setSelectedCenterName] = useState<string>(
    dfLatest[0]?.센터명 || '광진'
  );

  const selectedRecord = useMemo(() => {
    return dfLatest.find(r => r.센터명 === selectedCenterName) || dfLatest[0];
  }, [dfLatest, selectedCenterName]);

  // Simulation State: 6월말 최종 목표치를 시뮬레이션하기 위한 기본값 (안전점검은 누적 목표치 반영)
  const defaultSafety = monthInHalf < 6 ? 94.0 : (selectedRecord?.안전점검_달성률 || 90);
  const defaultKey = monthInHalf < 6 ? 95.0 : (selectedRecord?.중점고객_달성률 || 90);

  const [simSafety, setSimSafety] = useState<number>(defaultSafety);
  const [simKey, setSimKey] = useState<number>(defaultKey);
  const [simContract, setSimContract] = useState<number>(selectedRecord?.사용계약_달성률 || 80);
  const [simResponse, setSimResponse] = useState<number>(selectedRecord?.상담응대_달성률 || 90);
  const [simContrib, setSimContrib] = useState<number>(selectedRecord?.상담기여_달성률 || 90);
  const [simSatisfaction, setSimSatisfaction] = useState<number>(selectedRecord?.만족도_달성률 || 85);

  // Sync simulator sliders when center changes
  const handleSelectCenter = (centerName: string) => {
    setSelectedCenterName(centerName);
    const rec = dfLatest.find(r => r.센터명 === centerName);
    if (rec) {
      setSimSafety(monthInHalf < 6 ? 94.0 : (rec.안전점검_달성률 || 90));
      setSimKey(monthInHalf < 6 ? 95.0 : (rec.중점고객_달성률 || 90));
      setSimContract(rec.사용계약_달성률 || 80);
      setSimResponse(rec.상담응대_달성률 || 90);
      setSimContrib(rec.상담기여_달성률 || 90);
      setSimSatisfaction(rec.만족도_달성률 || 85);
    }
  };

  const simulationResult = useMemo(() => {
    if (!selectedRecord) return null;
    return runWhatIfSimulation(selectedRecord, {
      safetyRate: simSafety,
      keyCustomerRate: simKey,
      contractRate: simContract,
      counselResponseRate: simResponse,
      counselContribRate: simContrib,
      satisfactionRate: simSatisfaction,
    });
  }, [selectedRecord, simSafety, simKey, simContract, simResponse, simContrib, simSatisfaction]);

  const radarData = useMemo(() => {
    if (!selectedRecord) return [];
    return [
      { subject: '안전점검 (550)', rate: selectedRecord.안전점검_달성률, fullMark: 100 },
      { subject: '중점고객 (100)', rate: selectedRecord.중점고객_달성률, fullMark: 100 },
      { subject: '사용계약 (50)', rate: selectedRecord.사용계약_달성률, fullMark: 100 },
      { subject: '상담응대 (100)', rate: selectedRecord.상담응대_달성률, fullMark: 100 },
      { subject: '상담기여 (100)', rate: selectedRecord.상담기여_달성률, fullMark: 100 },
      { subject: '만족도 (100)', rate: selectedRecord.만족도_달성률, fullMark: 100 },
    ];
  }, [selectedRecord]);

  if (!selectedRecord) {
    return <div className="p-6">데이터가 없습니다.</div>;
  }

  // Interim 평가 뱃지 (월 6 미만일 때 예상 점수 기준 적용)
  const badge = getScoreBadge(selectedRecord.총점, selectedRecord.예상반기총점, monthInHalf < 6);

  return (
    <div className="space-y-6" id="center-detail-container">
      {/* Center Select Header Banner */}
      <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div>
            <label className="text-[11px] font-bold text-[#5E6C84] uppercase tracking-wider block mb-1">진단 센터 선택</label>
            <select
              value={selectedCenterName}
              onChange={e => handleSelectCenter(e.target.value)}
              className="px-3 py-2 border border-[#0B4EA2] rounded-lg text-sm font-bold bg-blue-50/40 text-[#0B4EA2] focus:outline-none cursor-pointer"
            >
              {dfLatest.map(r => (
                <option key={r.센터명} value={r.센터명}>
                  {r.센터명} 센터 ({r.총점.toFixed(1)}점 | {targetEndText} 예상 {r.예상반기총점.toFixed(1)}점)
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="text-[10px] text-[#5E6C84]">당월({monthInHalf}개월차) 누적 총점</div>
            <div className="text-base font-extrabold text-[#0B4EA2]">{selectedRecord.총점.toFixed(1)}점</div>
          </div>
          <div className="px-3 py-2 bg-indigo-50 border border-indigo-200 rounded-lg">
            <div className="text-[10px] text-indigo-700">{targetEndText} 예상 총점</div>
            <div className="text-base font-extrabold text-indigo-900">{selectedRecord.예상반기총점.toFixed(1)}점</div>
          </div>
          <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="text-[10px] text-[#5E6C84]">전년 동월 대비 (YoY)</div>
            <div className={`text-base font-extrabold ${selectedRecord.전년동월대비_증감 && selectedRecord.전년동월대비_증감 < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
              {selectedRecord.전년동월대비_증감 != null ? `${selectedRecord.전년동월대비_증감 >= 0 ? '+' : ''}${selectedRecord.전년동월대비_증감.toFixed(1)}점` : '-'}
            </div>
          </div>
          <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="text-[10px] text-[#5E6C84]">전년 {targetEndText} 실적</div>
            <div className="text-base font-extrabold text-slate-700">
              {selectedRecord.전년반기말_총점 != null ? `${selectedRecord.전년반기말_총점.toFixed(1)}점` : '-'}
            </div>
          </div>
          <span
            className="px-3 py-2 rounded-lg text-xs font-bold border flex items-center justify-center"
            style={{ backgroundColor: badge.bg, color: badge.color, borderColor: badge.border }}
          >
            {badge.text}
          </span>
        </div>
      </div>

      {/* 안내 뱃지 */}
      <div className="p-3 bg-blue-50/60 border border-blue-200 text-blue-900 rounded-lg text-xs flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <span>ℹ️</span> 
          <span>
            <strong>평가 진척 안내:</strong> 현재 {monthInHalf}개월차 기준 당 센터의 안전점검 실점검율은 {selectedRecord.안전점검_달성률.toFixed(1)}%로 계획 대비 {selectedRecord.오더진척상태 === '지연' ? '보강 관리가 필요합니다.' : '양호하게 추진 중입니다.'} {targetEndText} 911점 예상 판정은 <strong>{selectedRecord.도달판정 || '정상궤도'}</strong> 상태입니다.
          </span>
        </span>
        <span className="text-[11px] font-bold text-[#0B4EA2] shrink-0 ml-3">
          진척 판정: {selectedRecord.오더진척상태 || '양호'}
        </span>
      </div>

      {/* Radar & Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs flex flex-col justify-between">
          <h3 className="text-sm font-bold text-[#172B4D] mb-1 flex items-center gap-1.5">
            <span>🎯</span> 6대 핵심 KPI 진척 밸런스 레이더
          </h3>
          <p className="text-xs text-[#5E6C84] mb-3">각 지표별 만점 대비 당월 달성률 현황 (안전점검 계열은 누적 진척도)</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#172B4D' }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
                <Radar
                  name={selectedRecord.센터명}
                  dataKey="rate"
                  stroke="#0B4EA2"
                  fill="#0B4EA2"
                  fillOpacity={0.4}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed KPI Table */}
        <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-[#172B4D]">
              📊 지표별 세부 채점 및 성격 내역
            </h3>
            <span className="text-[11px] text-slate-500">{monthInHalf}개월차 기준</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-[#F8FAFC] text-[#5E6C84] border-y border-[#DCE3EA]">
                <tr>
                  <th className="py-2 px-3">평가 항목</th>
                  <th className="py-2 px-3">지표 성격</th>
                  <th className="py-2 px-3 text-right">배점</th>
                  <th className="py-2 px-3 text-right">당월 달성률</th>
                  <th className="py-2 px-3 text-right">획득 점수</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF2F6]">
                <tr>
                  <td className="py-2 px-3 font-semibold text-slate-800">안전점검실점검율</td>
                  <td className="py-2 px-3 text-blue-700 font-medium text-[11px]">핵심 점검형</td>
                  <td className="py-2 px-3 text-right text-gray-500">550점</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800">{selectedRecord.안전점검_달성률.toFixed(1)}%</td>
                  <td className="py-2 px-3 text-right font-bold text-[#0B4EA2]">{selectedRecord.안전점검_점수.toFixed(1)}점</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-slate-800">중점고객안전점검율</td>
                  <td className="py-2 px-3 text-blue-700 font-medium text-[11px]">핵심 점검형</td>
                  <td className="py-2 px-3 text-right text-gray-500">100점</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800">{selectedRecord.중점고객_달성률.toFixed(1)}%</td>
                  <td className="py-2 px-3 text-right font-bold text-[#0B4EA2]">{selectedRecord.중점고객_점수.toFixed(1)}점</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-slate-800">사용계약율</td>
                  <td className="py-2 px-3 text-slate-500 text-[11px]">월별 비율 유지</td>
                  <td className="py-2 px-3 text-right text-gray-500">50점</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800">{selectedRecord.사용계약_달성률.toFixed(1)}%</td>
                  <td className="py-2 px-3 text-right font-bold text-[#0B4EA2]">{selectedRecord.사용계약_점수.toFixed(1)}점</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-slate-800">상담응대율</td>
                  <td className="py-2 px-3 text-slate-500 text-[11px]">월별 비율 유지</td>
                  <td className="py-2 px-3 text-right text-gray-500">100점</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800">{selectedRecord.상담응대_달성률.toFixed(1)}%</td>
                  <td className="py-2 px-3 text-right font-bold text-[#0B4EA2]">{selectedRecord.상담응대_점수.toFixed(1)}점</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-slate-800">상담기여도</td>
                  <td className="py-2 px-3 text-slate-500 text-[11px]">월별 비율 유지</td>
                  <td className="py-2 px-3 text-right text-gray-500">100점</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800">{selectedRecord.상담기여_달성률.toFixed(1)}%</td>
                  <td className="py-2 px-3 text-right font-bold text-[#0B4EA2]">{selectedRecord.상담기여_점수.toFixed(1)}점</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold text-slate-800">고객서비스만족도</td>
                  <td className="py-2 px-3 text-slate-500 text-[11px]">조사 평가 유지</td>
                  <td className="py-2 px-3 text-right text-gray-500">100점</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800">{selectedRecord.만족도_달성률.toFixed(1)}점</td>
                  <td className="py-2 px-3 text-right font-bold text-[#0B4EA2]">{selectedRecord.만족도_점수.toFixed(1)}점</td>
                </tr>
                <tr className="bg-slate-50 font-bold">
                  <td className="py-2.5 px-3 text-slate-800">합계 (현재 누적 총점)</td>
                  <td className="py-2.5 px-3 text-[#0B4EA2] text-[11px]">
                    {targetEndText} 예상 {selectedRecord.예상반기총점.toFixed(1)}점
                  </td>
                  <td className="py-2.5 px-3 text-right text-gray-500">1,000점</td>
                  <td className="py-2.5 px-3 text-right">-</td>
                  <td className="py-2.5 px-3 text-right text-blue-700 text-sm">{selectedRecord.총점.toFixed(1)}점</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* What-If Simulator Section */}
      <div className="bg-white rounded-xl border border-[#DCE3EA] p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#DCE3EA] pb-3">
          <div>
            <h3 className="text-sm font-bold text-[#172B4D] flex items-center gap-1.5">
              <span>🔮</span> What-If 시뮬레이터: {selectedRecord.센터명} 센터 {targetEndText} 911점 달성 전략 수립
            </h3>
            <p className="text-xs text-[#5E6C84]">
              {targetEndText} 최종 누적 목표치를 슬라이더로 조율하여 911점 달성 여부와 추가 필요 점수를 시뮬레이션합니다.
            </p>
          </div>

          {simulationResult && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-[11px] text-[#5E6C84]">{targetEndText} 시뮬레이션 총점</div>
                <div className="text-xl font-extrabold text-[#0B4EA2]">
                  {simulationResult.simulatedScore.toFixed(1)}점
                </div>
              </div>
              <div
                className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${
                  simulationResult.isPassing
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                    : 'bg-red-50 border-red-300 text-red-800'
                }`}
              >
                {simulationResult.isPassing ? '911점 달성 (합격)' : `${Math.abs(simulationResult.gapToPass).toFixed(1)}점 보강 필요`}
              </div>
            </div>
          )}
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {/* Safety */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">{targetEndText} 안전점검 목표치 (550)</span>
              <span className="font-bold text-[#0B4EA2]">{simSafety.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min={70}
              max={100}
              step={0.5}
              value={simSafety}
              onChange={e => setSimSafety(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="text-[10px] text-[#5E6C84]">
              당월 누적: {selectedRecord.안전점검_달성률.toFixed(1)}% (권장 92% 이상)
            </div>
          </div>

          {/* Key Customer */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">{targetEndText} 중점고객 목표치 (100)</span>
              <span className="font-bold text-[#0B4EA2]">{simKey.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min={60}
              max={100}
              step={0.5}
              value={simKey}
              onChange={e => setSimKey(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="text-[10px] text-[#5E6C84]">
              당월 누적: {selectedRecord.중점고객_달성률.toFixed(1)}% (권장 95% 이상)
            </div>
          </div>

          {/* Contract */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">사용계약율 (50)</span>
              <span className="font-bold text-[#0B4EA2]">{simContract.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min={60}
              max={100}
              step={1}
              value={simContract}
              onChange={e => setSimContract(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Counsel Response */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">상담응대율 (100)</span>
              <span className="font-bold text-[#0B4EA2]">{simResponse.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min={70}
              max={100}
              step={0.5}
              value={simResponse}
              onChange={e => setSimResponse(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Counsel Contrib */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">상담기여도 (100)</span>
              <span className="font-bold text-[#0B4EA2]">{simContrib.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min={70}
              max={100}
              step={0.5}
              value={simContrib}
              onChange={e => setSimContrib(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Satisfaction */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">만족도 점수 (100)</span>
              <span className="font-bold text-[#0B4EA2]">{simSatisfaction.toFixed(1)}점</span>
            </div>
            <input
              type="range"
              min={60}
              max={100}
              step={0.5}
              value={simSatisfaction}
              onChange={e => setSimSatisfaction(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>

        {/* Recommendation Box */}
        {simulationResult && (
          <div className="p-3.5 bg-blue-50/70 border border-blue-200 rounded-lg text-xs text-blue-950 font-medium mt-3 leading-relaxed">
            💡 <strong>시뮬레이션 진단 의견:</strong> {simulationResult.recommendation}
          </div>
        )}
      </div>
    </div>
  );
};
