import { useEffect, useRef, useState } from 'react'
import { searchLabCoins } from './labApi'
import type { LabCoinMatch } from './labContract'
import './CoinPicker.css'

function Chevron() {
  return <svg className="coin-picker-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m6 9 6 6 6-6" />
  </svg>
}

export function CoinPicker({ label, value, coins, excluded, onChange }: {
  label: string; value: string; coins: LabCoinMatch[]; excluded?: string; onChange: (id: string) => void
}) {
  const [query, setQuery] = useState('')
  const [matches, setMatches] = useState<LabCoinMatch[]>(coins)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const detailsRef = useRef<HTMLDetailsElement>(null)
  const selected = coins.find((coin) => coin.id === value)
  const [chosen, setChosen] = useState<LabCoinMatch | undefined>()
  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => {
      if (!query) { setMatches(coins); setError(''); return }
      void searchLabCoins(query, controller.signal).then((result) => {
        if (!controller.signal.aborted) { setMatches(result.coins); setError('') }
      }).catch(() => { if (!controller.signal.aborted) setError('Search unavailable. Try again.') })
    }, 200)
    return () => { clearTimeout(timer); controller.abort() }
  }, [query, coins])
  // An open menu closes on an outside pointer press, like a native select.
  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => {
      if (!detailsRef.current?.contains(event.target as Node)) detailsRef.current?.removeAttribute('open')
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])
  const close = () => {
    const details = detailsRef.current
    if (!details) return
    details.removeAttribute('open')
    details.querySelector('summary')?.focus()
  }
  const current = selected ?? (chosen?.id === value ? chosen : undefined)
  const code = current?.code ?? value.replace('binance:', '')
  const visible = matches.filter((coin) => coin.id !== excluded)
  return <details ref={detailsRef} className="coin-picker" onToggle={(event) => setOpen(event.currentTarget.open)}
    onKeyDown={(event) => { if (event.key === 'Escape' && open) { event.preventDefault(); close() } }}>
    <summary aria-label={`${label}: ${code}`}>
      <span className="coin-picker-label">{label}</span>
      <span className="coin-picker-control">
        <strong>{code}</strong>
        {current?.name && current.name !== code && <span className="coin-picker-name">{current.name}</span>}
        <Chevron />
      </span>
    </summary>
    <div className="coin-picker-menu">
      <label>{label} search<input aria-label={`${label} search`} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name or ticker" autoComplete="off" spellCheck={false} /></label>
      {error && <p role="alert" className="coin-picker-message">{error}</p>}
      <div className="coin-picker-results">
        {visible.slice(0, 30).map((coin) => <button type="button" key={coin.id} aria-current={coin.id === value ? 'true' : undefined}
          onClick={() => { setChosen(coin); onChange(coin.id); close() }}>
          <strong>{coin.code}</strong><span>{coin.name}</span>
        </button>)}
        {!error && visible.length === 0 && <p className="coin-picker-message">No eligible coins match.</p>}
      </div>
    </div>
  </details>
}
