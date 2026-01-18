import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { LoginPage } from './LoginPage'

// Mock useLogin hook
vi.mock('@refinedev/core', async () => {
  const actual = await vi.importActual('@refinedev/core')
  return {
    ...actual,
    useLogin: () => ({
      mutate: vi.fn(),
      isLoading: false,
    }),
  }
})

describe('LoginPage', () => {
  it('renders login form', () => {
    render(<LoginPage />)

    expect(screen.getByText('Welkom bij MarQed.ai')).toBeInTheDocument()
    expect(screen.getByLabelText('E-mailadres')).toBeInTheDocument()
    expect(screen.getByLabelText('Wachtwoord')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Inloggen' })).toBeInTheDocument()
  })

  it('shows MarQed logo', () => {
    render(<LoginPage />)
    expect(screen.getByText('M')).toBeInTheDocument()
  })

  it('allows entering email and password', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText('E-mailadres')
    const passwordInput = screen.getByLabelText('Wachtwoord')

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    expect(emailInput).toHaveValue('test@example.com')
    expect(passwordInput).toHaveValue('password123')
  })

  it('shows support contact link', () => {
    render(<LoginPage />)

    const supportLink = screen.getByText('Neem contact op')
    expect(supportLink).toHaveAttribute('href', 'mailto:support@marqed.ai')
  })

  it('has correct input types', () => {
    render(<LoginPage />)

    expect(screen.getByLabelText('E-mailadres')).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText('Wachtwoord')).toHaveAttribute('type', 'password')
  })

  it('has autocomplete attributes for accessibility', () => {
    render(<LoginPage />)

    expect(screen.getByLabelText('E-mailadres')).toHaveAttribute(
      'autocomplete',
      'email'
    )
    expect(screen.getByLabelText('Wachtwoord')).toHaveAttribute(
      'autocomplete',
      'current-password'
    )
  })
})
