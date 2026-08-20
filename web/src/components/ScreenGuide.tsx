interface ScreenGuideContent {
  intent: string
  action: string
  example: string
  next: string
  boundary: string
}

const guides = {
  home: {
    intent: 'See the state of this local research workspace and choose the next valid task.',
    action:
      'Start with the setup/readiness message or the resume card. Clear operational blockers before starting new research.',
    example:
      'If market data is not prepared, complete setup first. If a timeframe is ready, continue to Research and find ideas.',
    next: 'QAP opens the workflow that owns the next action and keeps scientific decisions out of Home.',
    boundary:
      'A failed background task is an operational problem, not negative research, and Home never recommends a trade.',
  },
  universe: {
    intent:
      'Tell QAP which venue asset codes represent the economic assets you mean and which canonical assets it is allowed to research.',
    action:
      'Load current markets, resolve required quote identities first, confirm base-asset identities only with independent evidence, then approve canonical assets separately.',
    example:
      'After independently confirming that Binance BTC is the same canonical BTC identity you intend to research, map that venue code to canonical BTC and its confirmed identity version. Approve BTC separately.',
    next:
      'Resolved and approved markets can move into market-data preparation and timeframe readiness checks.',
    boundary:
      'Matching ticker text is not identity evidence. An identity mapping is not approval, and approval is not the same as data readiness.',
  },
  research: {
    intent:
      'Start from a concrete research question: research one pair, scan the approved universe, or declare an advanced typed experiment.',
    action:
      'Choose one Research task. For a pair, select two assets and one timeframe, resolve only genuine identity or approval setup, then use Research this pair. QAP prepares only that pair when needed and shows relationship evidence before economic replay support.',
    example:
      'Select W and PIXEL, choose Medium-term, and research the relationship on their same-venue USDT paths. A missing direct W/PIXEL market limits economic replay; it does not erase the relationship study.',
    next:
      'Pair Research shows current backend relationship values first and only checks a default economic recipe when one can be truthfully declared. Universal Scan and Experiment Lab keep their existing authorities.',
    boundary:
      'The browser does not decide method support, scientific compatibility, or trade attractiveness, and no Research action authorizes a live trade.',
  },
  scan: {
    intent: 'Understand exactly what one completed research generation tested and what survived.',
    action:
      'Read the research claim and data boundary first, then inspect stage counts, Research Ideas, rejected evidence, and unavailable replay evidence.',
    example:
      'A completed generation with zero Research Ideas is still a valid scientific result; it is not the same as a failed task.',
    next: 'Open a Research Idea to inspect its historical, later, and current evidence layers.',
    boundary:
      'Stage counts have specific backend meanings; they are not asset counts, success probabilities, or trade recommendations.',
  },
  candidate: {
    intent: 'Inspect the evidence history for one research relationship without collapsing different evidence layers.',
    action:
      'Start with the original historical result, then read later prospective evidence and current capacity evidence. Use only actions the backend exposes for this claim.',
    example:
      'A relationship may be historically supported while later evidence is not supported. Both statements can remain true at the same time.',
    next:
      'When available, follow the all-survivor evidence stream, inspect a current amount assessment, or open related portfolio research.',
    boundary:
      'Later evidence does not rewrite an earlier valid historical claim, and this screen does not authorize a live trade.',
  },
  prospectiveList: {
    intent: 'Track all historically surviving ideas forward without choosing winners after seeing later outcomes.',
    action:
      'Open a cohort to see its frozen membership, completed checkpoints, reselections, and current assessments.',
    example:
      'If three ideas survived historical checks, QAP follows all three rather than selecting only the one that later looks best.',
    next: 'Use the cohort detail to advance due evidence and inspect the active evidence stream.',
    boundary:
      'Prospective follow-up is later evidence. It does not change what the original historical research did or did not establish.',
  },
  prospectiveDetail: {
    intent: 'See how one frozen all-survivor cohort evolved after the original research date.',
    action:
      'Review selection membership, active reselection lineage, checkpoints, current public-evidence readiness, and amount assessments in time order.',
    example:
      'A reselection can point a later candidate to the same active evidence stream without creating a second historical freeze.',
    next:
      'Advance the cohort or assess an amount only when the backend marks that action as valid for the current evidence state.',
    boundary:
      'Forward evidence, public-market capture, and capital assessment are distinct from historical replay evidence.',
  },
  baskets: {
    intent: 'Build a manual 3–6 asset portfolio study from existing relationship evidence.',
    action:
      'Choose the research source, select 3–6 economic assets, choose the exact relationship candidate for each edge you want to use, then run the portfolio analysis.',
    example:
      'BTC, ETH, and SOL can form a study where BTC/ETH uses one selected relationship edge while SOL remains isolated and therefore neutral.',
    next:
      'QAP runs the existing basket resolver and economic replay, then stores the result for Portfolio detail and History.',
    boundary:
      'This is manual research, not automatic portfolio discovery, optimization, or a recommendation to allocate capital.',
  },
  basketDetail: {
    intent: 'Interpret one completed portfolio study against QAP’s declared HODL/control objective.',
    action:
      'Read the research source and result state first, then compare HODL/control outcomes, drawdown, time-below, costs, turnover, allocations, and concentration.',
    example:
      'A basket can complete successfully yet trail its HODL/control benchmark after costs; that is valid negative research, not an application error.',
    next:
      'Use History for the longitudinal story or open the exact QAP run and audit lineage when you need specialist evidence.',
    boundary:
      'Terminal holdings differences are not causal asset-level P&L attribution, and no portfolio result authorizes live trading.',
  },
  history: {
    intent: 'Understand what QAP tested, what happened later, and how evidence changed over time.',
    action:
      'Start with Research Ideas, compare original historical evidence with later/current evidence, then open linked portfolio or specialist evidence only when needed.',
    example:
      'History can show “historical replay supported” together with “later evidence not supported” without replacing either claim.',
    next:
      'Open the Research Idea, forward cohort, portfolio study, or QAP run when you need the underlying immutable evidence.',
    boundary:
      'History does not stamp today’s approval/readiness state onto past research and does not create a second scientific verdict.',
  },
  experiment: {
    intent: 'Inspect one authoritative QAP economic run in detail.',
    action:
      'Read the run status, declared benchmark/control frame, information boundary, and persisted result roles before inspecting deeper evidence.',
    example:
      'Compare the strategy with the declared primary control and matched HODL using the values persisted by the run.',
    next: 'Open linked portfolio, pair, or lineage evidence when you need to explain how the run behaved.',
    boundary:
      'This specialist economic evidence is not a separate Product recommendation and the browser does not recalculate the verdict.',
  },
  portfolio: {
    intent: 'Inspect the holdings, costs, concentration, and rebalance evidence produced by one QAP run.',
    action:
      'Compare starting and terminal holdings, then review costs, concentration, allocation history, and rebalance audit evidence.',
    example:
      'Use the starting-versus-terminal allocation views to see what changed, then use the audit trail to see why a rebalance target was produced.',
    next: 'Return to the Portfolio study or open pair evidence for more specific relationship context.',
    boundary:
      'Holdings changes and terminal value differences are not causal profit attribution to a single asset or relationship.',
  },
  pair: {
    intent: 'Inspect one pair relationship inside an authoritative research/economic run.',
    action:
      'Confirm the selected orientation and anchor, then read the ratio/relationship charts and model evidence in that declared context.',
    example:
      'BTC/ETH and ETH/BTC are different orientations; inspect the one actually used by the research artifact rather than assuming they are interchangeable.',
    next: 'Return to the owning Research Idea, scan, or portfolio after you have answered the specific pair-level question.',
    boundary:
      'A visually interesting ratio or chart does not by itself establish a valid Research Idea, portfolio edge, or trade.',
  },
  operations: {
    intent: 'Monitor background operational tasks separately from scientific research results.',
    action:
      'Check which task is running, completed, failed, or interrupted. Open a task when you need its failure reason or terminal evidence link.',
    example:
      'A market-data or research task can fail because of an operational problem even though no negative scientific conclusion was reached.',
    next: 'Return to the owning Product workflow to retry or continue after resolving the operational issue.',
    boundary:
      'Activity status is operational state. Failed or interrupted does not mean the research hypothesis was rejected.',
  },
  operationDetail: {
    intent: 'Diagnose one background operation and find the evidence it produced, if any.',
    action:
      'Read status and failure information first, then timing, request summary, and the terminal evidence link when one exists.',
    example:
      'An interrupted scan has an operational record but no implied scientific conclusion; a completed scan links to its persisted research evidence.',
    next: 'Use the terminal evidence link or return to the owning workflow for the next valid action.',
    boundary:
      'The operation record reports execution state; it is not the scientific or economic authority for the resulting artifact.',
  },
  paperList: {
    intent: 'Review operational paper dry runs without mixing them with scientific support.',
    action:
      'Use reconciliation, fills, costs, residuals, and exception state to inspect whether the operational dry run behaved as recorded.',
    example:
      'A reconciled paper rebalance can demonstrate operational consistency while still providing no scientific support for the strategy.',
    next: 'Open a paper operation for exact holdings, fills, reconciliation, and exception evidence.',
    boundary:
      'Paper operations are operational dry runs. They are not live orders, investment recommendations, or scientific validation.',
  },
  paperDetail: {
    intent: 'Inspect one paper dry run as operational evidence.',
    action:
      'Read reconciliation and exception state first, then inspect holdings, fills, fees, slippage, tracking, and exact audit information.',
    example:
      'A paper run can reconcile exactly while the underlying research remains unsupported; those are separate questions.',
    next: 'Return to History or the owning research artifact when you need the scientific context.',
    boundary:
      'This screen describes a simulated operational run only; it does not prove scientific support or authorize live trading.',
  },
} satisfies Record<string, ScreenGuideContent>

function normalizedPath(pathname: string) {
  if (pathname === '/') return pathname
  return pathname.replace(/\/+$/, '')
}

export function screenGuideForPath(pathname: string): ScreenGuideContent | null {
  const path = normalizedPath(pathname)
  const parts = path.split('/').filter(Boolean)
  const root = parts[0]

  if (path === '/') return guides.home
  if (path === '/universe') return guides.universe
  if (root === 'scanner' && parts.length === 1) return guides.research
  if (root === 'scanner' && parts.length > 1) return guides.scan
  if (root === 'candidate') return guides.candidate
  if (root === 'prospective' && parts.length === 1) return guides.prospectiveList
  if (root === 'prospective') return guides.prospectiveDetail
  if (root === 'baskets' && parts.length === 1) return guides.baskets
  if (root === 'baskets') return guides.basketDetail
  if (root === 'experiments' && parts.length === 1) return guides.history
  if (root === 'experiments') return guides.experiment
  if (root === 'portfolio') return guides.portfolio
  if (root === 'pair') return guides.pair
  if (root === 'operations' && parts.length === 1) return guides.operations
  if (root === 'operations') return guides.operationDetail
  if (root === 'paper-operations' && parts.length === 1) return guides.paperList
  if (root === 'paper-operations') return guides.paperDetail
  return null
}

function GuideItem({ label, children }: { label: string; children: string }) {
  return (
    <div className="rounded-md border border-border bg-canvas/40 p-4">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        {label}
      </p>
      <p className="mt-2 mb-0 text-sm leading-6 text-secondary">{children}</p>
    </div>
  )
}

export function ScreenGuide({ guide }: { guide: ScreenGuideContent }) {
  return (
    <details open className="mb-8 rounded-lg border border-accent/35 bg-subtle p-5">
      <summary className="min-h-11 cursor-pointer py-2 text-base font-semibold text-accent">
        How to use this screen
      </summary>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <GuideItem label="Intent">{guide.intent}</GuideItem>
        <GuideItem label="What to do">{guide.action}</GuideItem>
        <GuideItem label="Example">{guide.example}</GuideItem>
        <GuideItem label="What happens next">{guide.next}</GuideItem>
      </div>
      <p className="mt-4 mb-0 rounded-md border border-warning/35 bg-canvas/35 p-3 text-sm leading-6 text-secondary">
        <strong className="text-foreground">This does not mean:</strong> {guide.boundary}
      </p>
    </details>
  )
}
