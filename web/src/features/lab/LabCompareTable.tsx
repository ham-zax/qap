import { ChevronsUpDown, Trophy, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { DetailTag } from '@/components/watermelon/dashboard-card'
import { cn } from '@/lib/utils'
import type { LabCompareResult } from './labStudyApi'

interface LabCompareTableProps {
  compare: LabCompareResult
  onOpenStudy: (studyId: string) => void
  onClose: () => void
}

type SortField = 'ending' | 'hodl' | 'control' | 'swaps'

function pct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function dollars(value: unknown): string {
  const amount = Number(value)
  return value == null || !Number.isFinite(amount)
    ? '—'
    : amount.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })
}

export function LabCompareTable({ compare, onOpenStudy, onClose }: LabCompareTableProps) {
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  function handleSort(field: SortField) {
    if (sortField === field) {
      if (sortDir === 'desc') setSortDir('asc')
      else {
        setSortField(null)
        setSortDir('desc')
      }
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const rows = useMemo(() => {
    if (!sortField) return compare.studies
    return [...compare.studies].sort((left, right) => {
      const valueOf = (item: (typeof compare.studies)[number]): number => {
        if (sortField === 'ending') return Number(item.result.wealth?.terminal_values.strategy ?? 0)
        if (sortField === 'hodl') return item.result.proof.vs_hodl_pct ?? -Infinity
        if (sortField === 'control') return item.result.proof.vs_control_pct ?? -Infinity
        return item.result.proof.validation_trades ?? 0
      }
      const delta = valueOf(left) - valueOf(right)
      return sortDir === 'asc' ? delta : -delta
    })
  }, [compare.studies, sortField, sortDir])

  return (
    <Card role="region" className="shadow-primary gap-3 rounded-xl py-4" aria-label="Preset comparison">
      <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3 px-4 pb-0">
        <div className="space-y-1">
          <CardTitle>
            <h2 className="m-0 text-sm font-semibold text-foreground">
              Preset Comparison ({compare.studies.length} candidates)
            </h2>
          </CardTitle>
          <CardDescription className="text-xs">{compare.advisor.simple_summary}</CardDescription>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={onClose} className="h-7 gap-1 px-2.5 text-xs">
          <X className="size-3.5" aria-hidden="true" />
          Close comparison
        </Button>
      </CardHeader>

      <CardContent className="px-4">
        <div className="overflow-hidden rounded-lg border border-border">
          <Table>
            <TableHeader className="bg-muted/60">
              <TableRow>
                <TableHead className="h-9 text-xs">Method</TableHead>
                <TableHead className="h-9 text-xs">Hedge / Lookback</TableHead>
                <TableHead className="h-9 text-right text-xs">
                  <button
                    type="button"
                    onClick={() => handleSort('ending')}
                    className="inline-flex items-center gap-1 hover:text-foreground"
                  >
                    Ending $10,000
                    <ChevronsUpDown className="size-3" aria-hidden="true" />
                  </button>
                </TableHead>
                <TableHead className="h-9 text-right text-xs">
                  <button
                    type="button"
                    onClick={() => handleSort('hodl')}
                    className="inline-flex items-center gap-1 hover:text-foreground"
                  >
                    vs Hold
                    <ChevronsUpDown className="size-3" aria-hidden="true" />
                  </button>
                </TableHead>
                <TableHead className="h-9 text-right text-xs">
                  <button
                    type="button"
                    onClick={() => handleSort('control')}
                    className="inline-flex items-center gap-1 hover:text-foreground"
                  >
                    vs Rebalance
                    <ChevronsUpDown className="size-3" aria-hidden="true" />
                  </button>
                </TableHead>
                <TableHead className="h-9 text-xs">Folds</TableHead>
                <TableHead className="h-9 text-right text-xs">
                  <button
                    type="button"
                    onClick={() => handleSort('swaps')}
                    className="inline-flex items-center gap-1 hover:text-foreground"
                  >
                    Swaps
                    <ChevronsUpDown className="size-3" aria-hidden="true" />
                  </button>
                </TableHead>
                <TableHead className="h-9 text-right text-xs">Fees</TableHead>
                <TableHead className="h-9 text-xs">Verdict</TableHead>
                <TableHead className="h-9 text-right text-xs" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((item) => {
                const best = item.study_id === compare.best_study_id
                const applied = item.result.applied_settings
                const vsHodl = item.result.proof.vs_hodl_pct ?? 0
                const vsCtrl = item.result.proof.vs_control_pct ?? 0
                return (
                  <TableRow key={item.study_id} className={cn(best && 'bg-primary/8')}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <strong>{applied.method}</strong>
                        {best && (
                          <Badge className="gap-1 bg-primary/15 text-primary hover:bg-primary/20">
                            <Trophy className="size-3" aria-hidden="true" />
                            Best
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {applied.hedge_method} · {applied.lookback}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs tabular-nums">
                      {dollars(item.result.wealth?.terminal_values.strategy)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DetailTag tone={vsHodl > 0 ? 'positive' : 'negative'}>
                        {pct(item.result.proof.vs_hodl_pct)}
                      </DetailTag>
                    </TableCell>
                    <TableCell className="text-right">
                      <DetailTag tone={vsCtrl > 0 ? 'positive' : 'negative'}>
                        {pct(item.result.proof.vs_control_pct)}
                      </DetailTag>
                    </TableCell>
                    <TableCell className="font-mono text-xs tabular-nums">
                      {item.result.proof.folds_passing}/{item.result.proof.folds_total}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs tabular-nums">
                      {item.result.proof.validation_trades}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs tabular-nums">
                      {dollars(item.result.statistics?.strategy?.fees_usdt)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{item.result.call.headline}</TableCell>
                    <TableCell className="text-right">
                      <Button type="button" variant="outline" size="sm" onClick={() => onOpenStudy(item.study_id)} className="h-7 px-2.5 text-xs">
                        Inspect
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
