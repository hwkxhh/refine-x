'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { TrendingUp, Users, DollarSign, Package, BarChart3, Briefcase, Sparkles, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { analyzeHeaders } from '@/lib/api/ai-analysis'
import type { HeaderAnalysisResponse } from '@/lib/api/types'

const domainIcons: Record<string, any> = {
  'Sales & Revenue': TrendingUp,
  'Customer Analytics': Users,
  'Financial Data': DollarSign,
  'Operations': Package,
  'Marketing': BarChart3,
  'Human Resources': Briefcase,
}

export default function DomainDetectionPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = searchParams.get('jobId')
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<HeaderAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) { setLoading(false); return }
    analyzeHeaders(Number(jobId))
      .then((data) => setAnalysis(data))
      .catch(() => setError('Failed to analyze headers'))
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-text-secondary">AI is analyzing your data columns…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-12 h-12 text-error" />
        <p className="text-error font-medium">{error}</p>
        <Button variant="outline" onClick={() => router.back()}>Go Back</Button>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Domain Detection</h1>
          <p className="text-text-secondary">AI has analyzed your data to determine its domain</p>
        </div>
        <Button onClick={() => router.push(`/dashboard/project/new/analytics?jobId=${jobId}`)}>
          Next: Select Analytics
        </Button>
      </div>

      {/* AI Detection Result */}
      {analysis && (
        <Alert variant="success">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <strong>AI Header Analysis Complete</strong>
              <p className="mt-1">{analysis.dataset_summary}</p>
            </div>
          </div>
        </Alert>
      )}

      {/* Essential Columns */}
      <Card className="border-primary shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-success" />
            Essential Columns ({analysis?.essential_columns.length ?? 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {analysis?.essential_columns.map((col) => (
              <Badge key={col} variant="success">{col}</Badge>
            ))}
            {(!analysis || analysis.essential_columns.length === 0) && (
              <p className="text-text-secondary text-sm">No essential columns identified</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Unnecessary Columns */}
      {analysis && analysis.unnecessary_columns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning" />
              Potentially Unnecessary Columns ({analysis.unnecessary_columns.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analysis.unnecessary_columns.map((col) => (
                <div key={col.column} className="flex items-start justify-between p-4 rounded-lg border border-border">
                  <div className="flex-1">
                    <h4 className="font-semibold text-foreground">{col.column}</h4>
                    <p className="text-sm text-text-secondary mt-1">{col.reason}</p>
                    <p className="text-xs text-text-muted mt-1">Impact if removed: {col.impact_if_removed}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => router.back()}>
          Back
        </Button>
        <Button onClick={() => router.push(`/dashboard/project/new/analytics?jobId=${jobId}`)}>
          Confirm & Continue
        </Button>
      </div>
    </div>
  )
}
