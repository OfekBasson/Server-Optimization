type Props = {
  x: number
  y: number
  onDelete: () => void
  onClose: () => void
}

export default function EventContextMenu({ x, y, onDelete, onClose }: Props) {
  return (
    <div
      className="context-menu-overlay"
      onClick={onClose}
      onContextMenu={(e) => {
        e.preventDefault()
        onClose()
      }}
    >
      <div className="context-menu" style={{ top: y, left: x }} onClick={(e) => e.stopPropagation()}>
        <button onClick={onDelete}>Delete</button>
      </div>
    </div>
  )
}
