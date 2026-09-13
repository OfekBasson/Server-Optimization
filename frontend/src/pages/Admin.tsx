import { FormEvent, useEffect, useState } from 'react'
import { api, CurrentUser } from '../api'
import { useAuth } from '../AuthContext'

export default function Admin() {
  const { admin } = useAuth()
  const [users, setUsers] = useState<CurrentUser[]>([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [whatsapp, setWhatsapp] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    api
      .adminListUsers()
      .then(setUsers)
      .catch((err: Error) => setError(err.message))
  }

  useEffect(load, [])

  if (!admin) return <p>Please log in as admin first.</p>

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await api.adminCreateUser({ name, university_email: email, whatsapp_number: whatsapp || undefined })
      setName('')
      setEmail('')
      setWhatsapp('')
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const toggleAdmin = async (u: CurrentUser) => {
    if (!u.is_admin) {
      const password = window.prompt(`Set a password for ${u.name} (needed to log in as admin):`)
      if (!password) return
      await api.adminUpdateUser(u.id, { is_admin: true })
      await api.adminSetPassword(u.id, password)
    } else {
      await api.adminUpdateUser(u.id, { is_admin: false })
    }
    load()
  }

  const setPassword = async (u: CurrentUser) => {
    const password = window.prompt(`New password for ${u.name}:`)
    if (!password) return
    await api.adminSetPassword(u.id, password)
    alert('Password updated.')
  }

  return (
    <div className="admin">
      <h1>Admin - manage users</h1>

      <form onSubmit={submit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          University email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          WhatsApp number (optional)
          <input value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} placeholder="+15551234567" />
        </label>
        <button type="submit">Add user</button>
      </form>
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>WhatsApp</th>
            <th>Admin</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.university_email}</td>
              <td>{u.whatsapp_number || '-'}</td>
              <td>
                <button onClick={() => toggleAdmin(u)}>{u.is_admin ? 'Revoke' : 'Make admin'}</button>
              </td>
              <td>{u.is_admin && <button onClick={() => setPassword(u)}>Set password</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
