import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { DateSelectArg, EventMountArg } from '@fullcalendar/core'
import { api, Reservation, UserSummary } from '../api'
import IdentifyModal from '../IdentifyModal'
import ConfirmDeleteModal from '../ConfirmDeleteModal'
import EventContextMenu from '../EventContextMenu'

type ContextMenuState = { x: number; y: number; id: number; title: string }

export default function ServerCalendar() {
  const { serverId } = useParams()
  const id = Number(serverId)
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [pendingSelection, setPendingSelection] = useState<{ start: Date; end: Date } | null>(null)
  const [pendingRelease, setPendingRelease] = useState<{ id: number; title: string } | null>(null)
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)
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

  const handleSelect = (arg: DateSelectArg) => {
    setPendingSelection({ start: arg.start, end: arg.end })
  }

  const cancelSelection = () => {
    setPendingSelection(null)
    calendarRef.current?.getApi().unselect()
  }

  const confirmSelection = async (chosenUser: UserSummary) => {
    if (!pendingSelection) return
    const purpose = window.prompt('What are you using it for?') || undefined
    try {
      await api.createReservation({
        server_id: id,
        user_id: chosenUser.id,
        start_time: pendingSelection.start.toISOString(),
        end_time: pendingSelection.end.toISOString(),
        purpose,
      })
      refresh()
    } catch (err) {
      alert((err as Error).message)
    } finally {
      cancelSelection()
    }
  }

  const handleEventDidMount = (info: EventMountArg) => {
    const onContextMenu = (e: MouseEvent) => {
      e.preventDefault()
      setContextMenu({
        x: e.clientX,
        y: e.clientY,
        id: Number(info.event.id),
        title: info.event.title,
      })
    }
    info.el.addEventListener('contextmenu', onContextMenu)
    ;(info.el as HTMLElement & { _contextMenuHandler?: (e: MouseEvent) => void })._contextMenuHandler =
      onContextMenu
  }

  const handleEventWillUnmount = (info: EventMountArg) => {
    const el = info.el as HTMLElement & { _contextMenuHandler?: (e: MouseEvent) => void }
    if (el._contextMenuHandler) el.removeEventListener('contextmenu', el._contextMenuHandler)
  }

  const requestDelete = () => {
    if (!contextMenu) return
    setPendingRelease({ id: contextMenu.id, title: contextMenu.title })
    setContextMenu(null)
  }

  const confirmRelease = async () => {
    if (!pendingRelease) return
    await api.releaseReservation(pendingRelease.id)
    setPendingRelease(null)
    refresh()
  }

  return (
    <div className="server-calendar">
      <h1>Server {id}</h1>
      <p className="calendar-hint">
        Click and drag across the time you want to book. Right-click an existing booking to release it.
      </p>
      <div className="calendar-wrap">
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          events={events}
          selectable
          select={handleSelect}
          eventDidMount={handleEventDidMount}
          eventWillUnmount={handleEventWillUnmount}
          height="100%"
          scrollTime="07:00:00"
        />
      </div>
      {contextMenu && (
        <EventContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onDelete={requestDelete}
          onClose={() => setContextMenu(null)}
        />
      )}
      {pendingSelection && (
        <IdentifyModal
          title="Who's booking this?"
          onConfirm={confirmSelection}
          onCancel={cancelSelection}
        />
      )}
      {pendingRelease && (
        <ConfirmDeleteModal
          title="Release this reservation?"
          message={pendingRelease.title}
          onConfirm={confirmRelease}
          onCancel={() => setPendingRelease(null)}
        />
      )}
    </div>
  )
}
