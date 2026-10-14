with open('src/utils/styles.ts', 'r', encoding='utf-8') as f:
    text = f.read()

old_badge_func = '''export function getScoreBadge(
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
}'''

new_badge_func = '''export function getScoreBadge(
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
}'''

if old_badge_func in text:
    text = text.replace(old_badge_func, new_badge_func)
    with open('src/utils/styles.ts', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated src/utils/styles.ts!')

# Now update src/components/pages/PerformancePage.tsx
with open('src/components/pages/PerformancePage.tsx', 'r', encoding='utf-8') as f:
    perf_text = f.read()

old_call = 'const badge = getScoreBadge(r.총점);'
new_call = 'const isInterim = periodInfo.month_in_half < 6;\n                const badge = getScoreBadge(r.총점, r.예상반기총점, isInterim);'

if old_call in perf_text:
    perf_text = perf_text.replace(old_call, new_call)
    with open('src/components/pages/PerformancePage.tsx', 'w', encoding='utf-8') as f:
        f.write(perf_text)
    print('Updated src/components/pages/PerformancePage.tsx!')

