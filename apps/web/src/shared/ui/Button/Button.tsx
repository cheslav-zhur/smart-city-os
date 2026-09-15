import type { ButtonHTMLAttributes } from 'react'

const focusRing =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f4f6f8] dark:focus-visible:ring-offset-[#0b1220]'

const variants = {
  primary:
    'bg-teal-600 text-white hover:bg-teal-500 dark:bg-teal-500 dark:text-slate-950 dark:hover:bg-teal-400',
  ghost:
    'bg-slate-900/5 text-slate-700 hover:bg-slate-900/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10',
  danger:
    'bg-rose-600 text-white hover:bg-rose-500 dark:bg-rose-500 dark:text-slate-950 dark:hover:bg-rose-400',
} as const

export type ButtonVariant = keyof typeof variants

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  busy?: boolean
}

export function Button({
  variant = 'primary',
  busy = false,
  disabled,
  className = '',
  type = 'button',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={`cursor-pointer rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-45 ${variants[variant]} ${focusRing} ${className}`.trim()}
      {...rest}
    >
      {children}
    </button>
  )
}
