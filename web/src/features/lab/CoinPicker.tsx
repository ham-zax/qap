import { Check, ChevronDown, Search } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Separator } from '@/components/ui/separator'
import { AssetBadge } from '@/components/watermelon/asset-badge'
import { cn } from '@/lib/utils'
import { searchLabCoins } from './labApi'
import type { LabCoinMatch } from './labContract'

const POPULAR_CODES = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'LINK', 'ADA', 'AVAX', 'SUI']
const MAX_MATCHES = 80
const NO_COINS: LabCoinMatch[] = []

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

export function CoinPicker({
  label,
  value,
  coins,
  excluded,
  onChange,
}: {
  label: string
  value: string
  coins: LabCoinMatch[]
  excluded?: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState('')
  const [remote, setRemote] = useState<LabCoinMatch[]>(NO_COINS)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
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

  useEffect(() => {
    const needle = query.trim()
    if (!needle || local.length > 0) {
      setRemote(NO_COINS)
      setError('')
      return
    }
    const controller = new AbortController()
    void searchLabCoins(needle, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setRemote(result.coins)
          setError('')
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setError('Search unavailable. Try again.')
      })
    return () => controller.abort()
  }, [query, local.length])

  const pick = (coin: LabCoinMatch) => {
    setChosen(coin)
    onChange(coin.id)
    setOpen(false)
    triggerRef.current?.focus()
  }

  const current = selected ?? (chosen?.id === value ? chosen : undefined)
  const code = current?.code ?? value.replace('binance:', '')

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          ref={triggerRef}
          type="button"
          variant="outline"
          aria-label={`${label}: ${code}`}
          className="h-8 gap-1.5 rounded-md border-border-strong bg-background px-2 text-xs font-semibold text-foreground hover:border-foreground/60 hover:bg-muted"
        >
          <AssetBadge symbol={code} size="xs" />
          <span className="font-semibold tracking-tight">{code}</span>
          <ChevronDown
            className={cn(
              'size-3.5 text-muted-foreground transition-transform duration-150',
              open && 'rotate-180',
            )}
            aria-hidden="true"
          />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        sideOffset={6}
        className="w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-border-strong bg-card p-3 text-card-foreground shadow-xl"
      >
        <div className="space-y-2.5">
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              aria-label={`${label} search`}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name or ticker"
              autoComplete="off"
              spellCheck={false}
              className="h-8 bg-background pl-8 text-xs"
            />
          </div>

          {chips.length > 0 && (
            <>
              <div
                className="flex flex-wrap gap-1.5"
                role="group"
                aria-label={`${label} popular coins`}
              >
                {chips.map((coin) => {
                  const active = coin.id === value
                  return (
                    <Button
                      key={coin.id}
                      type="button"
                      size="sm"
                      variant={active ? 'default' : 'secondary'}
                      aria-pressed={active}
                      onClick={() => pick(coin)}
                      className="h-6 rounded-full px-2.5 text-[11px] font-semibold"
                    >
                      {coin.code}
                    </Button>
                  )
                })}
              </div>
              <Separator />
            </>
          )}

          {error && (
            <p role="alert" className="m-0 text-xs text-destructive">
              {error}
            </p>
          )}

          <div className="max-h-64 space-y-0.5 overflow-y-auto pr-1">
            {visible.slice(0, MAX_MATCHES).map((coin) => {
              const active = coin.id === value
              return (
                <button
                  key={coin.id}
                  type="button"
                  aria-current={active ? 'true' : undefined}
                  onClick={() => pick(coin)}
                  className={cn(
                    'flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-xs transition-colors hover:bg-muted',
                    active && 'bg-muted/80 ring-1 ring-border-strong',
                  )}
                >
                  <AssetBadge symbol={coin.code} size="xs" />
                  <strong className="min-w-12 font-semibold text-foreground">{coin.code}</strong>
                  <span className="min-w-0 flex-1 truncate text-muted-foreground">{coin.name}</span>
                  {active ? <Check className="size-3.5 shrink-0 text-primary" aria-hidden="true" /> : null}
                </button>
              )
            })}
            {!error && visible.length === 0 && (
              <p className="m-0 py-3 text-center text-xs text-muted-foreground">
                No eligible coins match.
              </p>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
