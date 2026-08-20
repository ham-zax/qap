import { useEffect, useState } from 'react'

import type { CapabilityMetadataV1 } from '../../api/types'

function humanize(value: string): string {
  return value.replaceAll('_', ' ')
}

export function JsonConfigEditor({
  label,
  value,
  onApply,
}: {
  label: string
  value: Record<string, unknown>
  onApply: (value: Record<string, unknown>) => void
}) {
  const [text, setText] = useState(() => JSON.stringify(value, null, 2))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => setText(JSON.stringify(value, null, 2)), [value])

  return (
    <div>
      <label className="block text-xs font-semibold text-secondary">
        {label}
        <textarea
          className="mt-1 min-h-28 w-full rounded-md border border-border bg-canvas p-3 font-mono text-xs text-foreground"
          value={text}
          onChange={(event) => setText(event.target.value)}
          spellCheck={false}
        />
      </label>
      <button
        type="button"
        className="mt-2 min-h-9 rounded-md border border-border px-3 text-xs font-semibold text-foreground"
        onClick={() => {
          try {
            const parsed: unknown = JSON.parse(text)
            if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
              throw new Error('Configuration must be a JSON object.')
            }
            onApply(parsed as Record<string, unknown>)
            setError(null)
          } catch (caught) {
            setError(
              caught instanceof Error
                ? caught.message
                : 'Invalid JSON configuration.',
            )
          }
        }}
      >
        Apply exact config
      </button>
      {error ? <p className="mt-2 text-xs text-negative">{error}</p> : null}
    </div>
  )
}

export function ComponentSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: CapabilityMetadataV1[]
  onChange: (value: string) => void
}) {
  return (
    <label className="text-xs font-semibold text-secondary">
      {label}
      <select
        className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((item) => (
          <option key={`${item.kind}-${item.component_id}`} value={item.component_id}>
            {humanize(item.component_id)} · {humanize(item.capability)}
          </option>
        ))}
      </select>
    </label>
  )
}
