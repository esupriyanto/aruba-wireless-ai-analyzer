import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ClientDetail from './pages/ClientDetail'
import AuditLog from './pages/AuditLog'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/clients/:mac" element={<ClientDetail />} />
      <Route path="/audit" element={<AuditLog />} />
    </Routes>
  )
}
