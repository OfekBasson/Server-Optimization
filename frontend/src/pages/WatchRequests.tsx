import { FormEvent, useEffect, useState } from 'react'
import { api, WatchRequest } from '../api'

export default function WatchRequests() {
  const [userId, setUserId] = useState('')
  const [minVram, setMinVram] = useState('')
  const [gpuType, setGpuType] = useState('')
  const [requests, setRequests] = useState<WatchRequest[]>([])

  const load = async (id: string) => {
    if (!id) return
    setRequests(await api.listWatchRequests(Number(id)))
  }

  useEffect(() => {
    // no-op on mount: user ID is entered by hand for now, until auth is wired up
  }, [])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    await api.createWatchRequest({
      user_id: Number(userId),
      min_vram_gb: minVram ? Number(minVram) : undefined,
      gpu_type: gpuType || undefined,
    })
    load(userId)
  }

  return (
    <div className="watch-requests">
      <h1>Notify me when a server is free</h1>
      <form onSubmit={submit}>
        <label>
          Your user ID
          <input value={userId} onChange={(e) => setUserId(e.target.value)} required />
        </label>
        <label>
          Min VRAM (GB)
          <input value={minVram} onChange={(e) => setMinVram(e.target.value)} type="number" />
        </label>
        <label>
          GPU type
          <input value={gpuType} onChange={(e) => setGpuType(e.target.value)} placeholder="e.g. A100" />
        </label>
        <button type="submit">Create watch request</button>
      </form>

      <button onClick={() => load(userId)}>Refresh my requests</button>
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
