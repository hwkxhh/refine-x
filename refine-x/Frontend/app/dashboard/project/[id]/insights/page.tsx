'use client'

import { useState, useEffect, use } from 'react'
import Link from 'next/link'
import { Sparkles, TrendingUp, AlertTriangle, Lightbulb, Download, Share2, Loader2, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { listInsights } from '@/lib/api/insights'
import { getCleaningSummary } from '@/lib/api/cleaning'
import type { InsightResponse, CleaningSummaryResponse } from '@/lib/api/types'

export default function InsightsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const jobId = Number(id)

  const [insights, setInsights] = useState<InsightResponse[]>([])
  const [summary, setSummary] = useState<CleaningSummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      listInsights(jobId).catch(() => [] as InsightResponse[]),
      getCleaningSummary(jobId).catch(() => null),
    ]).then(([ins, sum]) => {
      setInsights(ins)
      setSummary(sum)
    }).finally(() => setLoading(false))
  }, [jobId])

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  const totalRows = summary?.row_count_cleaned ?? summary?.row_count_original ?? 0
  const totalCols = Object.keys(summary?.column_metadata ?? {}).length
  const qualityScore = summary?.quality_score ?? null
  const missingFilled = summary?.missing_filled ?? null

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">AI-Generated Insights</h1>
          <p className="text-text-secondary">Automated analysis and recommendations for Job #{jobId}</p>
        </div>
        <div className="flex gap-3">
          <Link href={`/dashboard/project/${jobId}/visualize`}>
            <Button size="sm" variant="outline">
              Back to Charts
            </Button>
          </Link>
        </div>
      </div>

      {/* Dataset Summary */}
      {summary && (
        <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Dataset Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-text-muted">Rows</p>
                <p className="font-semibold text-foreground text-lg">{totalRows.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-text-muted">Columns</p>
                <p className="font-semibold text-foreground text-lg">{totalCols}</p>
              </div>
              {qualityScore != null && (
                <div>
                  <p className="text-text-muted">Quality Score</p>
                  <p className={`font-semibold text-lg ${qualityScore >= 90 ? 'text-success' : qualityScore >= 70 ? 'text-warning' : 'text-error'}`}>
                    {qualityScore}/100
                  </p>
                </div>
              )}
              {missingFilled != null && (
                <div>
                  <p className="text-text-muted">Missing Filled</p>
                  <p className="font-semibold text-foreground text-lg">{missingFilled}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Insights List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">
          Key Findings
          {insights.length > 0 && <span className="ml-2 text-sm font-normal text-text-muted">({insights.length})</span>}
        </h2>

        {insights.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center">
              <Lightbulb className="w-10 h-10 text-text-muted mx-auto mb-3" />
              <p className="text-text-secondary text-sm">No insights generated yet.</p>
              <p className="text-text-muted text-xs mt-1">Go to the Charts page and click "Generate Insight" on a chart.</p>
              <Link href={`/dashboard/project/${jobId}/visualize`}>
                <Button size="sm" className="mt-4" variant="outline">
                  <ExternalLink className="w-4 h-4 mr-2" /> Go to Charts
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          insights.map((insight) => (
            <Card key={insight.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2 gap-2">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">Insight #{insight.id}</p>
                        {insight.is_ai_generated != null && (
                          <Badge variant={insight.is_ai_generated ? 'info' : 'default'}>
                            {insight.is_ai_generated ? 'AI' : 'Computed'}
                          </Badge>
                        )}
                      </div>
                      {insight.confidence_score != null && (
                        <Badge variant={insight.confidence_score >= 80 ? 'success' : insight.confidence_score >= 60 ? 'warning' : 'error'}>
                          {insight.confidence_score}% confidence
                        </Badge>
                      )}
                    </div>
                    <p className="text-text-secondary text-sm leading-relaxed">{insight.content}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Data Quality Breakdown */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Data Quality Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              {Object.entries(summary.column_metadata ?? {}).slice(0, 12).map(([col, meta]: [string, any]) => (
                <div key={col} className="flex items-center justify-between p-3 rounded-lg bg-muted">
                  <div>
                    <p className="font-medium text-foreground truncate max-w-[180px]">{col}</p>
                    <p className="text-xs text-text-muted">{meta.dtype}</p>
                  </div>
                  <div className="text-right">
                    {meta.null_count > 0 ? (
                      <Badge variant="warning">{meta.null_count} missing</Badge>
                    ) : (
                      <Badge variant="success">Complete</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {Object.keys(summary.column_metadata ?? {}).length > 12 && (
              <p className="text-xs text-text-muted mt-3 text-center">
                +{Object.keys(summary.column_metadata ?? {}).length - 12} more columns
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
