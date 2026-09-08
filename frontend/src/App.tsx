import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ServerCalendar from './pages/ServerCalendar'
import WatchRequests from './pages/WatchRequests'

export default function App() {
  return (
    <div className="app">
      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/watch-requests">Notify me when free</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/servers/:serverId" element={<ServerCalendar />} />
        <Route path="/watch-requests" element={<WatchRequests />} />
      </Routes>
    </div>
  )
}
