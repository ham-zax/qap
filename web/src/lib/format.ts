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

export function formatPercent(value: string): FormattedValue {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return { display: value, exact: value }

  const percent = numeric * 100
  const magnitude = Math.abs(percent)
  if (magnitude > 0 && magnitude < 0.01) {
    return { display: `${numeric < 0 ? '−' : ''}<0.01%`, exact: value }
  }

  const display = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: magnitude < 10 ? 2 : 1,
    maximumFractionDigits: 2,
  }).format(percent)
  return { display: `${withMathMinus(display)}%`, exact: value }
}

export function formatDecimal(value: string, maximumFractionDigits = 2): FormattedValue {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return { display: value, exact: value }
  return {
    display: withMathMinus(
      new Intl.NumberFormat('en-US', {
        maximumFractionDigits,
      }).format(numeric),
    ),
    exact: value,
  }
}

export function formatSignedDecimal(
  value: string,
  maximumFractionDigits = 2,
): FormattedValue {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return { display: value, exact: value }
  return {
    display: withMathMinus(
      new Intl.NumberFormat('en-US', {
        maximumFractionDigits,
        signDisplay: numeric === 0 ? 'auto' : 'always',
      }).format(numeric),
    ),
    exact: value,
  }
}

export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return `${seconds} seconds`
  if (seconds < 60) return `${Math.round(seconds)}s`
  const totalMinutes = Math.round(seconds / 60)
  if (totalMinutes < 60) return `${totalMinutes}m`
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours < 24) return minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  return remainingHours === 0 ? `${days}d` : `${days}d ${remainingHours}h`
}

export function formatResearchDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(date)
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
