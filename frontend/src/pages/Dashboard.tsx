import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, Server } from '../api'

export default function Dashboard() {
  const [servers, setServers] = useState<Server[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.listServers().then(setServers).catch((err: Error) => setError(err.message))
  }, [])

  if (error) return <p className="error">Failed to load servers: {error}</p>

  return (
    <div className="dashboard">
      <h1>Canvas Lab Servers</h1>
      <div className="server-grid">
        {servers.map((server) => {
          const statusClass = !server.current_reservation
            ? 'free'
            : server.is_idle_flagged
              ? 'idle'
              : 'busy'
          const statusText = !server.current_reservation
            ? 'Free'
            : server.is_idle_flagged
              ? 'Reserved · looks idle'
              : 'Reserved'

          return (
            <Link to={`/servers/${server.id}`} key={server.id} className="server-card">
              <h2>{server.name}</h2>
              <p>
                {server.gpu_type ?? 'GPU n/a'} x{server.gpu_count} · {server.vram_gb ?? '?'}GB VRAM
              </p>
              <span className={`status ${statusClass}`}>{statusText}</span>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
