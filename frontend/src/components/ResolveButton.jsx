export default function ResolveButton({ issueId }) {
  return (
    <button
      className="badge"
      style={{ cursor: 'pointer', border: 'none' }}
      onClick={() => alert(`Resolve ${issueId} — Phase 6`)}
    >
      Resolve
    </button>
  )
}
