'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { BarChart3, ChevronRight, ChevronLeft, Upload, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

const organizationTypes = [
  { id: 'school', name: '🏫 School or University' },
  { id: 'hospital', name: '🏥 Hospital or Clinic' },
  { id: 'ngo', name: '🤝 NGO or Non-profit' },
  { id: 'retail', name: '🛒 Retail or Supermarket' },
  { id: 'logistics', name: '🚚 Logistics or Delivery' },
  { id: 'business', name: '🏢 Business or Corporation' },
  { id: 'government', name: '🏛️ Government or Public Sector' },
  { id: 'research', name: '🔬 Research or Academia' },
  { id: 'other', name: 'Other' },
]

const dataTeamSizes = ['Just me', '2–5 people', '6–20 people', '20+ people']

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [organizationType, setOrganizationType] = useState('')
  const [teamSize, setTeamSize] = useState('')
  const [workspaceName, setWorkspaceName] = useState('')
  const [workspaceGoal, setWorkspaceGoal] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1)
    } else {
      handleComplete()
    }
  }

  const handleComplete = () => {
    setIsLoading(true)
    setTimeout(() => {
      router.push('/dashboard/upload')
    }, 1000)
  }

  const canProceed = () => {
    if (step === 1) return organizationType !== '' && teamSize !== ''
    if (step === 2) return workspaceName.trim().length > 0
    return true
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="max-w-4xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">RefineX</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-muted">
              Step {step} of 3
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="border-b border-border">
        <div className="max-w-4xl mx-auto px-8">
          <div className="flex gap-2 py-4">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                  s <= step ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-4xl">
          {/* Step 1: About You */}
          {step === 1 && (
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-foreground mb-4">
                Welcome to RefineX. Let&apos;s set things up.
              </h1>
              <p className="text-lg text-text-secondary max-w-2xl mx-auto">
                This takes 60 seconds and helps us personalize your experience.
              </p>
              <div className="mt-10 max-w-4xl mx-auto text-left">
                <p className="text-sm font-semibold text-foreground mb-3">What best describes your organization?</p>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {organizationTypes.map((org) => (
                    <Card
                      key={org.id}
                      className={`cursor-pointer transition-all duration-200 ${
                        organizationType === org.id
                          ? 'border-primary shadow-lg scale-[1.02]'
                          : 'border-border hover:border-accent-coral/50'
                      }`}
                      onClick={() => setOrganizationType(org.id)}
                    >
                      <CardContent className="p-4">
                        <p className="text-sm font-medium text-foreground">{org.name}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <p className="text-sm font-semibold text-foreground mb-3 mt-8">How many people work with data at your organization?</p>
                <div className="grid sm:grid-cols-2 gap-3">
                  {dataTeamSizes.map((size) => (
                    <Card
                      key={size}
                      className={`cursor-pointer transition-all duration-200 ${
                        teamSize === size
                          ? 'border-primary shadow-lg scale-[1.02]'
                          : 'border-border hover:border-accent-coral/50'
                      }`}
                      onClick={() => setTeamSize(size)}
                    >
                      <CardContent className="p-4">
                        <p className="text-sm font-medium text-foreground">{size}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: First Workspace */}
          {step === 2 && (
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-foreground mb-4">
                Create your first workspace
              </h1>
              <p className="text-lg text-text-secondary max-w-2xl mx-auto">
                A workspace keeps related datasets and analyses together. You can create more later.
              </p>

              <div className="max-w-2xl mx-auto mt-10 space-y-5 text-left">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Workspace name</label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                    <input
                      className="w-full h-11 rounded-xl border border-input bg-card pl-10 pr-3 text-sm"
                      value={workspaceName}
                      onChange={(e) => setWorkspaceName(e.target.value)}
                      placeholder="e.g., Monthly Payroll, Student Records, Sales Reports"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">What goal does this workspace serve?</label>
                  <input
                    className="w-full h-11 rounded-xl border border-input bg-card px-3 text-sm"
                    value={workspaceGoal}
                    onChange={(e) => setWorkspaceGoal(e.target.value)}
                    placeholder="e.g., Track rider payment accuracy each week"
                  />
                </div>

                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="text-sm text-primary font-medium hover:underline"
                >
                  I&apos;ll set this up later
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Upload first file */}
          {step === 3 && (
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-foreground mb-4">
                Now, let&apos;s see your data.
              </h1>
              <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-10">
                Upload any CSV or Excel file. We&apos;ll show you what RefineX does with it.
              </p>

              <Card className="max-w-2xl mx-auto border-border">
                <CardContent className="p-10 text-center">
                  <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
                    <Upload className="w-8 h-8 text-primary" />
                  </div>
                  <p className="text-lg font-semibold text-foreground">Drag and drop your file here</p>
                  <p className="text-sm text-text-muted mt-1">or</p>
                  <Button className="mt-4">Browse files</Button>
                  <p className="text-xs text-text-muted mt-4">Accepts CSV, XLSX, XLS · Up to 5MB on free plan</p>

                  <button type="button" className="mt-4 text-sm text-primary font-medium hover:underline">
                    Don&apos;t have a file ready? Try with our sample dataset →
                  </button>
                </CardContent>
              </Card>

              <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
                <Button onClick={handleComplete} isLoading={isLoading}>
                  Analyze This File →
                </Button>
                <button
                  type="button"
                  onClick={() => router.push('/dashboard')}
                  className="text-sm text-text-secondary hover:text-foreground"
                >
                  Skip for now — take me to my dashboard
                </button>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center mt-12">
            <Button
              variant="ghost"
              onClick={() => setStep(step - 1)}
              disabled={step === 1}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back
            </Button>

            {step === 1 && (
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
                size="lg"
              >
                Continue →
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}

            {step === 2 && (
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
                size="lg"
              >
                Create Workspace →
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
