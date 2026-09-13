import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ServerCalendar from './pages/ServerCalendar'
import WatchRequests from './pages/WatchRequests'
import Admin from './pages/Admin'
import AdminLoginForm from './AdminLoginForm'
import { AuthProvider, useAuth } from './AuthContext'

function AuthStatus() {
  const { admin, loading, logout } = useAuth()
  if (loading) return null
  if (!admin) return <AdminLoginForm />
  return (
    <span>
      Admin: {admin.name} · <button onClick={logout}>Sign out</button>
    </span>
  )
}

function AdminLink() {
  const { admin } = useAuth()
  if (!admin) return null
  return <Link to="/admin">Admin</Link>
}

function AppShell() {
  const location = useLocation()
  const isCalendar = location.pathname.startsWith('/servers/')

  return (
    <div className={isCalendar ? 'app wide' : 'app'}>
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
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}
