import { useEffect, useState } from 'react'
import { api, UserSummary } from './api'
import { useAuth } from './AuthContext'

export default function UserPicker() {
  const { refresh } = useAuth()
  const [users, setUsers] = useState<UserSummary[]>([])
  const [selected, setSelected] = useState('')

  useEffect(() => {
    api.listSelectableUsers().then(setUsers)
  }, [])

  const go = async () => {
    if (!selected) return
    await api.selectUser(Number(selected))
    refresh()
  }

  return (
    <span className="user-picker">
      <select value={selected} onChange={(e) => setSelected(e.target.value)}>
        <option value="">Who are you?</option>
        {users.map((u) => (
          <option key={u.id} value={u.id}>
            {u.name}
          </option>
        ))}
      </select>
      <button onClick={go} disabled={!selected}>
        Continue
      </button>
    </span>
  )
}
