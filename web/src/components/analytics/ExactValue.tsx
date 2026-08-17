interface ExactValueProps {
  value: string
  label?: string
}

export function ExactValue({ value, label = 'Exact value' }: ExactValueProps) {
  return (
    <details className="mt-2 border-0 bg-transparent p-0 text-xs text-muted">
      <summary className="mb-0 w-fit cursor-pointer border-0 pb-0 font-medium text-secondary">
        {label}
      </summary>
      <code className="mt-2 block max-w-full overflow-x-auto rounded-md bg-canvas px-3 py-2 font-mono text-xs text-secondary">
        {value}
      </code>
    </details>
  )
}
