import { useEffect, useState } from 'react'
import type { CaseListItem } from './api/generated/models/caseListItem'
import type { EventTapeItem } from './api/generated/models/eventTapeItem'
import { StatusChip } from './StatusChip'
import { formatRelativeTime, isCollapseSpeed } from './time'

type DecideKind = 'approve' | 'reject'

type CaseCardProps = {
  caseRow: CaseListItem | null
  speeds: EventTapeItem[]
  busy: boolean
  busyKind: DecideKind | null
  casesLoading?: boolean
  speedsLoading?: boolean
  onApprove: () => void
  onReject: () => void
}

const focusRing =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f4f6f8] dark:focus-visible:ring-offset-[#0b1220]'

export function CaseCard({
  caseRow,
  speeds,
  busy,
  busyKind,
  casesLoading = false,
  speedsLoading = false,
  onApprove,
  onReject,
}: CaseCardProps) {
  const [nowMs, setNowMs] = useState(() => Date.now())
  const canDecide = caseRow !== null && caseRow.status === 'open' && !busy

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now())
    }, 15_000)
    return () => {
      window.clearInterval(timer)
    }
  }, [])

  const newestCollapseId = speeds.find((row) => isCollapseSpeed(row.speed))
    ?.event_id

  return (
    <section className="rounded-2xl bg-white/80 p-7 shadow-[0_1px_0_rgba(15,23,42,0.04)] dark:bg-white/[0.03] dark:shadow-none dark:ring-1 dark:ring-white/[0.06]">
      {casesLoading && caseRow === null ? (
        <div className="mb-10 space-y-3" aria-hidden="true">
          <div className="h-4 w-40 animate-pulse rounded bg-slate-900/5 dark:bg-white/5" />
          <div className="h-8 w-72 animate-pulse rounded bg-slate-900/5 dark:bg-white/5" />
          <div className="h-4 w-full max-w-md animate-pulse rounded bg-slate-900/5 dark:bg-white/5" />
        </div>
      ) : caseRow !== null ? (
        <>
          <div className="mb-6 flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Case {caseRow.id} · segment {caseRow.segment}
            </span>
            <StatusChip status={caseRow.status} />
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
              className={`cursor-pointer rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-teal-500 dark:text-slate-950 dark:hover:bg-teal-400 ${focusRing}`}
            >
              {busyKind === 'approve' ? 'Sending…' : 'Send drone'}
            </button>
            <button
              type="button"
              disabled={!canDecide}
              onClick={onReject}
              className={`cursor-pointer rounded-xl bg-slate-900/5 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-900/10 disabled:cursor-not-allowed disabled:opacity-45 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10 ${focusRing}`}
            >
              {busyKind === 'reject' ? 'Dismissing…' : 'Dismiss'}
            </button>
          </div>
        </>
      ) : (
        <div className="mb-10 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
          <p className="m-0 font-medium text-slate-700 dark:text-slate-200">
            No case selected
          </p>
          <p className="mt-1.5 mb-0">
            Pick a case from the list, or run{' '}
            <code className="font-mono text-[0.8rem]">make sim</code> to open
            one from a speed collapse.
          </p>
        </div>
      )}

      <div className="border-t border-slate-900/5 pt-6 dark:border-white/5">
        <h2 className="mb-4 text-sm font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
          Last speeds
        </h2>
        {speedsLoading && speeds.length === 0 ? (
          <div className="space-y-2" aria-hidden="true">
            {[0, 1, 2].map((key) => (
              <div
                key={key}
                className="h-8 animate-pulse rounded bg-slate-900/5 dark:bg-white/5"
              />
            ))}
          </div>
        ) : speeds.length === 0 ? (
          <div className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
            <p className="m-0 font-medium text-slate-700 dark:text-slate-200">
              No speed samples yet
            </p>
            <p className="mt-1.5 mb-0">
              The live tape appears after{' '}
              <code className="font-mono text-[0.8rem]">make sim</code> posts
              events on segment A.
            </p>
          </div>
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
                {speeds.map((row) => {
                  const collapse = isCollapseSpeed(row.speed)
                  const newest = row.event_id === newestCollapseId
                  return (
                    <tr
                      key={row.event_id}
                      className={`border-t border-slate-900/5 dark:border-white/5 ${
                        newest
                          ? 'bg-rose-500/10 text-rose-900 dark:text-rose-100'
                          : collapse
                            ? 'bg-rose-500/5 text-slate-700 dark:text-slate-200'
                            : 'text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <td className="py-2.5 pr-4 align-top">{row.event_id}</td>
                      <td className="py-2.5 pr-4 align-top">{row.segment}</td>
                      <td className="py-2.5 pr-4 align-top tabular-nums">
                        {row.speed}
                        {newest ? (
                          <span className="ml-2 font-sans text-[0.65rem] tracking-wide text-rose-700 uppercase dark:text-rose-300">
                            collapse
                          </span>
                        ) : null}
                      </td>
                      <td
                        className="py-2.5 align-top font-sans text-xs text-slate-500 dark:text-slate-400"
                        title={row.recorded_at}
                      >
                        {formatRelativeTime(row.recorded_at, nowMs)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
