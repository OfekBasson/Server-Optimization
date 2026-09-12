import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ServerCalendar from './pages/ServerCalendar'
import WatchRequests from './pages/WatchRequests'
import { AuthProvider, useAuth } from './AuthContext'

function AuthStatus() {
  const { user, loading, logout } = useAuth()
  if (loading) return null
  if (!user) {
    return <a href="/api/auth/login">Sign in with Microsoft</a>
  }
  return (
    <span>
      {user.name} · <button onClick={logout}>Sign out</button>
    </span>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <div className="app">
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/watch-requests">Notify me when free</Link>
          <span className="nav-auth">
            <AuthStatus />
          </span>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/servers/:serverId" element={<ServerCalendar />} />
          <Route path="/watch-requests" element={<WatchRequests />} />
        </Routes>
      </div>
    </AuthProvider>
  )
}
