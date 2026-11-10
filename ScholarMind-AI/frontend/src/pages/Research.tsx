import { useState } from 'react'
import { GitCompare, Microscope, Search } from 'lucide-react'
import { CitationList } from '../components/Citations'
import DocPicker from '../components/DocPicker'
import ResultPanel from '../components/ResultPanel'
import { Alert, Button, Card, PageHeader } from '../components/ui'
import { api } from '../services/api'
import type { AgentReply, Citation } from '../types'

type Mode = 'research' | 'compare' | 'search'
const TABS = [{ m: 'research' as Mode, label: 'Research', icon: Microscope }, { m: 'compare' as Mode, label: 'Compare', icon: GitCompare }, { m: 'search' as Mode, label: 'Search', icon: Search }]

export default function Research() {
  const [mode, setMode] = useState<Mode>('research')
  const [sel, setSel] = useState<string[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reply, setReply] = useState<AgentReply | null>(null)
  const [hits, setHits] = useState<Citation[] | null>(null)

  const valid = mode === 'compare' ? sel.length >= 2 || text.trim().length > 0 : text.trim().length > 1
  const hint = mode === 'research' ? 'Describe a research topic or question' : mode === 'compare' ? 'Concepts to compare (optional if you select 2+ documents)' : 'Search query'

  async function run() {
    setBusy(true); setError(null); setReply(null); setHits(null)
    try {
      if (mode === 'search') setHits((await api.search(text.trim(), 8, sel)).results)
      else setReply(await api.study(mode, { document_ids: sel, topic: text }))
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return (
    <div className="mx-auto max-w-4xl p-6">
      <PageHeader title="Research Workspace" subtitle="Investigate topics, compare sources, and search passages — all grounded in your documents." />
      <div role="tablist" className="mb-5 flex gap-1 rounded-xl bg-slate-100 p-1">
        {TABS.map(({ m, label, icon: Icon }) => (
          <button key={m} role="tab" aria-selected={mode === m} onClick={() => { setMode(m); setReply(null); setHits(null); setError(null) }}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${mode === m ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600'}`}><Icon className="h-4 w-4" />{label}</button>))}
      </div>
      <Card className="mb-6 space-y-4">
        <DocPicker value={sel} onChange={setSel} label={mode === 'compare' ? 'Documents to compare' : 'Limit to documents'} />
        <label className="block text-sm font-medium text-slate-700">{hint}
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} maxLength={1000} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal" /></label>
        {mode === 'compare' && sel.length < 2 && !text.trim() && <p className="text-xs text-slate-500">Select at least two documents, or enter the concepts to compare.</p>}
        <Button variant="primary" loading={busy} disabled={!valid} onClick={run}>{mode === 'search' ? 'Search' : mode === 'compare' ? 'Compare' : 'Start research'}</Button>
      </Card>
      {error && <Alert onRetry={run}>{error}</Alert>}
      {reply && <ResultPanel reply={reply} />}
      {hits && (hits.length === 0 ? <Alert tone="amber">No relevant passages found. Try different keywords.</Alert> : <CitationList citations={hits} />)}
    </div>
  )
}
