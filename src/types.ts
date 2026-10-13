export interface RawRecord {
  센터명: string;
  평가월: string;
  안전점검실점검율: number | null;
  중점고객안전점검율: number | null;
  사용계약율: number | null;
  상담응대율: number | null;
  상담기여도: number | null;
  고객서비스만족도: number | null;
  민원대응적정성?: number;
  주의경고?: number;
  가점?: number;
  총점?: number | null;
  [key: string]: any;
}

export interface ScoredRecord extends RawRecord {
  연도: number;
  월: number;
  반기: '상반기' | '하반기';
  총점: number;
  안전점검_점수: number;
  중점고객_점수: number;
  사용계약_점수: number;
  상담응대_점수: number;
  상담기여_점수: number;
  만족도_점수: number;
  안전점검_달성률: number;
  중점고객_달성률: number;
  사용계약_달성률: number;
  상담응대_달성률: number;
  상담기여_달성률: number;
  만족도_달성률: number;
  예상반기총점: number;
  전년대비증감?: number | null;
  전년동월_총점?: number | null;
  전년동월_안전점검달성률?: number | null;
  전년동월대비_증감?: number | null;
  전년반기말_총점?: number | null;
  도달판정?: '정상궤도' | '주의' | '위험';
  오더진척상태?: '양호' | '보통' | '지연';
}

export type PageKey = 
  | '🏠 홈'
  | '📊 성과 분석'
  | '🎯 센터 진단'
  | '⚠️ 위험 관리'
  | '🌡️ KPI 히트맵'
  | '🔬 심화 분석'
  | '📑 상반기 보고';

export interface PeriodInfo {
  year: number;
  current_month: number;
  month_in_half: number;
  half: '상반기' | '하반기';
  progress_rate: number;
  is_half_end: boolean;
  period_text: string;
  target_half_end_text: string;
}

export interface KPIDetail {
  key: string;
  label: string;
  maxScore: number;
  score: number;
  rate: number;
  isCumulative: boolean;
}

