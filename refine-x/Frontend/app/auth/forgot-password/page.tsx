import Link from 'next/link'
import { ArrowLeft, Mail } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8">
      <div className="w-full max-w-md dashboard-card rounded-3xl p-8">
        <Link href="/auth/login" className="inline-flex items-center text-text-secondary hover:text-foreground mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Sign In
        </Link>

        <h1 className="text-3xl font-bold text-foreground mb-2">Reset your password</h1>
        <p className="text-text-secondary mb-6">Enter your email and we&apos;ll send you a link to reset your password.</p>

        <form className="space-y-4">
          <Input label="Work Email" type="email" placeholder="you@example.com" icon={<Mail className="w-4 h-4" />} required />
          <Button type="submit" className="w-full" size="lg">Send Reset Link</Button>
        </form>
      </div>
    </div>
  )
}
