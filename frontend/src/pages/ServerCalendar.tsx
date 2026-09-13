import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { DateSelectArg, EventClickArg } from '@fullcalendar/core'
import { api, Reservation } from '../api'
import { useAuth } from '../AuthContext'

export default function ServerCalendar() {
  const { serverId } = useParams()
  const id = Number(serverId)
  const { user } = useAuth()
  const [reservations, setReservations] = useState<Reservation[]>([])
  const calendarRef = useRef<FullCalendar>(null)

  const refresh = () => {
    api.serverCalendar(id).then(setReservations)
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  useEffect(() => {
    // FullCalendar can mis-measure its width on mount (most visibly under
    // React StrictMode's double-invoke in dev) - nudge it to remeasure
    // once the layout has actually settled.
    const timer = setTimeout(() => calendarRef.current?.getApi().updateSize(), 0)
    return () => clearTimeout(timer)
  }, [])

  const events = reservations
    .filter((r) => r.status === 'active')
    .map((r) => ({
      id: String(r.id),
      title: r.purpose || `User ${r.user_id}`,
      start: r.start_time,
      end: r.end_time,
      color: r.idle_flagged ? '#d97706' : '#2563eb',
    }))

  const handleSelect = async (arg: DateSelectArg) => {
    const calendarApi = arg.view.calendar
    if (!user) {
      alert('Pick who you are from the top right first.')
      calendarApi.unselect()
      return
    }
    const purpose = window.prompt('What are you using it for?') || undefined
    try {
      await api.createReservation({
        server_id: id,
        user_id: user.id,
        start_time: arg.start.toISOString(),
        end_time: arg.end.toISOString(),
        purpose,
      })
      refresh()
    } catch (err) {
      alert((err as Error).message)
    } finally {
      calendarApi.unselect()
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
      <p className="calendar-hint">
        Click and drag across the time you want to book. Click an existing booking to release it.
      </p>
      <div className="calendar-wrap">
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          events={events}
          selectable
          select={handleSelect}
          eventClick={handleEventClick}
          height="100%"
          scrollTime="07:00:00"
        />
      </div>
    </div>
  )
}
