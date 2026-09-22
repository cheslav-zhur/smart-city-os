import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import { CASE_OUTDATED, CASE_REJECTED } from './domain'
import { StatusChip } from './StatusChip'

test('outdated chip is not the rejected tone class', () => {
  render(
    <div>
      <StatusChip status={CASE_OUTDATED} />
      <StatusChip status={CASE_REJECTED} />
    </div>,
  )

  expect(screen.getByText(CASE_OUTDATED).className).not.toEqual(
    screen.getByText(CASE_REJECTED).className,
  )
})
