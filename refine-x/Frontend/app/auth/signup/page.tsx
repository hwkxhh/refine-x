'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Mail, Lock, User, BarChart3, ArrowLeft, CheckCircle2, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useAuth } from '@/lib/auth/use-auth'

export default function SignupPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    organization: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const getPasswordStrength = (password: string) => {
    if (password.length === 0) return { strength: 0, label: '', color: '' }
    if (password.length < 6) return { strength: 33, label: 'Weak', color: 'bg-error' }
    if (password.length < 10) return { strength: 66, label: 'Good', color: 'bg-warning' }
    return { strength: 100, label: 'Strong', color: 'bg-success' }
  }

  const passwordStrength = getPasswordStrength(formData.password)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await register(formData.name, formData.email, formData.password)
      router.push('/auth/onboarding')
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'detail' in err
          ? (err as { detail: string }).detail
          : 'Registration failed. Please try again.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <Link href="/" className="inline-flex items-center text-text-secondary hover:text-foreground mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to home
          </Link>
          
          <div className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold text-foreground">RefineX</span>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Start analyzing your data</h1>
            <p className="text-text-secondary">
              Free forever. No credit card.
            </p>
          </div>

          {error && (
            <Alert variant="error" className="mb-6" dismissible onDismiss={() => setError('')}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Full Name"
              type="text"
              placeholder="John Doe"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              icon={<User className="w-4 h-4" />}
              required
            />

            <Input
              label="Work Email"
              type="email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              icon={<Mail className="w-4 h-4" />}
              required
            />

            <div>
              <Input
                label="Password"
                type="password"
                placeholder="Create a strong password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                icon={<Lock className="w-4 h-4" />}
                required
              />
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-text-muted">Password strength</span>
                    <span className={`font-medium ${
                      passwordStrength.strength === 100 ? 'text-success' :
                      passwordStrength.strength === 66 ? 'text-warning' : 'text-error'
                    }`}>
                      {passwordStrength.label}
                    </span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${passwordStrength.color} transition-all duration-300`}
                      style={{ width: `${passwordStrength.strength}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <Input
              label="Organization Name (optional)"
              type="text"
              placeholder="e.g., Acme Logistics"
              value={formData.organization}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
              icon={<Building2 className="w-4 h-4" />}
            />

            <div className="flex items-start gap-2">
              <input type="checkbox" className="mt-1 rounded border-input" required />
              <span className="text-sm text-text-secondary">
                I agree to the{' '}
                <Link href="#" className="text-primary hover:underline">Terms of Service</Link>
                {' '}and{' '}
                <Link href="#" className="text-primary hover:underline">Privacy Policy</Link>
              </span>
            </div>

            <Button type="submit" className="w-full" size="lg" isLoading={isLoading}>
              Create My Account
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-text-secondary">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-primary font-medium hover:underline">
              Sign In →
            </Link>
          </div>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-background text-text-muted">Or sign up with</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4">
              <Button variant="outline" className="w-full">
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
              </Button>
              <Button variant="outline" className="w-full">
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z" />
                </svg>
                Microsoft
              </Button>
            </div>
          </div>

          <p className="mt-6 text-xs text-text-muted text-center">
            By creating an account you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>

      {/* Right Side - Benefits */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary to-accent-coral p-12 items-center justify-center">
        <div className="max-w-lg text-white">
          <h2 className="text-4xl font-bold mb-6">
            Everything you need to analyze data
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Start your free trial today. No credit card required.
          </p>
          <div className="space-y-6">
            {[
              {
                title: 'Instant Setup',
                description: 'Get started in less than 2 minutes'
              },
              {
                title: 'AI-Powered',
                description: 'Automatic data cleaning and insights'
              },
              {
                title: 'Secure & Private',
                description: 'Your data is encrypted and protected'
              },
              {
                title: 'Unlimited Projects',
                description: 'Analyze as many datasets as you need'
              }
            ].map((feature, i) => (
              <div key={i} className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-1">{feature.title}</h3>
                  <p className="text-white/80">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
