import type { Meta, StoryObj } from '@storybook/react-vite'
import { Panel } from './Panel'

const meta = {
  title: 'shared/Panel',
  component: Panel,
  args: {
    padding: 'md',
    children: 'Panel surface used by the case list and card.',
  },
  argTypes: {
    as: {
      control: 'inline-radio',
      options: ['div', 'section', 'aside'],
    },
    padding: {
      control: 'inline-radio',
      options: ['md', 'lg'],
    },
  },
} satisfies Meta<typeof Panel>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const LargePadding: Story = {
  args: {
    as: 'section',
    padding: 'lg',
    children: (
      <>
        <p className="m-0 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
          Send a drone to look
        </p>
        <p className="mt-2 mb-0 max-w-xl text-[0.95rem] leading-relaxed text-slate-600 dark:text-slate-300">
          Rule proposal is ready. Confirm to dispatch, or dismiss.
        </p>
      </>
    ),
  },
}

export const Aside: Story = {
  args: {
    as: 'aside',
    padding: 'md',
    children: (
      <>
        <h2 className="mb-4 text-sm font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
          Cases
        </h2>
        <p className="m-0 text-sm text-slate-600 dark:text-slate-300">
          List goes here.
        </p>
      </>
    ),
  },
}
