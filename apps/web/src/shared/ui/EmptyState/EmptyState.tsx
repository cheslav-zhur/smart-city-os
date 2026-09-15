import type { HTMLAttributes, ReactNode } from 'react'

type EmptyStateProps = HTMLAttributes<HTMLDivElement> & {
  title: string
  children: ReactNode
}

/** Title + hint block used for empty list/card/tape states. */
export function EmptyState({
  title,
  children,
  className = '',
  ...rest
}: EmptyStateProps) {
  return (
    <div
      className={`text-sm leading-relaxed text-slate-500 dark:text-slate-400 ${className}`.trim()}
      {...rest}
    >
      <p className="m-0 font-medium text-slate-700 dark:text-slate-200">{title}</p>
      <p className="mt-1.5 mb-0">{children}</p>
    </div>
  )
}

/** Mono chip for the local simulator command in empty hints. */
export function SimCommand() {
  return <code className="font-mono text-[0.8rem]">make sim</code>
}
