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
  if (evalScore >= 930) {
    return {
      text: isInterim ? 'S등급 (최우수)' : 'S등급 (최우수)',
      bg: '#DCFCE7',
      color: '#15803D',
      border: '#86EFAC',
    };
  } else if (evalScore >= 911) {
    return {
      text: isInterim ? 'A등급 (우수)' : 'A등급 (우수)',
      bg: '#E0E7FF',
      color: '#3730A3',
      border: '#A5B4FC',
    };
  } else if (evalScore >= 895) {
    return {
      text: isInterim ? 'B등급 (보통)' : 'B등급 (보통)',
      bg: '#FEF3C7',
      color: '#B45309',
      border: '#FDE68A',
    };
  } else if (evalScore >= 875) {
    return {
      text: isInterim ? 'C등급 (주의)' : 'C등급 (주의)',
      bg: '#FFEDD5',
      color: '#C2410C',
      border: '#FED7AA',
    };
  } else {
    return {
      text: isInterim ? 'D등급 (미달위험)' : 'D등급 (미달)',
      bg: '#FEE2E2',
      color: '#991B1B',
      border: '#FCA5A5',
    };
  }
}

