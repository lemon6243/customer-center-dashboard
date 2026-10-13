export const Colors = {
  PRIMARY: '#0B4EA2',
  PRIMARY_LIGHT: '#EAF3FF',
  PRIMARY_DARK: '#073A7A',
  
  SUCCESS: '#178A5B',
  SUCCESS_LIGHT: '#EDF9F0',
  
  WARNING: '#D48A00',
  WARNING_LIGHT: '#FFFBEA',
  
  DANGER: '#D92D20',
  DANGER_LIGHT: '#FEF3F2',
  
  GRADE_S: '#178A5B',
  GRADE_A: '#84CC16',
  GRADE_B: '#D48A00',
  GRADE_C: '#E66A1F',
  GRADE_D: '#D92D20',
  
  BG_PAGE: '#F5F7FA',
  CARD_BG: '#FFFFFF',
  BORDER: '#DCE3EA',
  TEXT_MAIN: '#172B4D',
  TEXT_SUB: '#5E6C84',
};

export const ScoreThresholds = {
  TARGET_PASS: 911.0,
  TARGET_HALF_TOTAL: 1822.0,
  WARNING_ZONE: 895.0,
  HIGH_RISK_ZONE: 870.0,
};

export function getScoreBadge(
  score: number,
  expectedScore?: number,
  isInterim: boolean = false
): { text: string; bg: string; color: string; border: string } {
  const evalScore = (isInterim && expectedScore !== undefined) ? expectedScore : score;
  if (evalScore >= ScoreThresholds.TARGET_PASS) {
    return {
      text: isInterim ? '정상 궤도 (911 유력)' : '안전 (달성)',
      bg: Colors.SUCCESS_LIGHT,
      color: Colors.SUCCESS,
      border: '#B8E6CB',
    };
  } else if (evalScore >= ScoreThresholds.WARNING_ZONE) {
    return {
      text: isInterim ? '주의 (집중 코칭)' : '주의 (근접)',
      bg: Colors.WARNING_LIGHT,
      color: Colors.WARNING,
      border: '#FCE5B2',
    };
  } else {
    return {
      text: isInterim ? '위험 (오더 보강)' : '위험 (미달)',
      bg: Colors.DANGER_LIGHT,
      color: Colors.DANGER,
      border: '#FECDCA',
    };
  }
}

