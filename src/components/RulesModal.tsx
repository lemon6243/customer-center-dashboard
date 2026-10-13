import React from 'react';

interface RulesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RulesModal: React.FC<RulesModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-4">
        <div className="flex items-center justify-between border-b pb-3">
          <h3 className="text-base font-bold text-[#172B4D] flex items-center gap-2">
            <span>⚖️</span> 2026년 고객센터 평가 배점 규칙 및 기준
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg font-bold cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4 text-xs text-[#172B4D]">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-bold text-blue-900 mb-1">🎯 종합 합격 및 재계약 기준</h4>
            <p className="text-blue-800 leading-relaxed">
              • 반기 합격 기준: <strong>911점 이상</strong> (만점 1,000점 기준)<br />
              • 연간 재계약 기준: 상·하반기 합산 <strong>1,822점 이상</strong><br />
              • 구간 판정: 911점 이상(안전/달성), 895~910점(주의/근접미달), 895점 미만(위험/미달)
            </p>
          </div>

          <div>
            <h4 className="font-bold text-sm text-[#172B4D] mb-2">📊 6대 핵심 KPI 항목 및 배점</h4>
            <table className="w-full text-xs text-left border border-gray-200">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="py-2 px-3">항목</th>
                  <th className="py-2 px-3 text-right">배점</th>
                  <th className="py-2 px-3">산출 방식</th>
                  <th className="py-2 px-3">구분</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr>
                  <td className="py-2 px-3 font-semibold">안전점검실점검율</td>
                  <td className="py-2 px-3 text-right font-bold text-blue-700">550점</td>
                  <td className="py-2 px-3">점검율 × 550점</td>
                  <td className="py-2 px-3 text-emerald-700 font-medium">누적형</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">중점고객안전점검율</td>
                  <td className="py-2 px-3 text-right font-bold text-blue-700">100점</td>
                  <td className="py-2 px-3">점검율 × 100점</td>
                  <td className="py-2 px-3 text-emerald-700 font-medium">누적형</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">사용계약율</td>
                  <td className="py-2 px-3 text-right font-bold text-blue-700">50점</td>
                  <td className="py-2 px-3">A(90%+) 50점, B(80%+) 45점, C(70%+) 40점, D 35점</td>
                  <td className="py-2 px-3 text-emerald-700 font-medium">누적형(등급)</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">상담응대율</td>
                  <td className="py-2 px-3 text-right font-bold text-blue-700">100점</td>
                  <td className="py-2 px-3">응대율 × 100점</td>
                  <td className="py-2 px-3 text-gray-500">당월형</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">상담기여도</td>
                  <td className="py-2 px-3 text-right font-bold text-blue-700">100점</td>
                  <td className="py-2 px-3">기여도 × 100점</td>
                  <td className="py-2 px-3 text-gray-500">당월형</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">고객서비스만족도</td>
                  <td className="py-2 px-3 text-right font-bold text-blue-700">100점</td>
                  <td className="py-2 px-3">만족도 점수 (100점 만점 환산)</td>
                  <td className="py-2 px-3 text-gray-500">당월형</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div>
            <h4 className="font-bold text-sm text-[#172B4D] mb-2">⚖️ 가감점 및 조정 항목</h4>
            <p className="text-gray-600 leading-relaxed">
              • <strong>민원대응적정성</strong>: 최대 ±5점 가감<br />
              • <strong>주의경고 감점</strong>: 사안별 -1점 ~ -5점 감점<br />
              • <strong>기타 가점</strong>: 안전혁신 및 공헌도 최대 +5점 가점
            </p>
          </div>
        </div>

        <div className="pt-3 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#0B4EA2] text-white rounded-lg text-xs font-bold hover:bg-[#073A7A] cursor-pointer"
          >
            확인 및 닫기
          </button>
        </div>
      </div>
    </div>
  );
};
