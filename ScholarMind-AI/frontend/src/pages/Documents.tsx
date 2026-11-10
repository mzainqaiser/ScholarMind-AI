import { DragEvent, useRef, useState } from 'react'
import { Eye, RefreshCw, Search, Trash2, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Alert, Badge, Button, Card, Drawer, EmptyState, PageHeader, Spinner, statusTone } from '../components/ui'
import { useApp } from '../context/AppContext'
import { api } from '../services/api'
import type { Doc, UploadResult } from '../types'
import { formatBytes, formatDate } from '../utils/format'

const ALLOWED = ['pdf', 'docx', 'txt', 'md']
const MAX_MB = 20

export default function Documents() {
  const { docs, docsLoading, docsError, refreshDocs, refreshStatus, toast } = useApp()
  const [category, setCategory] = useState('General')
  const [progress, setProgress] = useState<number | null>(null)
  const [results, setResults] = useState<UploadResult[]>([])
  const [drag, setDrag] = useState(false)
  const [query, setQuery] = useState('')
  const [filterCat, setFilterCat] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [preview, setPreview] = useState<{ doc: Doc; text: string; truncated: boolean } | null>(null)
  const [confirmDel, setConfirmDel] = useState<Doc | null>(null)
  const input = useRef<HTMLInputElement>(null)

  async function upload(list: FileList | File[]) {
    const files = Array.from(list)
    const local: UploadResult[] = [], ok: File[] = []
    for (const f of files) {                                 // client-side validation; the server validates again
      const ext = f.name.split('.').pop()?.toLowerCase() ?? ''
      if (!ALLOWED.includes(ext)) local.push({ filename: f.name, ok: false, error: `Unsupported type .${ext}. Use PDF, DOCX, TXT or MD.` })
      else if (f.size > MAX_MB * 1048576) local.push({ filename: f.name, ok: false, error: `Larger than ${MAX_MB} MB.` })
      else ok.push(f)
    }
    setResults(local)
    if (!ok.length) return
    setProgress(0)
    try {
      const res = await api.upload(ok, category.trim() || 'General', setProgress)
      setResults([...local, ...res])
      const n = res.filter((r) => r.ok).length
      if (n) toast('success', `${n} document${n > 1 ? 's' : ''} processed.`)
    } catch (e) { toast('error', (e as Error).message) }
    finally { setProgress(null); await refreshDocs(); refreshStatus() }
  }
  const onDrop = (e: DragEvent) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files.length) upload(e.dataTransfer.files) }

  async function act(id: string, fn: () => Promise<unknown>, okMsg: string) {
    setBusy(id)
    try { await fn(); toast('success', okMsg) } catch (e) { toast('error', (e as Error).message) }
    finally { setBusy(null); await refreshDocs(); refreshStatus() }
  }
  async function openPreview(doc: Doc) {
    try { const p = await api.preview(doc.id); setPreview({ doc, ...p }) } catch (e) { toast('error', (e as Error).message) }
  }
  const categories = Array.from(new Set(docs.map((d) => d.category)))
  const shown = docs.filter((d) => d.filename.toLowerCase().includes(query.toLowerCase()) && (!filterCat || d.category === filterCat))

  return (
    <div className="mx-auto max-w-6xl p-6">
      <PageHeader title="My Documents" subtitle="Upload academic material. Text is extracted, chunked, embedded and stored locally." />
      <Card className="mb-6">
        <div onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)} onDrop={onDrop}
          className={`flex flex-col items-center rounded-lg border-2 border-dashed px-4 py-8 text-center ${drag ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300'}`}>
          <Upload className="mb-2 h-6 w-6 text-indigo-500" />
          <p className="text-sm font-medium">Drag files here or choose files</p>
          <p className="mb-3 text-xs text-slate-500">PDF, DOCX, TXT, MD · up to {MAX_MB} MB each</p>
          <input ref={input} type="file" multiple accept=".pdf,.docx,.txt,.md" className="hidden" aria-label="Choose files"
            onChange={(e) => { if (e.target.files?.length) upload(e.target.files); e.target.value = '' }} />
          <div className="flex flex-wrap items-center justify-center gap-3">
            <label className="text-sm text-slate-600">Category{' '}
              <input value={category} onChange={(e) => setCategory(e.target.value)} maxLength={50} list="cats"
                className="ml-1 w-40 rounded-lg border border-slate-200 px-2 py-1.5 text-sm" />
              <datalist id="cats">{categories.map((c) => <option key={c} value={c} />)}</datalist></label>
            <Button variant="primary" loading={progress !== null} onClick={() => input.current?.click()}>
              {progress !== null ? (progress < 100 ? `Uploading ${progress}%` : 'Processing…') : 'Choose files'}</Button>
          </div>
          {progress !== null && <div className="mt-3 h-1.5 w-64 overflow-hidden rounded bg-slate-200" role="progressbar" aria-valuenow={progress}><div className="h-full bg-indigo-600 transition-all" style={{ width: `${progress}%` }} /></div>}
        </div>
        {results.length > 0 && <ul className="mt-3 space-y-1.5">{results.map((r, i) => (
          <li key={i}>{r.ok ? <Alert tone="indigo">{r.filename}: {r.document?.status === 'indexed' ? `indexed (${r.document.chunk_count} chunks)` : `failed — ${r.document?.error}`}</Alert>
            : <Alert>{r.filename}: {r.error}</Alert>}</li>))}</ul>}
      </Card>

      <div className="mb-3 flex flex-wrap gap-3">
        <div className="relative min-w-[200px] flex-1"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search documents…" aria-label="Search documents"
            className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm" /></div>
        <select value={filterCat} onChange={(e) => setFilterCat(e.target.value)} aria-label="Filter by category" className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
          <option value="">All categories</option>{categories.map((c) => <option key={c}>{c}</option>)}</select>
      </div>

      {docsLoading ? <Spinner /> : docsError ? <Alert onRetry={refreshDocs}>{docsError}</Alert> : docs.length === 0 ? (
        <EmptyState icon={<Upload className="h-5 w-5" />} title="Your library is empty" text="Upload your first document above to build your knowledge base." />
      ) : shown.length === 0 ? <p className="py-6 text-center text-sm text-slate-500">No documents match your filters.</p> : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-sm"><thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr><th className="px-4 py-3">Document</th><th className="px-4 py-3">Category</th><th className="px-4 py-3">Status</th><th className="hidden px-4 py-3 md:table-cell">Details</th><th className="px-4 py-3 text-right">Actions</th></tr></thead>
            <tbody className="divide-y divide-slate-100">{shown.map((d) => (
              <tr key={d.id}>
                <td className="px-4 py-3"><div className="font-medium">{d.filename}</div><div className="text-xs text-slate-400">{formatDate(d.uploaded_at)}</div></td>
                <td className="px-4 py-3">{d.category}</td>
                <td className="px-4 py-3"><Badge tone={statusTone(d.status)}>{d.status}</Badge>{d.error && <p className="mt-1 max-w-[220px] text-xs text-red-600">{d.error}</p>}</td>
                <td className="hidden px-4 py-3 text-xs text-slate-500 md:table-cell">{d.file_type.toUpperCase()} · {formatBytes(d.size_bytes)}<br />{d.pages ? `${d.pages} pages · ` : ''}{d.chunk_count} chunks</td>
                <td className="px-4 py-3"><div className="flex justify-end gap-1">
                  <Button variant="ghost" aria-label={`Preview ${d.filename}`} disabled={d.status !== 'indexed'} onClick={() => openPreview(d)}><Eye className="h-4 w-4" /></Button>
                  <Button variant="ghost" aria-label={`Re-index ${d.filename}`} loading={busy === d.id} onClick={() => act(d.id, () => api.reindex(d.id), 'Re-indexed.')}><RefreshCw className="h-4 w-4" /></Button>
                  <Button variant="ghost" aria-label={`Delete ${d.filename}`} onClick={() => setConfirmDel(d)}><Trash2 className="h-4 w-4 text-red-500" /></Button></div></td>
              </tr>))}</tbody></table>
        </Card>)}
      {docs.some((d) => d.status === 'indexed') && <p className="mt-4 text-sm text-slate-500">Ready to go: <Link className="text-indigo-600 hover:underline" to="/assistant">ask the assistant</Link> or <Link className="text-indigo-600 hover:underline" to="/study">generate study material</Link>.</p>}

      <Drawer open={!!preview} onClose={() => setPreview(null)} title={preview ? `Preview — ${preview.doc.filename}` : ''}>
        {preview && <><pre className="whitespace-pre-wrap text-sm text-slate-700">{preview.text}</pre>{preview.truncated && <p className="mt-3 text-xs text-slate-400">Preview truncated.</p>}</>}
      </Drawer>
      <Drawer open={!!confirmDel} onClose={() => setConfirmDel(null)} title="Delete document?">
        {confirmDel && <div className="space-y-4"><p className="text-sm">“{confirmDel.filename}” and all its indexed chunks will be permanently removed.</p>
          <div className="flex gap-2"><Button variant="danger" onClick={async () => { const d = confirmDel; setConfirmDel(null); await act(d.id, () => api.deleteDoc(d.id), 'Document deleted.') }}>Delete</Button>
            <Button onClick={() => setConfirmDel(null)}>Cancel</Button></div></div>}
      </Drawer>
    </div>
  )
}
