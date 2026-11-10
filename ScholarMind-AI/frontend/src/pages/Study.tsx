import { useState } from 'react'
import { BookOpen, CalendarDays, HelpCircle, Layers, Wand2 } from 'lucide-react'
import DocPicker from '../components/DocPicker'
import ResultPanel from '../components/ResultPanel'
import { Alert, Button, Card, PageHeader } from '../components/ui'
import { useApp } from '../context/AppContext'
import { api } from '../services/api'
import type { AgentReply } from '../types'

type Kind = 'notes' | 'quiz' | 'flashcards' | 'plan'
const TABS: { kind: Kind; label: string; icon: typeof BookOpen }[] = [
  { kind: 'notes', label: 'Notes', icon: BookOpen }, { kind: 'quiz', label: 'Quizzes', icon: HelpCircle },
  { kind: 'flashcards', label: 'Flashcards', icon: Layers }, { kind: 'plan', label: 'Study plan', icon: CalendarDays },
]

export default function Study() {
  const { docs } = useApp()
  const [kind, setKind] = useState<Kind>('notes')
  const [sel, setSel] = useState<string[]>([])
  const [topic, setTopic] = useState('')
  const [count, setCount] = useState(5)
  const [days, setDays] = useState(7)
  const [quizType, setQuizType] = useState<'mcq' | 'short'>('mcq')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reply, setReply] = useState<AgentReply | null>(null)
  const noDocs = !docs.some((d) => d.status === 'indexed')
  const canRun = !noDocs && (sel.length > 0 || topic.trim().length > 0)

  async function run() {
    setBusy(true); setError(null); setReply(null)
    try {
      setReply(await api.study(kind, { document_ids: sel, topic, count: kind === 'quiz' || kind === 'flashcards' ? count : undefined,
        days: kind === 'plan' ? days : undefined, quiz_type: kind === 'quiz' ? quizType : undefined }))
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return (
    <div className="mx-auto max-w-4xl p-6">
      <PageHeader title="Study Tools" subtitle="Generate notes, quizzes, flashcards and study plans from your own documents." />
      <div role="tablist" className="mb-5 flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
        {TABS.map(({ kind: k, label, icon: Icon }) => (
          <button key={k} role="tab" aria-selected={kind === k} onClick={() => { setKind(k); setReply(null); setError(null) }}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${kind === k ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600'}`}><Icon className="h-4 w-4" />{label}</button>))}
      </div>
      <Card className="mb-6 space-y-4">
        <DocPicker value={sel} onChange={setSel} />
        <label className="block text-sm font-medium text-slate-700">Topic or focus <span className="font-normal text-slate-400">(optional if documents are selected)</span>
          <input value={topic} onChange={(e) => setTopic(e.target.value)} maxLength={300} placeholder="e.g. clustering algorithms"
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal" /></label>
        <div className="flex flex-wrap gap-4">
          {(kind === 'quiz' || kind === 'flashcards') && <label className="text-sm font-medium text-slate-700">Count
            <input type="number" min={1} max={20} value={count} onChange={(e) => setCount(Math.max(1, Math.min(20, +e.target.value || 1)))} className="ml-2 w-20 rounded-lg border border-slate-200 px-2 py-1.5 text-sm" /></label>}
          {kind === 'quiz' && <label className="text-sm font-medium text-slate-700">Type
            <select value={quizType} onChange={(e) => setQuizType(e.target.value as 'mcq' | 'short')} className="ml-2 rounded-lg border border-slate-200 px-2 py-1.5 text-sm">
              <option value="mcq">Multiple choice</option><option value="short">Short answer</option></select></label>}
          {kind === 'plan' && <label className="text-sm font-medium text-slate-700">Days
            <input type="number" min={1} max={60} value={days} onChange={(e) => setDays(Math.max(1, Math.min(60, +e.target.value || 1)))} className="ml-2 w-20 rounded-lg border border-slate-200 px-2 py-1.5 text-sm" /></label>}
        </div>
        {!canRun && <p className="text-xs text-slate-500">{noDocs ? 'Upload and index a document to enable this.' : 'Select at least one document or enter a topic.'}</p>}
        <Button variant="primary" loading={busy} disabled={!canRun} onClick={run}><Wand2 className="h-4 w-4" />{busy ? 'Generating…' : 'Generate'}</Button>
      </Card>
      {error && <Alert onRetry={run}>{error}</Alert>}
      {reply && <ResultPanel reply={reply} />}
    </div>
  )
}
