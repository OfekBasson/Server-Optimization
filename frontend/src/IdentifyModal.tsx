import { useEffect, useState } from 'react'
import { api, UserSummary } from './api'

type Props = {
  title?: string
  onConfirm: (user: UserSummary) => void
  onCancel: () => void
}

export default function IdentifyModal({ title = 'Who are you?', onConfirm, onCancel }: Props) {
  const [users, setUsers] = useState<UserSummary[]>([])
  const [selected, setSelected] = useState('')

  useEffect(() => {
    api.listSelectableUsers().then(setUsers)
  }, [])

  const confirm = () => {
    const user = users.find((u) => String(u.id) === selected)
    if (user) onConfirm(user)
  }

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        {users.length === 0 ? (
          <p>No users yet - ask an admin to add you first.</p>
        ) : (
          <select value={selected} onChange={(e) => setSelected(e.target.value)} autoFocus>
            <option value="">Select your name</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        )}
        <div className="modal-actions">
          <button className="secondary" onClick={onCancel}>
            Cancel
          </button>
          <button onClick={confirm} disabled={!selected}>
            Continue
          </button>
        </div>
      </div>
    </div>
  )
}
