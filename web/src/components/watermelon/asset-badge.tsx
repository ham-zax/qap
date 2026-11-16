import { cn } from '@/lib/utils'

const ASSET_COLORS: Record<string, string> = {
  BTC: 'bg-amber-500 text-zinc-950',
  ETH: 'bg-indigo-400 text-zinc-950',
  SOL: 'bg-violet-500 text-white',
  BNB: 'bg-yellow-400 text-zinc-950',
  XRP: 'bg-sky-500 text-white',
  DOGE: 'bg-yellow-500 text-zinc-950',
  LINK: 'bg-blue-600 text-white',
  ADA: 'bg-blue-500 text-white',
  AVAX: 'bg-rose-500 text-white',
  SUI: 'bg-cyan-500 text-zinc-950',
  USDT: 'bg-emerald-500 text-zinc-950',
}

const FALLBACK_PALETTE = [
  'bg-sky-600 text-white',
  'bg-teal-600 text-white',
  'bg-indigo-600 text-white',
  'bg-amber-600 text-zinc-950',
  'bg-emerald-600 text-white',
  'bg-violet-600 text-white',
] as const

function colorForSymbol(symbol: string): string {
  const upper = symbol.toUpperCase()
  if (ASSET_COLORS[upper]) return ASSET_COLORS[upper]
  let hash = 0
  for (let i = 0; i < upper.length; i += 1) {
    hash = (hash * 31 + upper.charCodeAt(i)) >>> 0
  }
  return FALLBACK_PALETTE[hash % FALLBACK_PALETTE.length]
}

export function AssetBadge({
  symbol,
  size = 'sm',
  className,
}: {
  symbol: string
  size?: 'xs' | 'sm' | 'md'
  className?: string
}) {
  const clean = symbol.replace(/^binance:/i, '').toUpperCase()
  const label = clean.slice(0, 1) || '?'

  return (
    <span
      aria-hidden="true"
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full font-semibold shadow-[inset_0_1px_2px_1px_rgba(255,255,255,0.2),inset_0_-1px_2px_1px_rgba(0,0,0,0.12)]',
        size === 'xs' && 'size-5 text-[10px]',
        size === 'sm' && 'size-6 text-[11px]',
        size === 'md' && 'size-8 text-xs',
        colorForSymbol(clean),
        className,
      )}
    >
      {label}
    </span>
  )
}
