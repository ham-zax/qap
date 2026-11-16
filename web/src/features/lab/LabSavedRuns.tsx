import { Pin, PinOff } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AssetBadge } from '@/components/watermelon/asset-badge'
import { cn } from '@/lib/utils'
import type { LabSavedSummary } from './labStudyApi'

interface LabSavedRunsProps {
  studies: readonly LabSavedSummary[]
  activeStudyId: string | null
  loading: boolean
  onSelect: (studyId: string) => void
  onTogglePin: (studyId: string, pinned: boolean) => void
}

export function LabSavedRuns({
  studies,
  activeStudyId,
  loading,
  onSelect,
  onTogglePin,
}: LabSavedRunsProps) {
  return (
    <Card role="region" className="shadow-primary gap-3 rounded-xl py-4" aria-label="Saved and pinned studies">
      <CardHeader className="flex flex-row items-center justify-between gap-2 px-4 pb-0">
        <CardTitle>
          <h3 className="m-0 text-sm font-semibold text-foreground">Saved &amp; Pinned Studies</h3>
        </CardTitle>
        {studies.length > 0 && (
          <Badge variant="secondary" className="font-mono text-xs">
            {studies.length}
          </Badge>
        )}
      </CardHeader>

      <CardContent className="px-4">
        {loading && studies.length === 0 ? (
          <p className="m-0 text-xs text-muted-foreground">Loading saved studies…</p>
        ) : studies.length === 0 ? (
          <p className="m-0 text-xs text-muted-foreground">
            No saved studies yet. Run a test to record it here.
          </p>
        ) : (
          <ul className="m-0 grid list-none gap-2 p-0 sm:grid-cols-2">
            {studies.map((row) => {
              const active = row.study_id === activeStudyId
              return (
                <li
                  key={row.study_id}
                  className={cn(
                    'flex items-center gap-2 rounded-lg border bg-muted/35 p-2 transition-colors',
                    active ? 'border-primary ring-1 ring-primary/30' : 'border-border hover:border-border-strong',
                  )}
                >
                  <AssetBadge symbol={row.coin_a.code} size="xs" />
                  <button
                    type="button"
                    className="flex min-w-0 flex-1 flex-col items-start gap-0.5 text-left"
                    onClick={() => onSelect(row.study_id)}
                  >
                    <span className="font-mono text-xs text-muted-foreground">
                      {row.coin_a.code}/{row.coin_b.code} · {row.method}
                    </span>
                    <span className="w-full truncate text-xs font-medium text-foreground">
                      {row.headline}
                    </span>
                  </button>
                  <Button
                    type="button"
                    size="sm"
                    variant={row.pinned ? 'secondary' : 'outline'}
                    aria-label={
                      row.pinned
                        ? `Unpin ${row.coin_a.code}/${row.coin_b.code}`
                        : `Pin ${row.coin_a.code}/${row.coin_b.code}`
                    }
                    aria-pressed={row.pinned}
                    onClick={() => onTogglePin(row.study_id, !row.pinned)}
                    className="h-7 shrink-0 gap-1 px-2.5 text-[11px]"
                  >
                    {row.pinned ? <PinOff className="size-3" aria-hidden="true" /> : <Pin className="size-3" aria-hidden="true" />}
                    {row.pinned ? 'Pinned' : 'Pin'}
                  </Button>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
