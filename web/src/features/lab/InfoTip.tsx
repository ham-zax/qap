import { useEffect, useId, useRef, useState } from 'react'

export interface InfoTipProps {
  label: string
  text: string
}

export function InfoTip({ label, text }: InfoTipProps) {
  const [open, setOpen] = useState(false)
  const tipId = useId()
  const rootRef = useRef<HTMLSpanElement | null>(null)

  useEffect(() => {
    if (!open) return
    function onDocClick(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <span className="bt-info-tip" ref={rootRef}>
      <button
        type="button"
        className="bt-info-btn"
        aria-label={label}
        aria-expanded={open}
        aria-describedby={open ? tipId : undefined}
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          setOpen((prev) => !prev)
        }}
      >
        i
      </button>
      {open && (
        <span id={tipId} role="tooltip" className="bt-info-popover">
          {text}
        </span>
      )}
    </span>
  )
}
