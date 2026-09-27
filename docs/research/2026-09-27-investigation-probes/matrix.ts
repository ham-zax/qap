import { readFileSync } from 'node:fs'
import { rankResearchAssetOptions, researchAssetOptions } from './ras.ts'
const universe = JSON.parse(readFileSync(new URL('./ru.json', import.meta.url), 'utf8'))
const options = researchAssetOptions(universe)
console.log('options', options.length)
for (const q of ['W', 'w', 'Wormhole', 'WUSDT', 'W_USDT', 'W/USDT', ' wusdt ', 'BTC', 'Bitcoin', 'DAI', 'ETH', 'Ethereum', 'PIXEL', 'SOL', 'ADA']) {
  const top = rankResearchAssetOptions(options, q).slice(0, 5)
  console.log(JSON.stringify(q).padEnd(12), top.length ? top.map((o) => `${o.symbol}${o.venue ? '@' + o.venue : ''}[${o.venueSymbols.slice(0, 2).join(',')}]${o.canonicalAssetId ? '' : '*'}`).join(' | ') : '(no match)')
}
