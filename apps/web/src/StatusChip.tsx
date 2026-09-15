type StatusChipProps = {
  status: string
  size?: 'sm' | 'md'
}

const tones: Record<string, string> = {
  open: 'bg-teal-500/15 text-teal-800 dark:text-teal-200',
  approved: 'bg-slate-900/8 text-slate-700 dark:bg-white/10 dark:text-slate-200',
  rejected: 'bg-slate-900/5 text-slate-500 dark:bg-white/5 dark:text-slate-400',
}

export function StatusChip({ status, size = 'md' }: StatusChipProps) {
  const tone = tones[status] ?? tones.rejected
  const sizing =
    size === 'sm' ? 'px-2 py-0.5 text-[0.7rem]' : 'px-2.5 py-0.5 text-xs'

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium tracking-wide ${sizing} ${tone}`}
    >
      {status}
    </span>
  )
}
