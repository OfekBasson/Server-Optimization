import { useState } from 'react'

type Props = {
  title: string
  message?: string
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDeleteModal({ title, message, onConfirm, onCancel }: Props) {
  const [text, setText] = useState('')

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        {message && <p>{message}</p>}
        <p>
          Type <strong>DELETE</strong> to confirm.
        </p>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="DELETE" autoFocus />
        <div className="modal-actions">
          <button className="secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="danger" onClick={onConfirm} disabled={text !== 'DELETE'}>
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
