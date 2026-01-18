import { useState } from 'react'
import { useLogin } from '@refinedev/core'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { mutate: login, isLoading } = useLogin()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    login({ email, password })
  }

  return (
    <div className="min-h-screen flex login-bg">
      {/* Left side - Large Logo and branding */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 marqed-gradient opacity-95" />

        {/* Circuit pattern overlay */}
        <div className="absolute inset-0 marqed-circuit-lines opacity-20" />

        {/* Decorative nodes */}
        <div className="absolute top-20 left-20">
          <div className="marqed-node animate-pulse-subtle" />
        </div>
        <div className="absolute top-40 left-40">
          <div className="marqed-node-orange animate-pulse-subtle" style={{ animationDelay: '0.5s' }} />
        </div>
        <div className="absolute bottom-32 right-32">
          <div className="marqed-node animate-pulse-subtle" style={{ animationDelay: '1s' }} />
        </div>
        <div className="absolute top-1/4 right-20">
          <div className="marqed-node-orange animate-pulse-subtle" style={{ animationDelay: '1.5s' }} />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-12">
          {/* Large Logo */}
          <div className="logo-glow animate-float mb-8">
            <img
              src="/marqed-logo.svg"
              alt="arQed.ai"
              className="w-full max-w-md h-auto"
              style={{
                filter: 'brightness(0) invert(1)',
                maxHeight: '120px',
                objectFit: 'contain'
              }}
            />
          </div>

          {/* Tagline */}
          <div className="text-center text-white mt-8">
            <p className="text-2xl font-light tracking-wide opacity-90">
              Innovate. Lead. Succeed.
            </p>
            <p className="text-lg mt-4 opacity-75 max-w-md">
              Het platform voor (legacy-)software onderhoud, (legacy-)migratie, en software kwaliteitsanalyse
            </p>
          </div>

          {/* Feature highlights */}
          <div className="mt-12 grid grid-cols-3 gap-8 text-white/80 text-center max-w-lg">
            <div>
              <div className="text-3xl font-bold text-white">5+</div>
              <div className="text-sm mt-1">Projecten</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">5M</div>
              <div className="text-sm mt-1">Regels code</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">99,9%</div>
              <div className="text-sm mt-1">Uptime</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="w-full lg:w-1/2 xl:w-2/5 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden mb-8 text-center">
            <img
              src="/marqed-logo.svg"
              alt="arQed.ai"
              className="h-16 w-auto mx-auto logo-glow"
            />
          </div>

          <Card className="border-0 shadow-xl shadow-marqed-blue/5">
            <CardHeader className="space-y-1 text-center pb-2">
              <CardTitle className="text-2xl font-bold marqed-headline">
                Client Portal
              </CardTitle>
              <CardDescription className="text-base">
                Log in om toegang te krijgen tot uw projecten
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">
                    E-mailadres
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="u@voorbeeld.nl"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className="h-11 focus-marqed"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-sm font-medium">
                      Wachtwoord
                    </Label>
                    <a
                      href="#"
                      className="text-xs text-marqed-blue hover:text-marqed-blue-dark hover:underline"
                    >
                      Wachtwoord vergeten?
                    </a>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Uw wachtwoord"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="h-11 focus-marqed"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full h-11 btn-marqed text-base"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Bezig met inloggen...
                    </>
                  ) : (
                    'Inloggen'
                  )}
                </Button>
              </form>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">
                    Of
                  </span>
                </div>
              </div>

              {/* SSO option placeholder */}
              <Button
                type="button"
                variant="outline"
                className="w-full h-11"
                disabled
              >
                <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"
                  />
                </svg>
                Inloggen met SSO (binnenkort)
              </Button>

              <div className="mt-6 text-center text-sm text-muted-foreground">
                <p>
                  Hulp nodig?{' '}
                  <a
                    href="mailto:support@marqed.ai"
                    className="text-marqed-orange hover:text-marqed-orange-dark font-medium hover:underline"
                  >
                    Neem contact op
                  </a>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="mt-8 text-center text-xs text-muted-foreground">
            <p>
              &copy; {new Date().getFullYear()} MarQed.ai - Alle rechten voorbehouden
            </p>
            <p className="mt-1">
              <a href="#" className="hover:text-marqed-blue">Privacybeleid</a>
              {' · '}
              <a href="#" className="hover:text-marqed-blue">Gebruiksvoorwaarden</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
