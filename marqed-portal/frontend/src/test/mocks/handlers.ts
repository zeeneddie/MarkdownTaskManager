import { http, HttpResponse } from 'msw'

// Mock user data
const mockUsers = [
  {
    id: '1',
    email: 'admin@hci.nl',
    full_name: 'Admin User',
    role: 'ADMIN',
    tenant_id: 'hci',
  },
]

// Login attempt tracking for lockout functionality
const loginAttempts: Map<string, { count: number; lockedUntil: number | null }> = new Map()
const MAX_LOGIN_ATTEMPTS = 3
const LOCKOUT_DURATION_MS = 3 * 60 * 1000 // 3 minutes

function getLoginAttemptState(email: string) {
  if (!loginAttempts.has(email)) {
    loginAttempts.set(email, { count: 0, lockedUntil: null })
  }
  return loginAttempts.get(email)!
}

function recordFailedAttempt(email: string): { isLocked: boolean; remainingTime: number } {
  const state = getLoginAttemptState(email)

  // Check if currently locked
  if (state.lockedUntil && Date.now() < state.lockedUntil) {
    const remainingTime = Math.ceil((state.lockedUntil - Date.now()) / 1000)
    return { isLocked: true, remainingTime }
  }

  // Reset if lock expired
  if (state.lockedUntil && Date.now() >= state.lockedUntil) {
    state.count = 0
    state.lockedUntil = null
  }

  // Increment attempt count
  state.count++

  // Lock if max attempts reached
  if (state.count >= MAX_LOGIN_ATTEMPTS) {
    state.lockedUntil = Date.now() + LOCKOUT_DURATION_MS
    return { isLocked: true, remainingTime: LOCKOUT_DURATION_MS / 1000 }
  }

  return { isLocked: false, remainingTime: 0 }
}

function resetLoginAttempts(email: string) {
  loginAttempts.delete(email)
}

// Export for tests to reset state
export function clearAllLoginAttempts() {
  loginAttempts.clear()
}

function isAccountLocked(email: string): { locked: boolean; remainingTime: number } {
  const state = getLoginAttemptState(email)
  if (state.lockedUntil && Date.now() < state.lockedUntil) {
    const remainingTime = Math.ceil((state.lockedUntil - Date.now()) / 1000)
    return { locked: true, remainingTime }
  }
  return { locked: false, remainingTime: 0 }
}

// Mock projects data
const mockProjects = [
  {
    id: '1',
    name: 'HCI Legacy Migration',
    description: 'Migrating legacy COBOL systems',
    status: 'active',
    tenant_id: 'hci',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T14:30:00Z',
  },
]

// Mock tokens
const mockTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
}

export const handlers = [
  // Auth endpoints
  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json() as { email: string; password: string }

    // Check if account is locked
    const lockStatus = isAccountLocked(body.email)
    if (lockStatus.locked) {
      return HttpResponse.json(
        {
          error: 'Account geblokkeerd',
          message: `Te veel mislukte inlogpogingen. Probeer opnieuw over ${Math.ceil(lockStatus.remainingTime / 60)} minuten.`,
          remaining_seconds: lockStatus.remainingTime,
        },
        { status: 423 } // Locked status code
      )
    }

    // Check credentials
    if (body.email === 'admin@hci.nl' && body.password === 'password123') {
      // Reset attempts on successful login
      resetLoginAttempts(body.email)
      return HttpResponse.json({
        ...mockTokens,
        user: mockUsers[0],
      })
    }

    // Record failed attempt
    const attemptResult = recordFailedAttempt(body.email)
    const attemptsRemaining = MAX_LOGIN_ATTEMPTS - getLoginAttemptState(body.email).count

    if (attemptResult.isLocked) {
      return HttpResponse.json(
        {
          error: 'Account geblokkeerd',
          message: `Te veel mislukte inlogpogingen. Probeer opnieuw over 3 minuten.`,
          remaining_seconds: attemptResult.remainingTime,
        },
        { status: 423 }
      )
    }

    return HttpResponse.json(
      {
        error: 'Ongeldige inloggegevens',
        message: `E-mailadres of wachtwoord is onjuist. Nog ${attemptsRemaining} ${attemptsRemaining === 1 ? 'poging' : 'pogingen'} over.`,
        attempts_remaining: attemptsRemaining,
      },
      { status: 401 }
    )
  }),

  http.post('/api/auth/refresh', () => {
    return HttpResponse.json(mockTokens)
  }),

  http.get('/api/auth/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (authHeader?.includes('mock-access-token')) {
      return HttpResponse.json(mockUsers[0])
    }
    return new HttpResponse(null, { status: 401 })
  }),

  http.post('/api/auth/logout', () => {
    return HttpResponse.json({ message: 'Logged out successfully' })
  }),

  // Projects endpoints
  http.get('/api/projects', () => {
    return HttpResponse.json({
      data: mockProjects,
      total: mockProjects.length,
      page: 1,
      pageSize: 10,
    })
  }),

  http.get('/api/projects/:id', ({ params }) => {
    const project = mockProjects.find((p) => p.id === params.id)
    if (project) {
      return HttpResponse.json(project)
    }
    return new HttpResponse(null, { status: 404 })
  }),

  http.post('/api/projects', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    const newProject = {
      id: String(mockProjects.length + 1),
      ...body,
      tenant_id: 'hci',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    return HttpResponse.json(newProject, { status: 201 })
  }),

  // Health check
  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'healthy' })
  }),
]
