import type { Meta, StoryObj } from '@storybook/react-vite'
import { fn } from 'storybook/test'
import { Button } from './Button'

const meta = {
  title: 'shared/Button',
  component: Button,
  args: {
    children: 'Send drone',
    variant: 'primary',
    disabled: false,
    busy: false,
    onClick: fn(),
  },
  argTypes: {
    variant: {
      control: 'inline-radio',
      options: ['primary', 'ghost', 'danger'],
    },
  },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

export const Primary: Story = {}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Dismiss',
  },
}

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Reject',
  },
}

export const Busy: Story = {
  args: {
    busy: true,
    children: 'Sending…',
  },
}

export const Disabled: Story = {
  args: {
    disabled: true,
  },
}

export const Pair: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      <Button variant="primary">Send drone</Button>
      <Button variant="ghost">Dismiss</Button>
    </div>
  ),
}
