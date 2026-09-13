import { useState } from 'react'
import WatchRequestModal from './WatchRequestModal'

export default function NotifyMeButton() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button className="nav-link-button" onClick={() => setOpen(true)}>
        Notify me when free
      </button>
      {open && <WatchRequestModal onClose={() => setOpen(false)} />}
    </>
  )
}
