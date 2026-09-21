import { useEffect, useState } from 'react'
import type { AuditListItem } from '../../../api/generated/models/auditListItem'
import type { CaseListItem } from '../../../api/generated/models/caseListItem'
import type { EventTapeItem } from '../../../api/generated/models/eventTapeItem'
import { formatRelativeTime, isCollapseSpeed } from '../../../shared/lib/time'
import { Button, EmptyState, Panel, SimCommand } from '../../../shared/ui'
import type { DecideKind } from '../decide'
import { CASE_OPEN, EMPTY_OPINIONS_COPY, formatDroneStatus } from '../domain'
import { StatusChip } from '../StatusChip'

type CaseCardProps = {
  caseRow: CaseListItem | null
  speeds: EventTapeItem[]
  audit: AuditListItem[]
  busy: boolean
  busyKind: DecideKind | null
  casesLoading?: boolean
  speedsLoading?: boolean
  auditLoading?: boolean
  /** True when the audit GET failed — do not show the empty-ledger copy. */
  auditError?: boolean
  onApprove: () => void
  onReject: () => void
}

export function CaseCard({
  caseRow,
  speeds,
  audit,
  busy,
  busyKind,
  casesLoading = false,
  speedsLoading = false,
  auditLoading = false,
  auditError = false,
  onApprove,
  onReject,
}: CaseCardProps) {
  const [nowMs, setNowMs] = useState(() => Date.now())
  const canDecide = caseRow !== null && caseRow.status === CASE_OPEN && !busy

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

  const bothOpinionsEmpty =
    caseRow !== null &&
    caseRow.dispatcher_opinion == null &&
    caseRow.critic_opinion == null

  return (
    <Panel as="section" padding="lg">
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
              {caseRow.trigger_kind ? ` · ${caseRow.trigger_kind}` : ''}
            </span>
            <StatusChip status={caseRow.status} />
            <span className="rounded-full bg-slate-900/5 px-2.5 py-0.5 text-xs text-slate-600 dark:bg-white/5 dark:text-slate-300">
              drone {formatDroneStatus(caseRow.drone_status)}
            </span>
          </div>

          <p className="mb-2 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
            Send a drone to look
          </p>

          {bothOpinionsEmpty ? (
            <p className="mb-6 max-w-2xl text-[0.95rem] leading-relaxed text-slate-500 dark:text-slate-400">
              {EMPTY_OPINIONS_COPY}
            </p>
          ) : (
            <div className="mb-6 grid max-w-2xl gap-4">
              <OpinionBlock
                label="Dispatcher"
                text={caseRow.dispatcher_opinion}
              />
              <OpinionBlock label="Critic" text={caseRow.critic_opinion} />
            </div>
          )}

          <div className="mb-10 flex flex-wrap gap-3">
            <Button
              variant="primary"
              disabled={!canDecide}
              busy={busyKind === 'approve'}
              onClick={onApprove}
            >
              {busyKind === 'approve' ? 'Sending…' : 'Send drone'}
            </Button>
            <Button
              variant="ghost"
              disabled={!canDecide}
              busy={busyKind === 'reject'}
              onClick={onReject}
            >
              {busyKind === 'reject' ? 'Dismissing…' : 'Dismiss'}
            </Button>
          </div>
        </>
      ) : (
        <EmptyState title="No case selected" className="mb-10">
          Pick a case from the list, or run <SimCommand /> to open one from a
          speed collapse.
        </EmptyState>
      )}

      {caseRow !== null ? (
        <div className="mb-10 border-t border-slate-900/5 pt-6 dark:border-white/5">
          <h2 className="mb-4 text-sm font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
            Audit
          </h2>
          {auditError ? (
            <EmptyState title="Could not load audit">
              Retry will follow the next poll, or pick the case again.
            </EmptyState>
          ) : auditLoading && audit.length === 0 ? (
            <div className="space-y-2" aria-hidden="true">
              {[0, 1].map((key) => (
                <div
                  key={key}
                  className="h-8 animate-pulse rounded bg-slate-900/5 dark:bg-white/5"
                />
              ))}
            </div>
          ) : audit.length === 0 ? (
            <EmptyState title="No audit rows yet">
              Model and operator actions appear here after the worker or a
              decision.
            </EmptyState>
          ) : (
            <ul className="m-0 list-none space-y-3 p-0">
              {audit.map((row) => (
                <li
                  key={row.id}
                  className="border-t border-slate-900/5 pt-3 text-sm first:border-t-0 first:pt-0 dark:border-white/5"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="font-medium text-slate-800 dark:text-slate-100">
                      {row.actor} · {row.action}
                    </span>
                    <span
                      className="text-xs text-slate-500 dark:text-slate-400"
                      title={row.created_at}
                    >
                      {formatRelativeTime(row.created_at, nowMs)}
                    </span>
                  </div>
                  {row.why ? (
                    <p className="mt-1 m-0 text-slate-600 dark:text-slate-300">
                      {row.why}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

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
          <EmptyState title="No speed samples yet">
            The live tape appears after <SimCommand /> posts events on segment
            A.
          </EmptyState>
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
    </Panel>
  )
}

function OpinionBlock({
  label,
  text,
}: {
  label: string
  text: string | null
}) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
        {label}
      </h3>
      <p className="m-0 text-[0.95rem] leading-relaxed text-slate-600 dark:text-slate-300">
        {text ?? '—'}
      </p>
    </div>
  )
}
