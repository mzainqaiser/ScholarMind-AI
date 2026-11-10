import { useState } from 'react'
import { Check, Copy, RefreshCw } from 'lucide-react'
import { Alert, Badge, Button, Card, PageHeader, Spinner } from '../components/ui'
import { useApp } from '../context/AppContext'

const SETUP = `# 1. Install Ollama from https://ollama.com, then:
ollama pull qwen2.5:3b-instruct
# 2. Make sure it is running (default http://localhost:11434), then restart the backend`

export default function Settings() {
  const { status, statusError, refreshStatus, toast } = useApp()
  const [checking, setChecking] = useState(false)
  const [copied, setCopied] = useState(false)
  async function recheck() { setChecking(true); await refreshStatus(); setChecking(false); toast('success', 'Status refreshed.') }
  async function copy() { await navigator.clipboard.writeText(SETUP); setCopied(true); setTimeout(() => setCopied(false), 1500) }
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <PageHeader title="Settings" subtitle="Runtime configuration is read from the backend (.env). Values are shown read-only."
        actions={<Button loading={checking} onClick={recheck}><RefreshCw className="h-4 w-4" />Re-check connections</Button>} />
      {statusError && <Alert>Cannot reach the backend. Start it with <code>scripts/start_backend.ps1</code>.</Alert>}
      {!status && !statusError ? <Spinner /> : status && (
        <>
          <Card><h3 className="mb-3 font-semibold">Language model</h3>
            <div className="flex items-center gap-2 text-sm"><Badge tone={status.llm.available ? 'green' : 'amber'}>{status.llm.available ? 'connected' : 'not connected'}</Badge>
              <span>{status.llm.provider} · {status.llm.model}</span></div>
            {!status.llm.available && <><p className="mt-2 text-sm text-slate-600">{status.llm.detail}</p>
              <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">{SETUP}</pre>
              <Button className="mt-2" onClick={copy}>{copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}{copied ? 'Copied' : 'Copy commands'}</Button></>}</Card>
          <Card><h3 className="mb-3 font-semibold">Embeddings & vector store</h3>
            <div className="flex items-center gap-2 text-sm"><Badge tone={status.vector_store.semantic ? 'green' : 'amber'}>{status.vector_store.semantic ? 'semantic model' : 'lexical fallback'}</Badge><span>{status.vector_store.embedder}</span></div>
            {!status.vector_store.semantic && <p className="mt-2 text-sm text-slate-600">The semantic model could not be loaded, so a keyword-based fallback is used. Install <code>sentence-transformers</code> and allow the one-time model download, then restart the backend and re-index your documents.</p>}
            <p className="mt-2 text-sm text-slate-500">{status.vector_store.chunks} chunks stored · {status.database.documents} documents</p></Card>
          <Card><h3 className="mb-3 font-semibold">Pipeline configuration</h3>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">{Object.entries(status.config).map(([k, v]) => (<div key={k} className="contents"><dt className="text-slate-500">{k.replace(/_/g, ' ')}</dt><dd className="font-mono text-xs">{String(v)}</dd></div>))}</dl></Card>
        </>)}
    </div>
  )
}
