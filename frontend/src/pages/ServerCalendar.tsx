import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin, { DateClickArg } from '@fullcalendar/interaction'
import { EventClickArg } from '@fullcalendar/core'
import { api, Reservation } from '../api'

export default function ServerCalendar() {
  const { serverId } = useParams()
  const id = Number(serverId)
  const [reservations, setReservations] = useState<Reservation[]>([])

  const refresh = () => {
    api.serverCalendar(id).then(setReservations)
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const events = reservations
    .filter((r) => r.status === 'active')
    .map((r) => ({
      id: String(r.id),
      title: r.purpose || `User ${r.user_id}`,
      start: r.start_time,
      end: r.end_time,
      color: r.idle_flagged ? '#d97706' : '#2563eb',
    }))

  const handleDateClick = async (arg: DateClickArg) => {
    const userIdInput = window.prompt('Your user ID')
    if (!userIdInput) return
    const purpose = window.prompt('What are you using it for?') || undefined
    const start = new Date(arg.dateStr)
    const end = new Date(start.getTime() + 60 * 60 * 1000)
    try {
      await api.createReservation({
        server_id: id,
        user_id: Number(userIdInput),
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        purpose,
      })
      refresh()
    } catch (err) {
      alert((err as Error).message)
    }
  }

  const handleEventClick = async (arg: EventClickArg) => {
    if (window.confirm('Release this reservation?')) {
      await api.releaseReservation(Number(arg.event.id))
      refresh()
    }
  }

  return (
    <div className="server-calendar">
      <h1>Server {id}</h1>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        events={events}
        selectable
        dateClick={handleDateClick}
        eventClick={handleEventClick}
        height="auto"
      />
    </div>
  )
}
