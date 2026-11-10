import { Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Analytics from './pages/Analytics'
import Chat from './pages/Chat'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Research from './pages/Research'
import Settings from './pages/Settings'
import Study from './pages/Study'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="assistant" element={<Chat />} />
        <Route path="documents" element={<Documents />} />
        <Route path="research" element={<Research />} />
        <Route path="study" element={<Study />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<div className="p-10 text-center text-slate-500">Page not found.</div>} />
      </Route>
    </Routes>
  )
}
