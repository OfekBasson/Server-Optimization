import { FormEvent, useState } from 'react'
import { api, UserSummary, WatchRequest } from '../api'
import IdentifyModal from '../IdentifyModal'

type Pending = 'create' | 'view' | null

export default function WatchRequests() {
  const [minVram, setMinVram] = useState('')
  const [gpuType, setGpuType] = useState('')
  const [pending, setPending] = useState<Pending>(null)
  const [requests, setRequests] = useState<WatchRequest[] | null>(null)
  const [viewedAs, setViewedAs] = useState<UserSummary | null>(null)

  const submit = (e: FormEvent) => {
    e.preventDefault()
    setPending('create')
  }

  const handleIdentified = async (user: UserSummary) => {
    if (pending === 'create') {
      await api.createWatchRequest({
        user_id: user.id,
        min_vram_gb: minVram ? Number(minVram) : undefined,
        gpu_type: gpuType || undefined,
      })
      setMinVram('')
      setGpuType('')
      alert(`Watch request created for ${user.name}.`)
    } else if (pending === 'view') {
      setViewedAs(user)
      setRequests(await api.listWatchRequests(user.id))
    }
    setPending(null)
  }

  return (
    <div className="watch-requests">
      <h1>Notify me when a server is free</h1>
      <form onSubmit={submit}>
        <label>
          Min VRAM (GB)
          <input value={minVram} onChange={(e) => setMinVram(e.target.value)} type="number" />
        </label>
        <label>
          GPU type
          <input
            value={gpuType}
            onChange={(e) => setGpuType(e.target.value)}
            placeholder="e.g. RTX 3090"
          />
        </label>
        <button type="submit">Create watch request</button>
      </form>

      <button onClick={() => setPending('view')}>View my requests</button>

      {requests && (
        <>
          <h2>{viewedAs?.name}'s requests</h2>
          <ul>
            {requests.map((r) => (
              <li key={r.id}>
                {r.gpu_type || 'any GPU'} · min {r.min_vram_gb ?? '-'}GB · {r.status}
              </li>
            ))}
          </ul>
        </>
      )}

      {pending && (
        <IdentifyModal
          title={pending === 'create' ? 'Who is this request for?' : 'Whose requests do you want to see?'}
          onConfirm={handleIdentified}
          onCancel={() => setPending(null)}
        />
      )}
    </div>
  )
}
