import type { ElementType, HTMLAttributes } from 'react'

const surface =
  'rounded-2xl bg-white/80 shadow-[0_1px_0_rgba(15,23,42,0.04)] dark:bg-white/[0.03] dark:shadow-none dark:ring-1 dark:ring-white/[0.06]'

const paddings = {
  md: 'p-5',
  lg: 'p-7',
} as const

export type PanelPadding = keyof typeof paddings

type PanelProps = HTMLAttributes<HTMLElement> & {
  as?: 'section' | 'aside' | 'div'
  padding?: PanelPadding
}

export function Panel({
  as: Tag = 'div',
  padding = 'md',
  className = '',
  children,
  ...rest
}: PanelProps) {
  const Component = Tag as ElementType
  return (
    <Component
      className={`${surface} ${paddings[padding]} ${className}`.trim()}
      {...rest}
    >
      {children}
    </Component>
  )
}
