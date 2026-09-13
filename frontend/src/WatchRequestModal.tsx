import { FormEvent, useEffect, useState } from 'react'
import { api, Server, UserSummary, WatchRequest } from './api'
import IdentifyModal from './IdentifyModal'

type Pending = 'create' | 'view' | null

export default function WatchRequestModal({ onClose }: { onClose: () => void }) {
  const [gpuTypes, setGpuTypes] = useState<string[]>([])
  const [minVram, setMinVram] = useState('')
  const [gpuType, setGpuType] = useState('')
  const [pending, setPending] = useState<Pending>(null)
  const [requests, setRequests] = useState<WatchRequest[] | null>(null)
  const [viewedAs, setViewedAs] = useState<UserSummary | null>(null)

  useEffect(() => {
    api.listServers().then((servers: Server[]) => {
      const types = Array.from(new Set(servers.map((s) => s.gpu_type).filter((t): t is string => !!t)))
      setGpuTypes(types.sort())
    })
  }, [])

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
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <h2>Notify me when a server is free</h2>
        <form onSubmit={submit}>
          <label>
            Min VRAM (GB)
            <input value={minVram} onChange={(e) => setMinVram(e.target.value)} type="number" min="0" />
          </label>
          <label>
            GPU type
            <select value={gpuType} onChange={(e) => setGpuType(e.target.value)}>
              <option value="">Any GPU</option>
              {gpuTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <button type="submit">Create watch request</button>
        </form>

        <button onClick={() => setPending('view')}>View my requests</button>

        {requests && (
          <div className="watch-request-list">
            <h3>{viewedAs?.name}'s requests</h3>
            {requests.length === 0 ? (
              <p>No requests yet.</p>
            ) : (
              <ul>
                {requests.map((r) => (
                  <li key={r.id}>
                    {r.gpu_type || 'any GPU'} · min {r.min_vram_gb ?? '-'}GB · {r.status}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="modal-actions">
          <button className="secondary" onClick={onClose}>
            Close
          </button>
        </div>

        {pending && (
          <IdentifyModal
            title={pending === 'create' ? 'Who is this request for?' : 'Whose requests do you want to see?'}
            onConfirm={handleIdentified}
            onCancel={() => setPending(null)}
          />
        )}
      </div>
    </div>
  )
}
