import { useCallback, useEffect, useState } from 'react'
import { BarChart3 } from 'lucide-react'
import { Alert, Card, EmptyState, PageHeader, Spinner } from '../components/ui'
import { api } from '../services/api'
import type { Doc, Overview, Usage } from '../types'
import { formatBytes, TOOL_TITLES } from '../utils/format'

function Bars({ data, label }: { data: [string, number][]; label: (k: string) => string }) {
  const max = Math.max(1, ...data.map(([, v]) => v))
  return <div className="space-y-2">{data.map(([k, v]) => (
    <div key={k} className="flex items-center gap-3 text-sm"><span className="w-36 shrink-0 truncate text-slate-600">{label(k)}</span>
      <div className="h-2.5 flex-1 rounded bg-slate-100"><div className="h-full rounded bg-indigo-500" style={{ width: `${(v / max) * 100}%` }} /></div><span className="w-8 text-right tabular-nums">{v}</span></div>))}</div>
}

export default function Analytics() {
  const [ov, setOv] = useState<Overview | null>(null)
  const [usage, setUsage] = useState<Usage | null>(null)
  const [docs, setDocs] = useState<Doc[]>([])
  const [err, setErr] = useState<string | null>(null)
  const load = useCallback(() => {
    setErr(null)
    Promise.all([api.overview(), api.usage(), api.analyticsDocs()]).then(([o, u, d]) => { setOv(o); setUsage(u); setDocs(d.documents) }).catch((e) => setErr(e.message))
  }, [])
  useEffect(load, [load])
  if (err) return <div className="p-6"><Alert onRetry={load}>{err}</Alert></div>
  if (!ov || !usage) return <div className="p-6"><Spinner /></div>
  if (ov.documents.total === 0 && ov.messages === 0)
    return <div className="mx-auto max-w-3xl p-6"><PageHeader title="Analytics" /><EmptyState icon={<BarChart3 className="h-5 w-5" />} title="Nothing to analyse yet" text="Upload documents and chat with the assistant — usage statistics will appear here." /></div>
  const perDay = usage.messages_per_day.map((d) => [d.date.slice(5), d.user] as [string, number])
  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <PageHeader title="Analytics" subtitle="Computed from your stored documents and conversations." />
      <div className="grid gap-6 md:grid-cols-2">
        <Card><h3 className="mb-3 font-semibold">Questions asked per day (last 14 days)</h3><Bars data={perDay} label={(k) => k} /></Card>
        <Card><h3 className="mb-3 font-semibold">Agent tools used</h3>
          {Object.keys(usage.tools).length ? <Bars data={Object.entries(usage.tools)} label={(k) => TOOL_TITLES[k] ?? k} /> : <p className="text-sm text-slate-500">No agent responses yet.</p>}</Card>
        <Card><h3 className="mb-3 font-semibold">Documents by type</h3><Bars data={Object.entries(ov.by_type)} label={(k) => k.toUpperCase()} /></Card>
        <Card><h3 className="mb-3 font-semibold">Response outcomes</h3>
          {Object.keys(usage.statuses).length ? <Bars data={Object.entries(usage.statuses)} label={(k) => k.replace('_', ' ')} /> : <p className="text-sm text-slate-500">No responses yet.</p>}</Card>
      </div>
      <Card className="overflow-x-auto"><h3 className="mb-3 font-semibold">Knowledge base by document</h3>
        <table className="w-full text-sm"><thead className="text-left text-xs uppercase text-slate-500"><tr><th className="py-2">Document</th><th>Type</th><th>Pages</th><th>Chunks</th><th>Size</th></tr></thead>
          <tbody className="divide-y divide-slate-100">{docs.map((d) => (<tr key={d.id}><td className="py-2 font-medium">{d.filename}</td><td>{d.file_type.toUpperCase()}</td><td>{d.pages ?? '—'}</td><td>{d.chunk_count}</td><td>{formatBytes(d.size_bytes)}</td></tr>))}</tbody></table></Card>
    </div>
  )
}
