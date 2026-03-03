'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowRight, TrendingUp, Users, MapPin, Package, DollarSign, Calendar, Check, Info, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getFormulaSuggestions } from '@/lib/api/ai-analysis'
import { setGoal, generateChart } from '@/lib/api/charts'
import type { SuggestedAnalysis, RecommendedViz } from '@/lib/api/types'

const iconMap: Record<string, any> = {
  trend: TrendingUp,
  customer: Users,
  regional: MapPin,
  product: Package,
  pricing: DollarSign,
  seasonal: Calendar,
}

const colorMap: Record<string, string> = {
  trend: 'from-blue-100 to-blue-200',
  customer: 'from-purple-100 to-purple-200',
  regional: 'from-green-100 to-green-200',
  product: 'from-orange-100 to-orange-200',
  pricing: 'from-pink-100 to-pink-200',
  seasonal: 'from-indigo-100 to-indigo-200',
}

function pickIcon(name: string) {
  const lower = name.toLowerCase()
  for (const [key, icon] of Object.entries(iconMap)) {
    if (lower.includes(key)) return icon
  }
  return TrendingUp
}

function pickColor(name: string) {
  const lower = name.toLowerCase()
  for (const [key, color] of Object.entries(colorMap)) {
    if (lower.includes(key)) return color
  }
  return 'from-gray-100 to-gray-200'
}

export default function AnalyticsSelectionPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = searchParams.get('jobId')

  const [analyses, setAnalyses] = useState<SuggestedAnalysis[]>([])
  const [vizzes, setVizzes] = useState<RecommendedViz[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) { setLoading(false); return }
    getFormulaSuggestions(Number(jobId))
      .then((data) => {
        setAnalyses(data.suggested_analyses ?? [])
        setVizzes(data.recommended_visualizations ?? [])
        // pre-select first two
        const pre = (data.suggested_analyses ?? []).slice(0, 2).map((_, i) => i)
        setSelectedIds(pre)
      })
      .catch(() => setError('Failed to load formula suggestions'))
      .finally(() => setLoading(false))
  }, [jobId])

  const toggleAnalytic = (index: number) => {
    setSelectedIds(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  const handleContinue = async () => {
    if (!jobId) return
    setGenerating(true)
    try {
      const id = Number(jobId)
      // Set goal based on selected analyses
      const goalText = selectedIds.map(i => analyses[i]?.name).filter(Boolean).join(', ')
      await setGoal(id, goalText || 'General analysis', 'custom')

      // Generate charts from recommended visualizations
      const selectedVizzes = vizzes.slice(0, 3) // generate up to 3 charts
      for (const v of selectedVizzes) {
        await generateChart(id, v.x_column, v.y_column || undefined, true).catch(() => {})
      }

      router.push(`/dashboard/project/${jobId}/visualize`)
    } catch {
      setError('Failed to generate analytics')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-text-secondary">AI is suggesting analytics for your data…</p>
      </div>
    )
  }

  if (error && analyses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-12 h-12 text-error" />
        <p className="text-error font-medium">{error}</p>
        <Button variant="outline" onClick={() => router.back()}>Go Back</Button>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <div className="flex items-center gap-2 text-sm text-text-secondary mb-2">
          <span>Step 3 of 4</span>
          <span>•</span>
          <span className="text-primary font-medium">Select Analytics</span>
        </div>
        <h1 className="text-3xl font-bold text-foreground mb-3">
          Choose Your Analytics
        </h1>
        <p className="text-text-secondary text-lg max-w-3xl">
          Select the types of analysis you'd like to run on your data. You can always change this later.
        </p>
      </div>

      {/* Selected Summary */}
      {selectedIds.length > 0 && (
        <div className="mb-6 dashboard-card rounded-2xl p-5 animate-fade-in-up">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Check className="w-5 h-5 text-primary" />
                <span className="font-semibold text-foreground">
                  {selectedIds.length} {selectedIds.length === 1 ? 'analytic' : 'analytics'} selected
                </span>
              </div>
            </div>
            <Button onClick={handleContinue} disabled={generating} className="gap-2">
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating…
                </>
              ) : (
                <>
                  Continue to Visualization
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Analytics Grid — from AI suggestions */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {analyses.map((analytic, index) => {
          const isSelected = selectedIds.includes(index)
          const Icon = pickIcon(analytic.name)
          const color = pickColor(analytic.name)

          return (
            <div
              key={index}
              className="animate-fade-in-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <button
                onClick={() => toggleAnalytic(index)}
                className={`w-full text-left dashboard-card rounded-2xl p-6 transition-all duration-200 relative overflow-hidden group ${
                  isSelected ? 'ring-2 ring-primary shadow-lg' : 'hover:shadow-lg'
                }`}
              >
                {/* Selection Indicator */}
                <div className={`absolute top-4 left-4 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                  isSelected ? 'bg-primary border-primary' : 'border-border group-hover:border-primary'
                }`}>
                  {isSelected && <Check className="w-4 h-4 text-white" />}
                </div>

                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4 mt-8`}>
                  <Icon className="w-7 h-7 text-gray-700" />
                </div>

                {/* Content */}
                <h3 className="text-lg font-bold text-foreground mb-2">
                  {analytic.name}
                </h3>
                <p className="text-sm text-text-secondary mb-4 leading-relaxed">
                  {analytic.description}
                </p>

                {/* Columns needed */}
                {analytic.columns_needed.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {analytic.columns_needed.map((col) => (
                      <span key={col} className="px-2 py-0.5 rounded bg-muted text-xs text-text-muted">{col}</span>
                    ))}
                  </div>
                )}

                {/* Formula type */}
                <div className="flex items-center justify-between text-xs mt-3">
                  <span className="text-text-muted">{analytic.formula_type}</span>
                </div>
              </button>
            </div>
          )
        })}
      </div>

      {/* Recommended Visualizations */}
      {vizzes.length > 0 && (
        <div className="dashboard-card rounded-2xl p-5 mb-8 animate-fade-in-up stagger-6">
          <h3 className="font-semibold text-foreground mb-3">Recommended Visualizations</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vizzes.map((v, i) => (
              <div key={i} className="p-4 rounded-lg border border-border">
                <p className="text-sm font-medium text-foreground">{v.chart_type}</p>
                <p className="text-xs text-text-muted mt-1">{v.x_column} {v.y_column ? `vs ${v.y_column}` : ''}</p>
                <p className="text-xs text-text-secondary mt-2">{v.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="dashboard-card rounded-2xl p-5 flex items-start gap-4 animate-fade-in-up stagger-8">
        <Info className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
        <div className="text-sm text-text-secondary">
          <span className="font-semibold text-foreground">Tip:</span> We recommend starting with 2-3 analytics to get quick insights. 
          You can always run additional analytics later from the dashboard.
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
        <Button variant="ghost" onClick={() => router.back()}>
          Back
        </Button>
        <Button
          onClick={handleContinue}
          disabled={selectedIds.length === 0 || generating}
          className="gap-2"
          size="lg"
        >
          {generating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generating…
            </>
          ) : (
            <>
              Generate Analytics ({selectedIds.length})
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
