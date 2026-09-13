import { FormEvent, useEffect, useState } from 'react'
import { api, Server, UserSummary, WatchRequest } from './api'
import IdentifyModal from './IdentifyModal'

type Pending = 'create' | 'view' | null

export default function WatchRequestModal({ onClose }: { onClose: () => void }) {
  const [gpuTypes, setGpuTypes] = useState<string[]>([])
  const [selectedGpuTypes, setSelectedGpuTypes] = useState<string[]>([])
  const [minGpuCount, setMinGpuCount] = useState('')
  const [pending, setPending] = useState<Pending>(null)
  const [requests, setRequests] = useState<WatchRequest[] | null>(null)
  const [viewedAs, setViewedAs] = useState<UserSummary | null>(null)

  useEffect(() => {
    api.listServers().then((servers: Server[]) => {
      const types = Array.from(new Set(servers.map((s) => s.gpu_type).filter((t): t is string => !!t)))
      setGpuTypes(types.sort())
    })
  }, [])

  const toggleGpuType = (type: string) => {
    setSelectedGpuTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    )
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    setPending('create')
  }

  const handleIdentified = async (user: UserSummary) => {
    if (pending === 'create') {
      await api.createWatchRequest({
        user_id: user.id,
        gpu_types: selectedGpuTypes.length ? selectedGpuTypes : undefined,
        min_gpu_count: minGpuCount ? Number(minGpuCount) : undefined,
      })
      setSelectedGpuTypes([])
      setMinGpuCount('')
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
            GPU type (any checked, or leave blank for any GPU)
            <div className="checkbox-group">
              {gpuTypes.map((t) => (
                <label key={t} className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={selectedGpuTypes.includes(t)}
                    onChange={() => toggleGpuType(t)}
                  />
                  {t}
                </label>
              ))}
            </div>
          </label>
          <label>
            Min GPUs needed
            <input
              value={minGpuCount}
              onChange={(e) => setMinGpuCount(e.target.value)}
              type="number"
              min="1"
            />
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
                    {r.gpu_types?.length ? r.gpu_types.join(' / ') : 'any GPU'} · min{' '}
                    {r.min_gpu_count ?? 1} GPU{(r.min_gpu_count ?? 1) === 1 ? '' : 's'} · {r.status}
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
