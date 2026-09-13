const API_BASE = '/api'

export type ReservationStatus = 'active' | 'ended' | 'released'
export type WatchRequestStatus = 'active' | 'fulfilled' | 'expired'

export type Reservation = {
  id: number
  server_id: number
  user_id: number
  start_time: string
  end_time: string
  purpose: string | null
  status: ReservationStatus
  idle_flagged: boolean
  idle_since: string | null
}

export type Server = {
  id: number
  name: string
  hostname: string | null
  gpu_type: string | null
  gpu_count: number
  vram_gb: number | null
  cpu_cores: number | null
  ram_gb: number | null
  disk_gb: number | null
  current_reservation: Reservation | null
  is_idle_flagged: boolean
}

export type CurrentUser = {
  id: number
  name: string
  university_email: string
  whatsapp_number: string | null
  is_admin: boolean
}

export type UserSummary = {
  id: number
  name: string
  university_email: string
}

export type WatchRequest = {
  id: number
  user_id: number
  min_vram_gb: number | null
  gpu_type: string | null
  min_gpu_count: number | null
  min_cpu_cores: number | null
  min_ram_gb: number | null
  status: WatchRequestStatus
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options,
  })
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${await response.text()}`)
  }
  return response.json()
}

export const api = {
  listServers: () => request<Server[]>('/servers'),
  serverCalendar: (serverId: number) => request<Reservation[]>(`/servers/${serverId}/calendar`),
  createReservation: (payload: {
    server_id: number
    user_id: number
    start_time: string
    end_time: string
    purpose?: string
  }) => request<Reservation>('/reservations', { method: 'POST', body: JSON.stringify(payload) }),
  releaseReservation: (id: number) =>
    request<Reservation>(`/reservations/${id}/release`, { method: 'POST' }),
  listWatchRequests: (userId: number) =>
    request<WatchRequest[]>(`/watch-requests?user_id=${userId}`),
  createWatchRequest: (payload: { user_id: number; min_vram_gb?: number; gpu_type?: string }) =>
    request<WatchRequest>('/watch-requests', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => request<CurrentUser>('/auth/me'),
  logout: () => request<{ status: string }>('/auth/logout', { method: 'POST' }),
  adminLogin: (username: string, password: string) =>
    request<CurrentUser>('/auth/admin-login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  listSelectableUsers: () => request<UserSummary[]>('/auth/users'),

  adminListUsers: () => request<CurrentUser[]>('/admin/users'),
  adminCreateUser: (payload: {
    name: string
    university_email: string
    whatsapp_number?: string
    is_admin?: boolean
    password?: string
  }) => request<CurrentUser>('/admin/users', { method: 'POST', body: JSON.stringify(payload) }),
  adminUpdateUser: (
    id: number,
    payload: Partial<{ name: string; whatsapp_number: string; is_admin: boolean }>,
  ) => request<CurrentUser>(`/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  adminSetPassword: (id: number, password: string) =>
    request<{ status: string }>(`/admin/users/${id}/set-password`, {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),
}
