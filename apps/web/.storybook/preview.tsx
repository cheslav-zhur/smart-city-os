import type { Decorator, Preview } from '@storybook/react-vite'
import { applyTheme, DEFAULT_THEME, type DeskTheme } from '../src/shared/theme'
import '../src/index.css'

const withDeskTheme: Decorator = (Story, context) => {
  const theme = (context.globals.theme as DeskTheme | undefined) ?? DEFAULT_THEME
  applyTheme(theme)
  return (
    <div className="min-h-[100vh] bg-[#f4f6f8] p-8 font-sans text-slate-800 dark:bg-[#0b1220] dark:text-slate-100">
      <Story />
    </div>
  )
}

const preview: Preview = {
  globalTypes: {
    theme: {
      description: 'Desk color scheme',
      toolbar: {
        title: 'Theme',
        icon: 'mirror',
        items: [
          { value: 'dark', title: 'Dark' },
          { value: 'light', title: 'Light' },
        ],
        dynamicTitle: true,
      },
    },
  },
  initialGlobals: {
    theme: DEFAULT_THEME,
  },
  decorators: [withDeskTheme],
  parameters: {
    layout: 'fullscreen',
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      test: 'todo',
    },
  },
}

export default preview
