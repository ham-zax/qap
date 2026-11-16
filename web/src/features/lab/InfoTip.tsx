import { Info } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

export interface InfoTipProps {
  label: string
  text: string
  align?: 'left' | 'right'
}

export function InfoTip({ label, text, align = 'left' }: InfoTipProps) {
  const [open, setOpen] = useState(false)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label={label}
          aria-expanded={open}
          onClick={(event) => {
            event.stopPropagation()
          }}
          className="size-5 rounded-full border border-border-strong bg-muted p-0 text-muted-foreground hover:border-primary hover:text-foreground"
        >
          <Info className="size-3" aria-hidden="true" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        role="tooltip"
        align={align === 'right' ? 'end' : 'start'}
        sideOffset={6}
        className="w-64 max-w-[75vw] rounded-lg border border-border-strong bg-popover p-3 text-xs leading-relaxed text-popover-foreground shadow-lg"
      >
        {text}
      </PopoverContent>
    </Popover>
  )
}
