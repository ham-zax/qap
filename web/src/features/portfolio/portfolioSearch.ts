export interface PortfolioSearch {
  decision?: string
}

function stringValue(value: unknown): string | null {
  if (typeof value !== 'string') return null
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

export function parsePortfolioSearch(raw: Record<string, unknown>): PortfolioSearch {
  return { decision: stringValue(raw.decision) ?? undefined }
}

export function canonicalPortfolioSearch(
  input: PortfolioSearch,
  decisions: readonly { decision_id: string }[],
): { search: PortfolioSearch; changed: boolean } {
  const firstDecision = decisions[0]?.decision_id
  const decision =
    input.decision && decisions.some((item) => item.decision_id === input.decision)
      ? input.decision
      : firstDecision
  return {
    search: { decision },
    changed: decision !== input.decision,
  }
}
