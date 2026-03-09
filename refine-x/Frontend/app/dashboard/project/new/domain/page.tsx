'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Sparkles, Loader2, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { analyzeHeaders } from '@/lib/api/ai-analysis'
import type { HeaderAnalysisResponse, AnalyzedColumn } from '@/lib/api/types'

export default function DomainDetectionPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = searchParams.get('jobId')
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

  const columns: AnalyzedColumn[] = analysis?.columns ?? []
  const keepCount = columns.filter((c) => c.decision === 'keep').length
  const dropCount = columns.filter((c) => c.decision === 'drop').length

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Column Analysis</h1>
          <p className="text-text-secondary">AI has reviewed every column and explained what it measures</p>
        </div>
        <Button onClick={() => router.push(`/dashboard/project/new/analytics?jobId=${jobId}`)}>
          Next: Select Analytics
        </Button>
      </div>

      {/* Summary banner */}
      {analysis && (
        <Alert variant="success">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <strong>AI Analysis Complete</strong>
              <p className="mt-1 text-sm">{analysis.dataset_summary}</p>
              <p className="mt-1 text-sm">
                <span className="text-success font-medium">{keepCount} keep</span>
                {dropCount > 0 && (
                  <span className="text-warning font-medium ml-3">{dropCount} flagged for removal</span>
                )}
              </p>
            </div>
          </div>
        </Alert>
      )}

      {/* Per-column cards */}
      {columns.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {columns.map((col) => (
            <Card
              key={col.column}
              className={`border ${
                col.decision === 'keep'
                  ? 'border-success/30 bg-success/5'
                  : 'border-warning/30 bg-warning/5'
              }`}
            >
              <CardContent className="p-4 space-y-3">
                {/* Column name + decision badge */}
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-semibold text-foreground truncate" title={col.column}>
                    {col.column}
                  </h3>
                  {col.decision === 'keep' ? (
                    <Badge variant="success" className="flex items-center gap-1 shrink-0">
                      <CheckCircle className="w-3 h-3" /> KEEP
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="flex items-center gap-1 shrink-0">
                      <AlertCircle className="w-3 h-3" /> DROP
                    </Badge>
                  )}
                </div>

                {/* What it measures */}
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1">What it is</p>
                  <p className="text-sm text-foreground leading-relaxed">{col.what_it_measures}</p>
                </div>

                {/* Why keep / drop */}
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1">
                    {col.decision === 'keep' ? 'Why keep' : 'Why drop'}
                  </p>
                  <p className="text-sm text-text-secondary leading-relaxed">{col.why}</p>
                </div>

                {/* Analytical use (keep columns only) */}
                {col.analytical_use && (
                  <div>
                    <p className="text-xs font-medium text-text-muted uppercase tracking-wide mb-1">Enables</p>
                    <p className="text-sm text-text-secondary leading-relaxed">{col.analytical_use}</p>
                  </div>
                )}

                {/* Warning */}
                {col.warning && (
                  <div className="flex items-start gap-2 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 px-3 py-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-700 dark:text-amber-300 leading-relaxed">{col.warning}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        !loading && (
          <div className="flex flex-col items-center justify-center h-48 gap-3 text-text-secondary">
            <AlertCircle className="w-8 h-8" />
            <p>No column analysis available.</p>
          </div>
        )
      )}

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => router.back()}>Back</Button>
        <Button onClick={() => router.push(`/dashboard/project/new/analytics?jobId=${jobId}`)}>
          Confirm & Continue
        </Button>
      </div>
    </div>
  )
}
