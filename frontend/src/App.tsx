import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ServerCalendar from './pages/ServerCalendar'
import WatchRequests from './pages/WatchRequests'
import Admin from './pages/Admin'
import UserPicker from './UserPicker'
import { AuthProvider, useAuth } from './AuthContext'

function AuthStatus() {
  const { user, loading, logout } = useAuth()
  if (loading) return null
  if (!user) return <UserPicker />
  return (
    <span>
      {user.name} · <button onClick={logout}>Sign out</button>
    </span>
  )
}

function AdminLink() {
  const { user } = useAuth()
  if (!user?.is_admin) return null
  return <Link to="/admin">Admin</Link>
}

export default function App() {
  return (
    <AuthProvider>
      <div className="app">
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/watch-requests">Notify me when free</Link>
          <AdminLink />
          <span className="nav-auth">
            <AuthStatus />
          </span>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/servers/:serverId" element={<ServerCalendar />} />
          <Route path="/watch-requests" element={<WatchRequests />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </div>
    </AuthProvider>
  )
}
