import type { ReactNode } from 'react'

interface TableScrollProps {
  label: string
  children: ReactNode
}

export function TableScroll({ label, children }: TableScrollProps) {
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label={`${label} table`}
      tabIndex={0}
    >
      {children}
    </div>
  )
}
