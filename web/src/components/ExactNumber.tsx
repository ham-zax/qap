interface ExactNumberProps {
  value: string
}

function formatExactNumber(value: string): string {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return value

  const significantDigits = value.replace(/^[+-]/, '').replace(/[.eE+-]/g, '').replace(/^0+/, '')
  if (significantDigits.length <= 10 && value.length <= 16) return value

  const magnitude = Math.abs(numeric)
  const notation =
    magnitude !== 0 && (magnitude >= 1_000_000_000 || magnitude < 0.000001)
      ? 'scientific'
      : 'standard'

  return new Intl.NumberFormat('en-US', {
    maximumSignificantDigits: 8,
    notation,
    useGrouping: true,
  }).format(numeric)
}

export function ExactNumber({ value }: ExactNumberProps) {
  const display = formatExactNumber(value)
  if (display === value) return value

  return (
    <span className="exact-number">
      <span aria-hidden="true" data-exact={value} title={`Exact: ${value}`}>
        {display}
      </span>
      <span className="sr-only">
        {display}; exact value {value}
      </span>
    </span>
  )
}
