import { FormEvent, useState } from 'react'
import { useAuth } from './AuthContext'

export default function AdminLoginForm() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await login(username, password)
    } catch {
      setError('Invalid username or password')
    }
  }

  return (
    <form className="admin-login" onSubmit={submit}>
      <input
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Admin email"
        type="email"
        required
      />
      <input
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        type="password"
        required
      />
      <button type="submit">Admin login</button>
      {error && <span className="error">{error}</span>}
    </form>
  )
}
