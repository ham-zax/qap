export interface FormattedValue {
  display: string
  exact: string
}

function withMathMinus(value: string): string {
  return value.replace('-', '−')
}

export function formatRelativePercent(value: string): FormattedValue {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return { display: value, exact: value }

  const percent = numeric * 100
  const magnitude = Math.abs(percent)

  if (magnitude > 0 && magnitude < 0.01) {
    return {
      display: `${numeric < 0 ? '−' : '+'}<0.01%`,
      exact: value,
    }
  }

  const display = new Intl.NumberFormat('en-US', {
    signDisplay: numeric === 0 ? 'auto' : 'always',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(percent)

  return {
    display: `${withMathMinus(display)}%`,
    exact: value,
  }
}

export function formatResearchTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'UTC',
    timeZoneName: 'short',
  }).format(date)
}
