import { FormEvent, useEffect, useState } from 'react'
import { api, WatchRequest } from '../api'
import { useAuth } from '../AuthContext'

export default function WatchRequests() {
  const { user } = useAuth()
  const [minVram, setMinVram] = useState('')
  const [gpuType, setGpuType] = useState('')
  const [requests, setRequests] = useState<WatchRequest[]>([])

  const load = async () => {
    if (!user) return
    setRequests(await api.listWatchRequests(user.id))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) return
    await api.createWatchRequest({
      user_id: user.id,
      min_vram_gb: minVram ? Number(minVram) : undefined,
      gpu_type: gpuType || undefined,
    })
    load()
  }

  if (!user) {
    return (
      <div className="watch-requests">
        <h1>Notify me when a server is free</h1>
        <p>
          Please <a href="/api/auth/login">sign in with Microsoft</a> first.
        </p>
      </div>
    )
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

      <ul>
        {requests.map((r) => (
          <li key={r.id}>
            {r.gpu_type || 'any GPU'} · min {r.min_vram_gb ?? '-'}GB · {r.status}
          </li>
        ))}
      </ul>
    </div>
  )
}
