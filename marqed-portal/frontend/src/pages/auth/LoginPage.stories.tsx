import type { Meta, StoryObj } from '@storybook/react'
import { LoginPage } from './LoginPage'
import { BrowserRouter } from 'react-router-dom'
import { Refine } from '@refinedev/core'

const meta: Meta<typeof LoginPage> = {
  title: 'Pages/Auth/LoginPage',
  component: LoginPage,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => (
      <BrowserRouter>
        <Refine
          options={{ disableTelemetry: true }}
          authProvider={{
            login: async () => ({ success: true }),
            logout: async () => ({ success: true }),
            check: async () => ({ authenticated: false }),
            onError: async (error) => ({ error }),
          }}
        >
          <Story />
        </Refine>
      </BrowserRouter>
    ),
  ],
}

export default meta
type Story = StoryObj<typeof LoginPage>

export const Default: Story = {}

export const Mobile: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'mobile',
    },
  },
}

export const Tablet: Story = {
  parameters: {
    viewport: {
      defaultViewport: 'tablet',
    },
  },
}

export const DarkBackground: Story = {
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
