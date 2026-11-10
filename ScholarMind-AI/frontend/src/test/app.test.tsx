/** Frontend tests. The API client is mocked (these test UI behaviour; backend integration is tested separately). */
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { AppProvider } from '../context/AppContext'
import { ApiError, errorMessage } from '../services/api'
import type { Doc } from '../types'

const m = vi.hoisted(() => ({
  status: vi.fn(), overview: vi.fn(), listDocs: vi.fn(), upload: vi.fn(), deleteDoc: vi.fn(), reindex: vi.fn(), preview: vi.fn(),
  chat: vi.fn(), conversations: vi.fn(), conversation: vi.fn(), deleteConversation: vi.fn(), clearConversation: vi.fn(),
  study: vi.fn(), search: vi.fn(), usage: vi.fn(), analyticsDocs: vi.fn(),
}))
vi.mock('../services/api', async (orig) => ({ ...(await orig<typeof import('../services/api')>()), api: m }))

const doc = (o: Partial<Doc> = {}): Doc => ({ id: 'd1', filename: 'ml_notes.pdf', file_type: 'pdf', category: 'Course', status: 'indexed',
  error: null, chunk_count: 4, pages: 3, size_bytes: 2048, uploaded_at: '2026-11-05T10:00:00+00:00', ...o })
const STATUS = { vector_store: { status: 'ok', chunks: 4, embedder: 'hashing-384', semantic: false }, database: { status: 'ok', documents: 1 },
  llm: { available: true, provider: 'ollama', model: 'qwen2.5:3b-instruct', detail: 'ready' }, config: { chunk_size: 800 } }
const OVERVIEW = (n: number) => ({ documents: { total: n, indexed: n, failed: 0, processing: 0 }, chunks: n * 4, conversations: 2, messages: 4,
  by_type: {}, by_category: {}, recent_documents: n ? [doc()] : [], recent_conversations: [{ id: 'c1', title: 'Earlier chat', updated_at: '2026-11-05T10:00:00+00:00', message_count: 2 }] })
const REPLY = { conversation_id: 'c9', answer: 'Overfitting means memorising noise [S1].', status: 'answered', tool: 'document_qa', intent: 'document_qa',
  citations: [{ id: 'S1', chunk_id: 'd1:0', doc_id: 'd1', filename: 'ml_notes.pdf', page: 1, section: null, score: 0.42, excerpt: 'Overfitting happens when…', cited_in_answer: true }],
  trace: [{ step: 'Understanding your question', detail: 'Intent: document_qa' }], structured: null, warnings: [] }

function renderApp(route = '/') {
  return render(<MemoryRouter initialEntries={[route]}><AppProvider><App /></AppProvider></MemoryRouter>)
}
beforeEach(() => {
  vi.clearAllMocks()
  m.status.mockResolvedValue(STATUS); m.listDocs.mockResolvedValue([doc()]); m.overview.mockResolvedValue(OVERVIEW(1))
  m.conversations.mockResolvedValue([]); m.usage.mockResolvedValue({ messages_per_day: [], tools: {}, statuses: {} }); m.analyticsDocs.mockResolvedValue({ documents: [] })
})

describe('Dashboard', () => {
  it('shows real stats from the API and system status', async () => {
    renderApp()
    expect(await screen.findByText('Welcome to ScholarMind AI')).toBeInTheDocument()
    expect(await screen.findByTestId('stat-Knowledge chunks')).toHaveTextContent('4')
    expect(screen.getByText('Earlier chat')).toBeInTheDocument()
    expect(await screen.findByText('hashing-384')).toBeInTheDocument()
  })
  it('shows an empty state when there are no documents', async () => {
    m.overview.mockResolvedValue(OVERVIEW(0)); m.listDocs.mockResolvedValue([])
    renderApp()
    expect(await screen.findByText('No documents yet')).toBeInTheDocument()
  })
  it('shows an error with retry when the backend fails', async () => {
    m.overview.mockRejectedValueOnce(new ApiError('Cannot reach the backend.', 0))
    renderApp()
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the backend.')
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('Welcome to ScholarMind AI')).toBeInTheDocument()
  })
})

describe('Navigation & layout', () => {
  it('navigates between every sidebar page', async () => {
    renderApp()
    const nav = screen.getAllByRole('navigation', { name: 'Main' })[0]
    for (const label of ['My Documents', 'Study Tools', 'Research Workspace', 'Analytics', 'Settings']) {
      await userEvent.click(within(nav).getByRole('link', { name: label }))
      // top bar <h1> and the page's own <h2> both carry the title, so expect at least one of each
      expect((await screen.findAllByRole('heading', { name: label })).length).toBeGreaterThanOrEqual(1)
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(label)
    }
  })
  it('shows LLM and fallback-embedding badges in the top bar', async () => {
    renderApp()
    expect(await screen.findByText(/LLM: qwen2.5/)).toBeInTheDocument()
    expect(screen.getByText('Fallback embeddings')).toBeInTheDocument()
  })
  it('flags an offline LLM', async () => {
    m.status.mockResolvedValue({ ...STATUS, llm: { available: false, detail: 'Ollama not reachable' } })
    renderApp()
    expect(await screen.findByText('LLM offline')).toBeInTheDocument()
  })
})

describe('Documents', () => {
  it('lists documents and filters by search', async () => {
    m.listDocs.mockResolvedValue([doc(), doc({ id: 'd2', filename: 'photosynthesis.docx', file_type: 'docx' })])
    renderApp('/documents')
    expect(await screen.findByText('ml_notes.pdf')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Search documents'), 'photo')
    expect(screen.queryByText('ml_notes.pdf')).not.toBeInTheDocument()
    expect(screen.getByText('photosynthesis.docx')).toBeInTheDocument()
  })
  it('rejects unsupported files on the client without calling the API', async () => {
    renderApp('/documents')
    await screen.findByText('ml_notes.pdf')
    await userEvent.upload(screen.getByLabelText('Choose files'), new File(['x'], 'virus.exe'), { applyAccept: false })
    expect(await screen.findByText(/Unsupported type \.exe/)).toBeInTheDocument()
    expect(m.upload).not.toHaveBeenCalled()
  })
  it('uploads a valid file and reports indexing result', async () => {
    m.upload.mockResolvedValue([{ filename: 'new.pdf', ok: true, document: doc({ filename: 'new.pdf', chunk_count: 7 }) }])
    renderApp('/documents')
    await screen.findByText('ml_notes.pdf')
    await userEvent.upload(screen.getByLabelText('Choose files'), new File(['%PDF'], 'new.pdf', { type: 'application/pdf' }))
    expect(await screen.findByText(/indexed \(7 chunks\)/)).toBeInTheDocument()
    expect(m.upload).toHaveBeenCalledWith(expect.any(Array), 'General', expect.any(Function))
  })
  it('shows server-side upload errors', async () => {
    m.upload.mockResolvedValue([{ filename: 'a.pdf', ok: false, error: 'Duplicate of already uploaded ml_notes.pdf' }])
    renderApp('/documents')
    await screen.findByText('ml_notes.pdf')
    await userEvent.upload(screen.getByLabelText('Choose files'), new File(['%PDF'], 'a.pdf'))
    expect(await screen.findByText(/Duplicate of already uploaded/)).toBeInTheDocument()
  })
  it('asks for confirmation before deleting, then deletes', async () => {
    m.deleteDoc.mockResolvedValue({ deleted: 'd1' })
    renderApp('/documents')
    await userEvent.click(await screen.findByRole('button', { name: 'Delete ml_notes.pdf' }))
    expect(m.deleteDoc).not.toHaveBeenCalled()
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(m.deleteDoc).toHaveBeenCalledWith('d1'))
  })
  it('shows a failed document with its error', async () => {
    m.listDocs.mockResolvedValue([doc({ status: 'failed', error: 'File content is not a valid PDF.' })])
    renderApp('/documents')
    expect(await screen.findByText('File content is not a valid PDF.')).toBeInTheDocument()
  })
})

describe('Chat', () => {
  it('sends a message and shows the answer with its source citation', async () => {
    m.chat.mockResolvedValue(REPLY)
    renderApp('/assistant')
    await userEvent.type(await screen.findByLabelText('Message'), 'What is overfitting?')
    await userEvent.click(screen.getByRole('button', { name: 'Send message' }))
    expect(await screen.findByText(/memorising noise/)).toBeInTheDocument()
    expect(m.chat).toHaveBeenCalledWith('What is overfitting?', null, [])
    expect(screen.getByText('Document Q&A')).toBeInTheDocument()
    expect(await screen.findAllByText('ml_notes.pdf')).not.toHaveLength(0)       // citation panel
    expect(screen.getAllByText('p. 1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Agent activity').length).toBeGreaterThan(0)
  })
  it('keeps the draft and shows an error when the backend/LLM fails', async () => {
    m.chat.mockRejectedValue(new ApiError('Ollama is not reachable at http://localhost:11434.', 503))
    renderApp('/assistant')
    const box = await screen.findByLabelText('Message')
    await userEvent.type(box, 'hello there')
    await userEvent.click(screen.getByRole('button', { name: 'Send message' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Ollama is not reachable')
    expect(box).toHaveValue('hello there')
  })
  it('passes the selected document scope to the backend', async () => {
    m.chat.mockResolvedValue(REPLY)
    renderApp('/assistant')
    await userEvent.click(await screen.findByRole('button', { name: /All documents/ }))
    await userEvent.click(await screen.findByRole('checkbox', { name: /ml_notes.pdf/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Done' }))
    await userEvent.type(screen.getByLabelText('Message'), 'Summarize')
    await userEvent.click(screen.getByRole('button', { name: 'Send message' }))
    await waitFor(() => expect(m.chat).toHaveBeenCalledWith('Summarize', null, ['d1']))
  })
  it('loads and deletes conversations from history', async () => {
    m.conversations.mockResolvedValue([{ id: 'c1', title: 'Old chat', doc_ids: [], created_at: '', updated_at: '' }])
    m.conversation.mockResolvedValue({ id: 'c1', title: 'Old chat', doc_ids: [], created_at: '', updated_at: '',
      messages: [{ id: 1, role: 'user', content: 'earlier question', meta: {} }, { id: 2, role: 'assistant', content: 'earlier answer', meta: { status: 'answered' } }] })
    m.deleteConversation.mockResolvedValue({})
    renderApp('/assistant')
    await userEvent.click((await screen.findAllByText('Old chat'))[0])
    expect(await screen.findByText('earlier answer')).toBeInTheDocument()
    await userEvent.click(screen.getAllByRole('button', { name: /Delete conversation Old chat/ })[0])
    await waitFor(() => expect(m.deleteConversation).toHaveBeenCalledWith('c1'))
  })
})

describe('Study & Research', () => {
  it('disables Generate until a document or topic is provided', async () => {
    renderApp('/study')
    const btn = await screen.findByRole('button', { name: /Generate/ })
    expect(btn).toBeDisabled()
    await userEvent.type(screen.getByPlaceholderText(/clustering/), 'clustering')
    expect(btn).toBeEnabled()
  })
  it('renders an interactive quiz and marks the correct answer', async () => {
    m.study.mockResolvedValue({ ...REPLY, tool: 'quiz', answer: 'x', structured: { type: 'mcq', items: [{ question: 'What is K-means?', options: ['A clustering algorithm', 'A loss'], answer: 'A clustering algorithm', explanation: 'It clusters.', source: 'S1' }] } })
    renderApp('/study')
    await userEvent.click(await screen.findByRole('tab', { name: /Quizzes/ }))
    await userEvent.click(await screen.findByRole('checkbox', { name: /ml_notes.pdf/ }))
    await userEvent.click(screen.getByRole('button', { name: /Generate/ }))
    await userEvent.click(await screen.findByRole('button', { name: 'A clustering algorithm' }))
    expect(await screen.findByText('It clusters.')).toBeInTheDocument()
    expect(m.study).toHaveBeenCalledWith('quiz', expect.objectContaining({ document_ids: ['d1'], count: 5, quiz_type: 'mcq' }))
  })
  it('shows an insufficient-evidence result as a warning, not a fake answer', async () => {
    m.study.mockResolvedValue({ ...REPLY, status: 'insufficient_evidence', answer: "I couldn't find enough relevant material.", citations: [] })
    renderApp('/study')
    await userEvent.type(await screen.findByPlaceholderText(/clustering/), 'quantum gravity')
    await userEvent.click(screen.getByRole('button', { name: /Generate/ }))
    expect(await screen.findByText(/couldn't find enough relevant material/)).toBeInTheDocument()
    expect(screen.getByText(/insufficient evidence/)).toBeInTheDocument()
  })
  it('requires two documents or concepts for compare', async () => {
    renderApp('/research')
    await userEvent.click(await screen.findByRole('tab', { name: /Compare/ }))
    expect(screen.getByRole('button', { name: 'Compare' })).toBeDisabled()
    await userEvent.type(screen.getByRole('textbox'), 'supervised vs unsupervised')
    expect(screen.getByRole('button', { name: 'Compare' })).toBeEnabled()
  })
  it('runs a passage search and lists results', async () => {
    m.search.mockResolvedValue({ results: REPLY.citations, embedder: 'hashing-384' })
    renderApp('/research')
    await userEvent.click(await screen.findByRole('tab', { name: /Search/ }))
    await userEvent.type(screen.getByRole('textbox'), 'overfitting')
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(await screen.findByText('Overfitting happens when…')).toBeInTheDocument()
  })
})

describe('Analytics & Settings', () => {
  it('shows an empty state with no data', async () => {
    m.overview.mockResolvedValue({ ...OVERVIEW(0), messages: 0 })
    renderApp('/analytics')
    expect(await screen.findByText('Nothing to analyse yet')).toBeInTheDocument()
  })
  it('shows setup instructions when the LLM is offline', async () => {
    m.status.mockResolvedValue({ ...STATUS, llm: { available: false, provider: 'ollama', model: 'qwen2.5:3b-instruct', detail: 'Model not installed. Run: ollama pull qwen2.5:3b-instruct' } })
    renderApp('/settings')
    expect(await screen.findByText(/ollama pull qwen2.5:3b-instruct/, { selector: 'pre' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Re-check connections/ }))
    await waitFor(() => expect(m.status.mock.calls.length).toBeGreaterThan(1))
  })
})

describe('API error formatting', () => {
  it('handles every FastAPI error shape', () => {
    expect(errorMessage('plain')).toBe('plain')
    expect(errorMessage({ error: 'llm_unavailable', message: 'down' })).toBe('down')
    expect(errorMessage([{ filename: 'a', error: 'Duplicate' }])).toBe('Duplicate')
    expect(errorMessage([{ msg: 'field required' }])).toBe('field required')
    expect(errorMessage(undefined)).toBe('Unexpected error')
  })
})
