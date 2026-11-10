import { useApp } from '../context/AppContext'
import { Spinner } from './ui'

/** Multi-select over indexed documents. Empty selection means "all documents". */
export default function DocPicker({ value, onChange, label = 'Documents' }: { value: string[]; onChange: (v: string[]) => void; label?: string }) {
  const { docs, docsLoading } = useApp()
  const indexed = docs.filter((d) => d.status === 'indexed')
  const toggle = (id: string) => onChange(value.includes(id) ? value.filter((x) => x !== id) : [...value, id])
  if (docsLoading) return <Spinner />
  return (
    <fieldset>
      <legend className="mb-1.5 text-sm font-medium text-slate-700">{label} <span className="font-normal text-slate-400">({value.length ? `${value.length} selected` : 'all documents'})</span></legend>
      {indexed.length === 0 ? <p className="text-sm text-slate-500">No indexed documents yet — upload one first.</p> : (
        <div className="max-h-44 space-y-1 overflow-y-auto rounded-lg border border-slate-200 bg-white p-2">
          {indexed.map((d) => (
            <label key={d.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm hover:bg-slate-50">
              <input type="checkbox" checked={value.includes(d.id)} onChange={() => toggle(d.id)} className="h-4 w-4 rounded border-slate-300 text-indigo-600" />
              <span className="truncate">{d.filename}</span><span className="ml-auto text-xs text-slate-400">{d.category}</span>
            </label>
          ))}
        </div>
      )}
      {value.length > 0 && <button type="button" onClick={() => onChange([])} className="mt-1 text-xs text-indigo-600 hover:underline">Clear selection</button>}
    </fieldset>
  )
}
