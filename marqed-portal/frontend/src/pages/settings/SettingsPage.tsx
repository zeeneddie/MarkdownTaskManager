import { useState } from 'react'
import { useGetIdentity } from '@refinedev/core'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Settings,
  User,
  Bell,
  Building2,
  Key,
  Shield,
  Palette,
  Globe,
  Mail,
  Smartphone,
  Lock,
  Eye,
  EyeOff,
  Save,
  RefreshCw,
  Copy,
  Check,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface UserIdentity {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string
}

// Mock API keys for demonstration
const mockApiKeys = [
  { id: '1', name: 'Production API Key', key: 'mk_live_****************************a1b2', created: '2026-01-10', lastUsed: '2026-01-15' },
  { id: '2', name: 'Development API Key', key: 'mk_test_****************************c3d4', created: '2025-12-15', lastUsed: '2026-01-14' },
]

// Mock team members
const mockTeamMembers = [
  { id: '1', name: 'Jan de Vries', email: 'jan@example.com', role: 'Admin', avatar: 'J' },
  { id: '2', name: 'Maria Jansen', email: 'maria@example.com', role: 'Developer', avatar: 'M' },
  { id: '3', name: 'Peter Bakker', email: 'peter@example.com', role: 'Viewer', avatar: 'P' },
]

function SettingRow({
  label,
  description,
  children
}: {
  label: string
  description?: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between py-4 border-b last:border-0">
      <div className="space-y-0.5">
        <Label className="text-base">{label}</Label>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      <div>{children}</div>
    </div>
  )
}

export function SettingsPage() {
  const { data: user } = useGetIdentity<UserIdentity>()
  const [activeTab, setActiveTab] = useState('profile')
  const [showPassword, setShowPassword] = useState(false)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Form states
  const [profileForm, setProfileForm] = useState({
    fullName: user?.full_name || '',
    email: user?.email || '',
    phone: '+31 6 12345678',
    language: 'nl',
  })

  const [notifications, setNotifications] = useState({
    emailAnalysis: true,
    emailReports: true,
    emailSecurity: true,
    pushAnalysis: false,
    pushReports: true,
    weeklyDigest: true,
  })

  const [security, setSecurity] = useState({
    twoFactor: false,
    sessionTimeout: '30',
  })

  const handleCopyKey = (key: string, id: string) => {
    navigator.clipboard.writeText(key)
    setCopiedKey(id)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-marqed-blue-dark via-marqed-blue to-marqed-blue-medium p-6 text-white">
        <div className="absolute inset-0 marqed-circuit-lines opacity-10" />
        <div className="relative z-10">
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Settings className="h-7 w-7" />
            Instellingen
          </h1>
          <p className="text-white/80 mt-1">
            Beheer uw account, notificaties en organisatie-instellingen
          </p>
        </div>
        <div className="absolute top-4 right-4 w-20 h-20 rounded-full bg-marqed-orange/20 blur-2xl" />
      </div>

      {/* Settings Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-muted/50 p-1 h-auto flex-wrap">
          <TabsTrigger value="profile" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <User className="h-4 w-4 mr-2" />
            Profiel
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <Bell className="h-4 w-4 mr-2" />
            Notificaties
          </TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <Shield className="h-4 w-4 mr-2" />
            Beveiliging
          </TabsTrigger>
          <TabsTrigger value="organization" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <Building2 className="h-4 w-4 mr-2" />
            Organisatie
          </TabsTrigger>
          <TabsTrigger value="api" className="data-[state=active]:bg-marqed-blue data-[state=active]:text-white">
            <Key className="h-4 w-4 mr-2" />
            API Toegang
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Profile Info */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Persoonlijke Informatie</CardTitle>
                <CardDescription>
                  Beheer uw persoonlijke gegevens en contactinformatie
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center gap-6">
                  <div className="h-20 w-20 rounded-full bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">
                      {user?.full_name?.charAt(0) || 'U'}
                    </span>
                  </div>
                  <div>
                    <Button variant="outline" size="sm">
                      Foto wijzigen
                    </Button>
                    <p className="text-xs text-muted-foreground mt-2">
                      JPG, PNG of GIF. Max 2MB.
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="fullName">Volledige naam</Label>
                    <Input
                      id="fullName"
                      value={profileForm.fullName}
                      onChange={(e) => setProfileForm({ ...profileForm, fullName: e.target.value })}
                      className="focus-marqed"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">E-mailadres</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      className="focus-marqed"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Telefoonnummer</Label>
                    <Input
                      id="phone"
                      value={profileForm.phone}
                      onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                      className="focus-marqed"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="language">Taal</Label>
                    <select
                      id="language"
                      value={profileForm.language}
                      onChange={(e) => setProfileForm({ ...profileForm, language: e.target.value })}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm focus-marqed"
                    >
                      <option value="nl">Nederlands</option>
                      <option value="en">English</option>
                      <option value="de">Deutsch</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                    <Save className="h-4 w-4 mr-2" />
                    Wijzigingen opslaan
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Account Info */}
            <Card>
              <CardHeader>
                <CardTitle>Account Info</CardTitle>
                <CardDescription>
                  Uw account details
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-sm text-muted-foreground">Rol</p>
                  <p className="font-medium capitalize">{user?.role || 'User'}</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-sm text-muted-foreground">Organisatie</p>
                  <p className="font-medium uppercase">{user?.tenant_id || '-'}</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-sm text-muted-foreground">Account ID</p>
                  <p className="font-mono text-sm">{user?.id || '-'}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-marqed-blue" />
                  E-mail Notificaties
                </CardTitle>
                <CardDescription>
                  Kies welke e-mails u wilt ontvangen
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SettingRow
                  label="Analyse updates"
                  description="Ontvang e-mail wanneer een analyse is voltooid"
                >
                  <Switch
                    checked={notifications.emailAnalysis}
                    onCheckedChange={(checked) => setNotifications({ ...notifications, emailAnalysis: checked })}
                  />
                </SettingRow>
                <SettingRow
                  label="Rapporten"
                  description="Ontvang e-mail wanneer een rapport beschikbaar is"
                >
                  <Switch
                    checked={notifications.emailReports}
                    onCheckedChange={(checked) => setNotifications({ ...notifications, emailReports: checked })}
                  />
                </SettingRow>
                <SettingRow
                  label="Beveiligingswaarschuwingen"
                  description="Ontvang e-mail bij nieuwe kwetsbaarheden"
                >
                  <Switch
                    checked={notifications.emailSecurity}
                    onCheckedChange={(checked) => setNotifications({ ...notifications, emailSecurity: checked })}
                  />
                </SettingRow>
                <SettingRow
                  label="Wekelijkse samenvatting"
                  description="Ontvang een wekelijks overzicht van alle projecten"
                >
                  <Switch
                    checked={notifications.weeklyDigest}
                    onCheckedChange={(checked) => setNotifications({ ...notifications, weeklyDigest: checked })}
                  />
                </SettingRow>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Smartphone className="h-5 w-5 text-marqed-orange" />
                  Push Notificaties
                </CardTitle>
                <CardDescription>
                  Browser push notificaties
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SettingRow
                  label="Analyse updates"
                  description="Push notificatie bij voltooide analyse"
                >
                  <Switch
                    checked={notifications.pushAnalysis}
                    onCheckedChange={(checked) => setNotifications({ ...notifications, pushAnalysis: checked })}
                  />
                </SettingRow>
                <SettingRow
                  label="Rapporten"
                  description="Push notificatie bij nieuwe rapporten"
                >
                  <Switch
                    checked={notifications.pushReports}
                    onCheckedChange={(checked) => setNotifications({ ...notifications, pushReports: checked })}
                  />
                </SettingRow>

                <div className="mt-6 p-4 rounded-lg bg-marqed-blue/5 border border-marqed-blue/20">
                  <div className="flex items-start gap-3">
                    <Bell className="h-5 w-5 text-marqed-blue mt-0.5" />
                    <div>
                      <p className="font-medium">Push notificaties inschakelen</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Sta browser notificaties toe om push berichten te ontvangen.
                      </p>
                      <Button variant="outline" size="sm" className="mt-3">
                        Notificaties toestaan
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="h-5 w-5 text-marqed-blue" />
                  Wachtwoord wijzigen
                </CardTitle>
                <CardDescription>
                  Wijzig uw wachtwoord regelmatig voor extra veiligheid
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Huidig wachtwoord</Label>
                  <div className="relative">
                    <Input
                      id="currentPassword"
                      type={showPassword ? 'text' : 'password'}
                      className="focus-marqed pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="newPassword">Nieuw wachtwoord</Label>
                  <Input
                    id="newPassword"
                    type="password"
                    className="focus-marqed"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Bevestig wachtwoord</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    className="focus-marqed"
                  />
                </div>
                <Button className="w-full bg-marqed-blue hover:bg-marqed-blue-dark">
                  Wachtwoord wijzigen
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-marqed-orange" />
                  Beveiligingsopties
                </CardTitle>
                <CardDescription>
                  Extra beveiligingsmaatregelen voor uw account
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SettingRow
                  label="Twee-factor authenticatie"
                  description="Extra beveiliging met een authenticator app"
                >
                  <Switch
                    checked={security.twoFactor}
                    onCheckedChange={(checked) => setSecurity({ ...security, twoFactor: checked })}
                  />
                </SettingRow>

                <div className="py-4 border-b">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="text-base">Sessie timeout</Label>
                      <p className="text-sm text-muted-foreground">
                        Automatisch uitloggen na inactiviteit
                      </p>
                    </div>
                    <select
                      value={security.sessionTimeout}
                      onChange={(e) => setSecurity({ ...security, sessionTimeout: e.target.value })}
                      className="h-9 px-3 rounded-md border border-input bg-background text-sm"
                    >
                      <option value="15">15 minuten</option>
                      <option value="30">30 minuten</option>
                      <option value="60">1 uur</option>
                      <option value="120">2 uur</option>
                    </select>
                  </div>
                </div>

                <div className="mt-6 p-4 rounded-lg bg-red-50 border border-red-200">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-800">Actieve sessies</p>
                      <p className="text-sm text-red-600 mt-1">
                        U bent ingelogd op 2 apparaten.
                      </p>
                      <Button variant="outline" size="sm" className="mt-3 border-red-300 text-red-700 hover:bg-red-100">
                        Alle sessies beëindigen
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Organization Tab */}
        <TabsContent value="organization" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-marqed-blue" />
                  Organisatie Details
                </CardTitle>
                <CardDescription>
                  Beheer uw organisatie-instellingen
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="orgName">Organisatienaam</Label>
                    <Input
                      id="orgName"
                      defaultValue="Acme Corporation"
                      className="focus-marqed"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="orgId">Organisatie ID</Label>
                    <Input
                      id="orgId"
                      value={user?.tenant_id?.toUpperCase() || 'ACME'}
                      disabled
                      className="bg-muted"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="orgEmail">Contact e-mail</Label>
                    <Input
                      id="orgEmail"
                      type="email"
                      defaultValue="admin@acme.com"
                      className="focus-marqed"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="orgWebsite">Website</Label>
                    <Input
                      id="orgWebsite"
                      defaultValue="https://acme.com"
                      className="focus-marqed"
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                    <Save className="h-4 w-4 mr-2" />
                    Wijzigingen opslaan
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Abonnement</CardTitle>
                <CardDescription>
                  Uw huidige plan
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-lg bg-gradient-to-br from-marqed-blue/10 to-marqed-blue/5 border border-marqed-blue/20">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-marqed-blue">Professional</span>
                    <span className="px-2 py-0.5 bg-marqed-blue text-white text-xs rounded-full">Actief</span>
                  </div>
                  <p className="text-2xl font-bold">€499<span className="text-sm font-normal text-muted-foreground">/maand</span></p>
                  <ul className="mt-4 space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-600" />
                      Onbeperkte projecten
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-600" />
                      10 gebruikers
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-green-600" />
                      API toegang
                    </li>
                  </ul>
                  <Button variant="outline" className="w-full mt-4">
                    Plan wijzigen
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Team Members */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Teamleden</CardTitle>
                  <CardDescription>
                    Beheer wie toegang heeft tot uw organisatie
                  </CardDescription>
                </div>
                <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                  <User className="h-4 w-4 mr-2" />
                  Uitnodigen
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockTeamMembers.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-4 rounded-lg border hover:border-marqed-blue/30 hover:bg-marqed-blue/5 transition-all"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-marqed-blue to-marqed-blue-dark flex items-center justify-center">
                        <span className="text-sm font-bold text-white">{member.avatar}</span>
                      </div>
                      <div>
                        <p className="font-medium">{member.name}</p>
                        <p className="text-sm text-muted-foreground">{member.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={cn(
                        'px-2.5 py-0.5 rounded-full text-xs font-medium',
                        member.role === 'Admin' ? 'bg-marqed-blue/10 text-marqed-blue' :
                        member.role === 'Developer' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      )}>
                        {member.role}
                      </span>
                      <Button variant="ghost" size="sm">
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Tab */}
        <TabsContent value="api" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5 text-marqed-blue" />
                    API Sleutels
                  </CardTitle>
                  <CardDescription>
                    Beheer API sleutels voor integraties met externe systemen
                  </CardDescription>
                </div>
                <Button className="bg-marqed-blue hover:bg-marqed-blue-dark">
                  <Key className="h-4 w-4 mr-2" />
                  Nieuwe sleutel
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockApiKeys.map((apiKey) => (
                  <div
                    key={apiKey.id}
                    className="flex items-center justify-between p-4 rounded-lg border"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                        <Key className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium">{apiKey.name}</p>
                        <p className="text-sm font-mono text-muted-foreground">{apiKey.key}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <p className="text-muted-foreground">Laatst gebruikt</p>
                        <p className="font-medium">{apiKey.lastUsed}</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyKey(apiKey.key, apiKey.id)}
                      >
                        {copiedKey === apiKey.id ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                      <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50">
                        Verwijderen
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 rounded-lg bg-marqed-blue/5 border border-marqed-blue/20">
                <div className="flex items-start gap-3">
                  <Globe className="h-5 w-5 text-marqed-blue mt-0.5" />
                  <div>
                    <p className="font-medium">API Documentatie</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Bekijk onze uitgebreide API documentatie voor integratiemogelijkheden.
                    </p>
                    <Button variant="outline" size="sm" className="mt-3">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Documentatie openen
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Webhooks */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <RefreshCw className="h-5 w-5 text-marqed-orange" />
                    Webhooks
                  </CardTitle>
                  <CardDescription>
                    Ontvang real-time notificaties bij events
                  </CardDescription>
                </div>
                <Button variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Webhook toevoegen
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 border-2 border-dashed rounded-lg">
                <RefreshCw className="h-12 w-12 text-muted-foreground mx-auto" />
                <h3 className="mt-4 text-lg font-semibold">Geen webhooks geconfigureerd</h3>
                <p className="text-muted-foreground mt-2 max-w-sm mx-auto">
                  Configureer webhooks om automatisch notificaties te ontvangen wanneer events plaatsvinden.
                </p>
                <Button className="mt-4 bg-marqed-blue hover:bg-marqed-blue-dark">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Eerste webhook toevoegen
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
