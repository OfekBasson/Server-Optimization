import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api, CurrentUser } from './api'

// Represents the signed-in ADMIN only - regular users never have a
// session (see IdentifyModal for how they're asked who they are, inline,
// only when booking or creating a watch request).
type AuthContextValue = {
  admin: CurrentUser | null
  loading: boolean
  refresh: () => void
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api
      .me()
      .then(setAdmin)
      .catch(() => setAdmin(null))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const login = async (username: string, password: string) => {
    const user = await api.adminLogin(username, password)
    setAdmin(user)
  }

  const logout = async () => {
    await api.logout()
    setAdmin(null)
  }

  return (
    <AuthContext.Provider value={{ admin, loading, refresh: load, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
