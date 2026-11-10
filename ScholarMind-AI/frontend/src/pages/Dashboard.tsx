import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Database, FileText, FlaskConical, Layers, MessageSquare, Upload } from 'lucide-react'
import { Alert, Badge, Card, EmptyState, Spinner, statusTone } from '../components/ui'
import { useApp } from '../context/AppContext'
import { api } from '../services/api'
import type { Overview } from '../types'
import { formatDate } from '../utils/format'

export default function Dashboard() {
  const { status } = useApp()
  const [ov, setOv] = useState<Overview | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const load = useCallback(() => { setErr(null); api.overview().then(setOv).catch((e) => setErr(e.message)) }, [])
  useEffect(load, [load])
  if (err) return <div className="p-6"><Alert onRetry={load}>{err}</Alert></div>
  if (!ov) return <div className="p-6"><Spinner /></div>
  const stats = [
    { label: 'Documents', value: ov.documents.total, icon: FileText }, { label: 'Indexed', value: ov.documents.indexed, icon: Layers },
    { label: 'Knowledge chunks', value: ov.chunks, icon: Database }, { label: 'Conversations', value: ov.conversations, icon: MessageSquare },
  ]
  const actions = [
    { to: '/documents', label: 'Upload a document', icon: Upload }, { to: '/assistant', label: 'Ask the assistant', icon: MessageSquare },
    { to: '/study', label: 'Generate a quiz', icon: BookOpen }, { to: '/research', label: 'Research a topic', icon: FlaskConical },
  ]
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div><h2 className="text-2xl font-semibold">Welcome to ScholarMind AI</h2>
        <p className="text-slate-500">Your knowledge. Your research. Your intelligent AI assistant.</p></div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <Card key={label}><div className="flex items-center justify-between"><span className="text-sm text-slate-500">{label}</span><Icon className="h-4 w-4 text-indigo-500" /></div>
            <div className="mt-2 text-3xl font-semibold" data-testid={`stat-${label}`}>{value}</div></Card>))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <h3 className="mb-3 font-semibold">Recent documents</h3>
            {ov.recent_documents.length === 0 ? (
              <EmptyState icon={<Upload className="h-5 w-5" />} title="No documents yet" text="Upload a PDF, DOCX, TXT or Markdown file to start asking questions."
                action={<Link to="/documents" className="rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-700">Upload documents</Link>} />
            ) : (
              <ul className="divide-y divide-slate-100">{ov.recent_documents.map((d) => (
                <li key={d.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                  <span className="truncate font-medium">{d.filename}</span>
                  <span className="flex shrink-0 items-center gap-2"><span className="hidden text-xs text-slate-400 sm:inline">{d.chunk_count} chunks</span><Badge tone={statusTone(d.status)}>{d.status}</Badge></span>
                </li>))}</ul>)}
          </Card>
          <Card>
            <h3 className="mb-3 font-semibold">Recent activity</h3>
            {ov.recent_conversations.length === 0 ? <p className="text-sm text-slate-500">No conversations yet. Ask the assistant a question about your documents.</p> : (
              <ul className="divide-y divide-slate-100">{ov.recent_conversations.map((c) => (
                <li key={c.id} className="flex items-center justify-between py-2.5 text-sm"><span className="truncate">{c.title}</span>
                  <span className="shrink-0 text-xs text-slate-400">{formatDate(c.updated_at)}</span></li>))}</ul>)}
          </Card>
        </div>
        <div className="space-y-6">
          <Card><h3 className="mb-3 font-semibold">Quick actions</h3>
            <div className="space-y-2">{actions.map(({ to, label, icon: Icon }) => (
              <Link key={to} to={to} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium hover:bg-slate-50"><Icon className="h-4 w-4 text-indigo-500" />{label}</Link>))}</div></Card>
          <Card><h3 className="mb-3 font-semibold">System status</h3>
            {!status ? <Spinner /> : (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between"><dt>AI system</dt><dd><Badge tone="green">running</Badge></dd></div>
                <div className="flex justify-between"><dt>Vector database</dt><dd><Badge tone={status.vector_store.status === 'ok' ? 'green' : 'red'}>{status.vector_store.chunks} chunks</Badge></dd></div>
                <div className="flex justify-between"><dt>Embeddings</dt><dd><Badge tone={status.vector_store.semantic ? 'green' : 'amber'}>{status.vector_store.embedder}</Badge></dd></div>
                <div className="flex justify-between"><dt>LLM</dt><dd><Badge tone={status.llm.available ? 'green' : 'amber'}>{status.llm.available ? status.llm.model! : 'offline'}</Badge></dd></div>
                {!status.llm.available && <p className="text-xs text-slate-500">{status.llm.detail}</p>}
              </dl>)}</Card>
        </div>
      </div>
    </div>
  )
}
