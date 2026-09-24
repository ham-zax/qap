import { useEffect, useRef, useState } from 'react'

import {
  addAttempt, emptyStudy, readStudies, saveStudies, studyStorageKey,
  type ResearchStudy, type StudyLibrary, type StudyStorage,
} from './researchStudies'

function browserStorage(): StudyStorage {
  return {
    getItem: (key) => window.localStorage.getItem(key),
    setItem: (key, value) => window.localStorage.setItem(key, value),
  }
}

export function useResearchStudies(workspace: string) {
  const [initial] = useState(() => {
    const saved = readStudies(browserStorage(), workspace)
    const first = emptyStudy(crypto.randomUUID())
    return { library: saved.library ?? { activeId: first.id, studies: [first] }, warning: saved.warning }
  })
  const [library, setLibrary] = useState<StudyLibrary>(initial.library)
  const [warning, setWarning] = useState(initial.warning)
  const current = useRef(library)
  const externalChange = useRef(false)
  const conflictWarning = 'Saved studies changed in another tab. Reload to use that version. Until then, changes stay only in this tab; started backtests remain in History.'

  const publish = (next: StudyLibrary) => {
    const latest = readStudies(browserStorage(), workspace)
    const merged = externalChange.current ? next : { ...next, studies: next.studies.map((item) => {
      const recorded = latest.library?.studies.find((saved) => saved.id === item.id)?.attempts ?? []
      const attempts = [...recorded, ...item.attempts.filter((attempt) => !recorded.some((saved) => saved.operationId === attempt.operationId))]
      return { ...item, attempts }
    }) }
    current.current = merged
    setLibrary(merged)
    setWarning(externalChange.current ? conflictWarning : saveStudies(browserStorage(), workspace, merged))
  }

  useEffect(() => {
    const receive = (event: StorageEvent) => {
      if (event.key !== studyStorageKey(workspace) && event.key !== null) return
      // Never swap the question underneath an in-flight support check or run.
      // Preserve the other tab's library instead of silently overwriting it.
      externalChange.current = true
      setWarning(conflictWarning)
    }
    window.addEventListener('storage', receive)
    return () => window.removeEventListener('storage', receive)
  }, [workspace])

  const update = (id: string, patch: Partial<Omit<ResearchStudy, 'id' | 'attempts'>>) => {
    publish({ ...current.current, studies: current.current.studies.map((item) => item.id === id ? { ...item, ...patch } : item) })
  }
  const recordAttempt = (id: string, operationId: string, question: string) => {
    // A start request may finish after route navigation and a new hook mount.
    // Append to the latest saved library without restoring the old active draft.
    const latest = readStudies(browserStorage(), workspace)
    const base = !externalChange.current && !warning && latest.library ? latest.library : current.current
    publish({ ...base, studies: base.studies.map((item) => item.id === id
      ? addAttempt(item, operationId, new Date().toISOString(), question) : item) })
  }
  const create = () => {
    const next = emptyStudy(crypto.randomUUID())
    publish({ activeId: next.id, studies: [...current.current.studies, next] })
  }
  const select = (id: string) => {
    if (current.current.studies.some((item) => item.id === id)) publish({ ...current.current, activeId: id })
  }
  return { library, warning, update, recordAttempt, create, select }
}
