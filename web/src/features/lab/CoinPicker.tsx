import { useEffect, useMemo, useRef, useState } from 'react'
import { searchLabCoins } from './labApi'
import type { LabCoinMatch } from './labContract'
import './CoinPicker.css'

const POPULAR_CODES = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'LINK', 'ADA', 'AVAX', 'SUI']
const MAX_MATCHES = 80
const NO_COINS: LabCoinMatch[] = []

function Chevron() {
  return <svg className="coin-picker-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="m6 9 6 6 6-6" />
  </svg>
}

/** Ticker prefix first, then name substring: the whole 396-coin directory filters in memory. */
function filterCoins(coins: LabCoinMatch[], query: string, excluded?: string): LabCoinMatch[] {
  const visible = excluded ? coins.filter((coin) => coin.id !== excluded) : coins
  const needle = query.trim().toLowerCase()
  if (!needle) return visible
  const prefix: LabCoinMatch[] = []
  const named: LabCoinMatch[] = []
  for (const coin of visible) {
    if (coin.code.toLowerCase().startsWith(needle)) prefix.push(coin)
    else if (coin.name.toLowerCase().includes(needle)) named.push(coin)
  }
  return [...prefix, ...named]
}

export function CoinPicker({ label, value, coins, excluded, onChange }: {
  label: string; value: string; coins: LabCoinMatch[]; excluded?: string; onChange: (id: string) => void
}) {
  const [query, setQuery] = useState('')
  const [remote, setRemote] = useState<LabCoinMatch[]>(NO_COINS)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const detailsRef = useRef<HTMLDetailsElement>(null)
  const selected = coins.find((coin) => coin.id === value)
  const [chosen, setChosen] = useState<LabCoinMatch | undefined>()

  const local = useMemo(() => filterCoins(coins, query, excluded), [coins, query, excluded])
  const remoteMatches = useMemo(() => filterCoins(remote, query, excluded), [remote, query, excluded])
  const visible = local.length > 0 ? local : remoteMatches

  const chips = useMemo(() => {
    if (coins.length <= 4) return NO_COINS
    const byCode = new Map(coins.map((coin) => [coin.code, coin]))
    return POPULAR_CODES
      .map((code) => byCode.get(code))
      .filter((coin): coin is LabCoinMatch => Boolean(coin) && coin!.id !== excluded)
  }, [coins, excluded])

  // The local directory answers instantly; the network is only a fallback for a miss.
  useEffect(() => {
    const needle = query.trim()
    if (!needle || local.length > 0) { setRemote(NO_COINS); setError(''); return }
    const controller = new AbortController()
    void searchLabCoins(needle, controller.signal)
      .then((result) => { if (!controller.signal.aborted) { setRemote(result.coins); setError('') } })
      .catch(() => { if (!controller.signal.aborted) setError('Search unavailable. Try again.') })
    return () => controller.abort()
  }, [query, local.length])

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
  const pick = (coin: LabCoinMatch) => { setChosen(coin); onChange(coin.id); close() }
  const current = selected ?? (chosen?.id === value ? chosen : undefined)
  const code = current?.code ?? value.replace('binance:', '')

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
      {chips.length > 0 && <div className="coin-picker-chips" role="group" aria-label={`${label} popular coins`}>
        {chips.map((coin) => <button type="button" key={coin.id} aria-pressed={coin.id === value}
          onClick={() => pick(coin)}>{coin.code}</button>)}
      </div>}
      {error && <p role="alert" className="coin-picker-message">{error}</p>}
      <div className="coin-picker-results">
        {visible.slice(0, MAX_MATCHES).map((coin) => <button type="button" key={coin.id} aria-current={coin.id === value ? 'true' : undefined}
          onClick={() => pick(coin)}>
          <strong>{coin.code}</strong><span>{coin.name}</span>
        </button>)}
        {!error && visible.length === 0 && <p className="coin-picker-message">No eligible coins match.</p>}
      </div>
    </div>
  </details>
}
