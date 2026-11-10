import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import type { Doc, SystemStatus } from '../types'

interface Toast { id: number; kind: 'success' | 'error'; text: string }
interface Ctx {
  docs: Doc[]; docsLoading: boolean; docsError: string | null; refreshDocs: () => Promise<void>
  status: SystemStatus | null; statusError: boolean; refreshStatus: () => Promise<void>
  toast: (kind: Toast['kind'], text: string) => void
}
const AppCtx = createContext<Ctx | null>(null)
export const useApp = () => { const c = useContext(AppCtx); if (!c) throw new Error('useApp outside provider'); return c }

export function AppProvider({ children }: { children: ReactNode }) {
  const [docs, setDocs] = useState<Doc[]>([])
  const [docsLoading, setDocsLoading] = useState(true)
  const [docsError, setDocsError] = useState<string | null>(null)
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [statusError, setStatusError] = useState(false)
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(1)

  const refreshDocs = useCallback(async () => {
    try { setDocs(await api.listDocs()); setDocsError(null) }
    catch (e) { setDocsError((e as Error).message) }
    finally { setDocsLoading(false) }
  }, [])
  const refreshStatus = useCallback(async () => {
    try { setStatus(await api.status()); setStatusError(false) } catch { setStatusError(true) }
  }, [])
  const toast = useCallback((kind: Toast['kind'], text: string) => {
    const id = nextId.current++
    setToasts((t) => [...t, { id, kind, text }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000)
  }, [])

  useEffect(() => {
    refreshDocs(); refreshStatus()
    const t = setInterval(refreshStatus, 20000)
    return () => clearInterval(t)
  }, [refreshDocs, refreshStatus])

  return (
    <AppCtx.Provider value={{ docs, docsLoading, docsError, refreshDocs, status, statusError, refreshStatus, toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`max-w-sm rounded-lg border px-4 py-3 text-sm shadow-lg ${t.kind === 'error' ? 'border-red-200 bg-red-50 text-red-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'}`}>{t.text}</div>
        ))}
      </div>
    </AppCtx.Provider>
  )
}
