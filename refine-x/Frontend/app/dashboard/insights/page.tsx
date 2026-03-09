'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Sparkles, Loader2, ExternalLink } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { listJobs } from '@/lib/api/upload'
import { listInsights } from '@/lib/api/insights'
import type { InsightResponse } from '@/lib/api/types'

function confidenceBadge(score: number | null): 'success' | 'warning' | 'error' | 'default' {
  if (score == null) return 'default'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<(InsightResponse & { jobId: number; jobName: string })[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    listJobs()
      .then(async (jobs) => {
        const completed = jobs.filter(j => j.status === 'completed')
        const results = await Promise.all(
          completed.map(job =>
            listInsights(job.id)
              .then(ins => ins.map(i => ({ ...i, jobId: job.id, jobName: job.filename })))
              .catch(() => [])
          )
        )
        setInsights(results.flat())
      })
      .catch(() => setInsights([]))
      .finally(() => setLoading(false))
  }, [])

  const visible = insights.filter(i =>
    !search ||
    i.content.toLowerCase().includes(search.toLowerCase()) ||
    i.jobName.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Insights</h1>
        <p className="text-sm text-text-secondary">AI-generated observations across all your datasets</p>
      </div>

      <div className="dashboard-card rounded-2xl p-5 space-y-3">
        <input
          className="h-10 w-full rounded-lg border border-input bg-card px-3 text-sm"
          placeholder="Search insights..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : visible.length === 0 ? (
          <div className="text-center py-12">
            <Sparkles className="w-10 h-10 text-text-muted mx-auto mb-3" />
            <p className="text-sm text-text-secondary">
              {insights.length === 0
                ? 'No insights yet. Complete an analysis to generate AI insights.'
                : 'No insights match your search.'}
            </p>
            {insights.length === 0 && (
              <Link href="/dashboard/upload">
                <button className="mt-4 text-sm text-primary hover:underline">Upload a file →</button>
              </Link>
            )}
          </div>
        ) : (
          visible.map((insight) => (
            <div key={insight.id} className="rounded-xl border border-border bg-card/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="info">Insight #{insight.id}</Badge>
                  {insight.is_ai_generated != null && (
                    <Badge variant={insight.is_ai_generated ? 'info' : 'default'}>
                      {insight.is_ai_generated ? 'AI' : 'Computed'}
                    </Badge>
                  )}
                </div>
                {insight.confidence_score != null && (
                  <Badge variant={confidenceBadge(insight.confidence_score)}>
                    {insight.confidence_score}% confidence
                  </Badge>
                )}
              </div>
              <p className="text-sm text-foreground">{insight.content}</p>
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-text-muted">{insight.jobName}</p>
                <Link href={`/dashboard/project/${insight.jobId}/visualize`} className="text-xs text-primary hover:underline flex items-center gap-1">
                  View <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
