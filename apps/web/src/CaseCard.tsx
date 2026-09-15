import type { CaseListItem } from './api/generated/models/caseListItem'
import type { EventTapeItem } from './api/generated/models/eventTapeItem'

type CaseCardProps = {
  caseRow: CaseListItem | null
  speeds: EventTapeItem[]
  busy: boolean
  onApprove: () => void
  onReject: () => void
}

function statusTone(status: string): string {
  if (status === 'open') {
    return 'bg-teal-500/15 text-teal-800 dark:text-teal-200'
  }
  if (status === 'approved') {
    return 'bg-slate-900/8 text-slate-700 dark:bg-white/10 dark:text-slate-200'
  }
  return 'bg-slate-900/5 text-slate-500 dark:bg-white/5 dark:text-slate-400'
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
    <section className="rounded-2xl bg-white/80 p-7 shadow-[0_1px_0_rgba(15,23,42,0.04)] dark:bg-white/[0.03] dark:shadow-none dark:ring-1 dark:ring-white/[0.06]">
      {caseRow !== null ? (
        <>
          <div className="mb-6 flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Case {caseRow.id} · segment {caseRow.segment}
            </span>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusTone(caseRow.status)}`}
            >
              {caseRow.status}
            </span>
            <span className="rounded-full bg-slate-900/5 px-2.5 py-0.5 text-xs text-slate-600 dark:bg-white/5 dark:text-slate-300">
              drone {caseRow.drone_status.replaceAll('_', ' ')}
            </span>
          </div>

          <p className="mb-2 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
            Send a drone to look
          </p>
          {caseRow.rationale ? (
            <p className="mb-6 max-w-2xl text-[0.95rem] leading-relaxed text-slate-600 dark:text-slate-300">
              {caseRow.rationale}
            </p>
          ) : (
            <p className="mb-6 max-w-2xl text-[0.95rem] leading-relaxed text-slate-500 dark:text-slate-400">
              Rule proposal is ready. Confirm to dispatch, or dismiss.
            </p>
          )}

          <div className="mb-10 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={!canDecide}
              onClick={onApprove}
              className="cursor-pointer rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-teal-500 dark:text-slate-950 dark:hover:bg-teal-400"
            >
              Send drone
            </button>
            <button
              type="button"
              disabled={!canDecide}
              onClick={onReject}
              className="cursor-pointer rounded-xl bg-slate-900/5 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-900/10 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10"
            >
              Dismiss
            </button>
          </div>
        </>
      ) : (
        <p className="mb-10 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
          Select a case from the list, or wait for the simulator.
        </p>
      )}

      <div className="border-t border-slate-900/5 pt-6 dark:border-white/5">
        <h2 className="mb-4 text-sm font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
          Last speeds
        </h2>
        {speeds.length === 0 ? (
          <p className="m-0 text-sm text-slate-500 dark:text-slate-400">
            No speed samples yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-left text-xs tracking-wide text-slate-500 uppercase dark:text-slate-400">
                  <th className="pb-2 pr-4 font-medium">event</th>
                  <th className="pb-2 pr-4 font-medium">segment</th>
                  <th className="pb-2 pr-4 font-medium">speed</th>
                  <th className="pb-2 font-medium">recorded</th>
                </tr>
              </thead>
              <tbody className="font-mono text-[0.8rem]">
                {speeds.map((row) => (
                  <tr
                    key={row.event_id}
                    className="border-t border-slate-900/5 text-slate-700 dark:border-white/5 dark:text-slate-300"
                  >
                    <td className="py-2.5 pr-4 align-top">{row.event_id}</td>
                    <td className="py-2.5 pr-4 align-top">{row.segment}</td>
                    <td className="py-2.5 pr-4 align-top">{row.speed}</td>
                    <td className="py-2.5 align-top">{row.recorded_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
