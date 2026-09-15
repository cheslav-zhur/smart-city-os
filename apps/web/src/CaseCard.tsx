import type { CaseListItem } from './api/generated/models/caseListItem'
import type { EventTapeItem } from './api/generated/models/eventTapeItem'

type CaseCardProps = {
  caseRow: CaseListItem | null
  speeds: EventTapeItem[]
  busy: boolean
  onApprove: () => void
  onReject: () => void
}

export function CaseCard({
  caseRow,
  speeds,
  busy,
  onApprove,
  onReject,
}: CaseCardProps) {
  const canDecide = caseRow !== null && caseRow.status === 'open' && !busy

  return (
    <section className="card">
      {caseRow !== null ? (
        <>
          <dl className="case-meta">
            <div>
              <dt>id</dt>
              <dd>{caseRow.id}</dd>
            </div>
            <div>
              <dt>segment</dt>
              <dd>{caseRow.segment}</dd>
            </div>
            <div>
              <dt>status</dt>
              <dd>{caseRow.status}</dd>
            </div>
            <div>
              <dt>drone_status</dt>
              <dd>{caseRow.drone_status}</dd>
            </div>
          </dl>
          <p className="proposal">Send a drone to look</p>
          {caseRow.rationale ? (
            <p className="rationale">{caseRow.rationale}</p>
          ) : null}
          <div className="actions">
            <button type="button" disabled={!canDecide} onClick={onApprove}>
              Send drone
            </button>
            <button type="button" disabled={!canDecide} onClick={onReject}>
              Dismiss
            </button>
          </div>
        </>
      ) : null}

      <h2>Last speeds</h2>
      {speeds.length === 0 ? (
        <p className="empty">No speed samples yet.</p>
      ) : (
        <table className="speed-table">
          <thead>
            <tr>
              <th>event_id</th>
              <th>segment</th>
              <th>speed</th>
              <th>recorded_at</th>
            </tr>
          </thead>
          <tbody>
            {speeds.map((row) => (
              <tr key={row.event_id}>
                <td>{row.event_id}</td>
                <td>{row.segment}</td>
                <td>{row.speed}</td>
                <td>{row.recorded_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
