interface BasketGraphEdge {
  pair: string
  label?: string
}

interface BasketGraphProps {
  assets: string[]
  edges: BasketGraphEdge[]
}

export function BasketGraph({ assets, edges }: BasketGraphProps) {
  const size = 280
  const center = size / 2
  const radius = 96
  const positions = new Map(
    assets.map((asset, index) => {
      const angle =
        (Math.PI * 2 * index) / Math.max(assets.length, 1) - Math.PI / 2
      return [
        asset,
        {
          x: center + radius * Math.cos(angle),
          y: center + radius * Math.sin(angle),
        },
      ] as const
    }),
  )

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="mx-auto w-full max-w-[20rem]"
      role="img"
      aria-label="Basket topology"
    >
      {edges.map((edge) => {
        const [left, right] = edge.pair.split('/')
        const a = positions.get(left)
        const b = positions.get(right)
        if (!a || !b) return null
        return (
          <g key={edge.pair}>
            <line
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke="currentColor"
              className="text-accent"
              strokeWidth="2"
            />
            {edge.label ? (
              <title>
                {edge.pair}: {edge.label}
              </title>
            ) : null}
          </g>
        )
      })}
      {assets.map((asset) => {
        const point = positions.get(asset)
        if (!point) return null
        return (
          <g key={asset}>
            <circle
              cx={point.x}
              cy={point.y}
              r="24"
              fill="currentColor"
              className="text-panel"
              stroke="currentColor"
              strokeWidth="2"
            />
            <text
              x={point.x}
              y={point.y + 4}
              textAnchor="middle"
              className="fill-foreground text-[11px] font-semibold"
            >
              {asset}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
