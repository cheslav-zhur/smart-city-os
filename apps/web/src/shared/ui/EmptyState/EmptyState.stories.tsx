import type { Meta, StoryObj } from '@storybook/react-vite'
import { EmptyState, SimCommand } from './EmptyState'

const meta = {
  title: 'shared/EmptyState',
  component: EmptyState,
  args: {
    title: 'No cases yet',
    children: (
      <>
        Run <SimCommand /> to send the speed tape and open a collapse case.
      </>
    ),
  },
} satisfies Meta<typeof EmptyState>

export default meta
type Story = StoryObj<typeof meta>

export const NoCases: Story = {}

export const NoCaseSelected: Story = {
  args: {
    title: 'No case selected',
    children: (
      <>
        Pick a case from the list, or run <SimCommand /> to open one from a
        speed collapse.
      </>
    ),
  },
}

export const NoSpeedSamples: Story = {
  args: {
    title: 'No speed samples yet',
    children: (
      <>
        The live tape appears after <SimCommand /> posts events on segment A.
      </>
    ),
  },
}
