import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Renders model output as Markdown. Raw HTML is NOT enabled, so model/document text cannot inject markup. */
export default function Markdown({ children }: { children: string }) {
  return (
    <div className="prose-sm-custom break-words">
      <ReactMarkdown remarkPlugins={[remarkGfm]}
        components={{ table: ({ children: c }) => <div className="my-2 overflow-x-auto"><table>{c}</table></div> }}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
