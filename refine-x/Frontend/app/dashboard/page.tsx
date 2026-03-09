'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  FileUp,
  Sparkles,
  TrendingUp,
  Loader2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth/use-auth'
import { listJobs } from '@/lib/api/upload'
import { listInsights } from '@/lib/api/insights'
import { listCharts } from '@/lib/api/charts'
import type { UploadJobListResponse, InsightResponse, ChartListItem } from '@/lib/api/types'

// ── helpers ──────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return 'Yesterday'
  return `${days} days ago`
}

function jobStatusLabel(status: string): string {
  switch (status) {
    case 'completed': return 'Complete'
    case 'awaiting_review': return 'Awaiting Review'
    case 'processing': return 'Processing'
    case 'failed': return 'Failed'
    default: return 'Pending'
  }
}

function jobStatusVariant(status: string): 'success' | 'warning' | 'info' | 'error' | 'default' {
  switch (status) {
    case 'completed': return 'success'
    case 'awaiting_review': return 'warning'
    case 'failed': return 'error'
    case 'processing': return 'info'
    default: return 'default'
  }
}

function greeting(name: string | null): string {
  const hour = new Date().getHours()
  const part = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening'
  return `Good ${part}, ${name ?? 'there'}.`
}

function todayLabel(): string {
  return new Date().toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { user } = useAuth()

  const [jobs, setJobs] = useState<UploadJobListResponse[]>([])
  const [insights, setInsights] = useState<InsightResponse[]>([])
  const [charts, setCharts] = useState<ChartListItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      listJobs().catch(() => [] as UploadJobListResponse[]),
      // Insights and charts need a jobId; pull from most recent completed job
    ]).then(([jobList]) => {
      setJobs(jobList)
      const completedJobs = jobList.filter(j => j.status === 'completed')
      if (completedJobs.length > 0) {
        const latestId = completedJobs[0].id
        Promise.all([
          listInsights(latestId).catch(() => [] as InsightResponse[]),
          listCharts(latestId).catch(() => [] as ChartListItem[]),
        ]).then(([ins, ch]) => {
          setInsights(ins)
          setCharts(ch)
        }).finally(() => setLoading(false))
      } else {
        setLoading(false)
      }
    })
  }, [])

  // ── derived stats ──────────────────────────────────────────────────────────
  const totalJobs = jobs.length
  const completedJobs = jobs.filter(j => j.status === 'completed').length
  const awaitingReview = jobs.filter(j => j.status === 'awaiting_review').length
  const avgQuality = completedJobs > 0
    ? Math.round(jobs.filter(j => j.quality_score != null).reduce((s, j) => s + (j.quality_score ?? 0), 0) / completedJobs)
    : null

  const recentJobs = jobs.slice(0, 3)
  const recentInsights = insights.slice(0, 3)
  const recentCharts = charts.slice(0, 4)

  // ── empty state banner ─────────────────────────────────────────────────────
  const noData = !loading && jobs.length === 0

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">

      {/* ── Welcome banner ─────────────────────────────────────────────────── */}
      <div className="card-gradient rounded-2xl p-5 text-white animate-fade-in-up">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-semibold">{greeting(user?.name ?? null)} Your workspace is ready.</p>
            <p className="text-sm text-white/90">
              {noData
                ? 'Upload your first file to get started. RefineX will clean, analyze and summarize it.'
                : `${completedJobs} file${completedJobs !== 1 ? 's' : ''} cleaned · ${insights.length} insight${insights.length !== 1 ? 's' : ''} generated · ${charts.length} chart${charts.length !== 1 ? 's' : ''} created`}
            </p>
          </div>
          <Link href="/dashboard/upload">
            <Button variant="secondary" size="sm" className="h-10 px-4 text-primary">
              Upload a File <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>
      </div>

      {/* ── Heading ────────────────────────────────────────────────────────── */}
      <section className="animate-fade-in-up stagger-1">
        <h1 className="text-2xl font-bold text-foreground">{greeting(user?.name ?? null)}</h1>
        <p className="text-sm text-text-secondary mt-1">{todayLabel()}</p>
        {awaitingReview > 0 && (
          <p className="text-sm text-text-muted mt-2">
            You have <span className="text-warning font-medium">{awaitingReview} file{awaitingReview > 1 ? 's' : ''}</span> awaiting column review.{' '}
            <Link href="/dashboard/projects" className="text-primary hover:underline">Review now →</Link>
          </p>
        )}
      </section>

      {/* ── KPI cards ──────────────────────────────────────────────────────── */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 animate-fade-in-up stagger-2">
        {[
          { label: 'Files Uploaded', value: String(totalJobs), sub: totalJobs === 0 ? 'None yet' : `${completedJobs} completed`, icon: FileUp },
          { label: 'Insights Generated', value: String(insights.length), sub: insights.length === 0 ? 'Run analytics to generate' : 'From latest dataset', icon: Sparkles },
          { label: 'Charts Created', value: String(charts.length), sub: charts.length === 0 ? 'No charts yet' : 'From latest dataset', icon: BarChart3 },
          { label: 'Avg. Quality Score', value: avgQuality != null ? `${avgQuality}/100` : '—', sub: avgQuality != null ? (avgQuality >= 90 ? '✓ Excellent' : avgQuality >= 70 ? 'Good' : 'Needs attention') : 'No completed files', icon: TrendingUp },
        ].map((item) => (
          <div key={item.label} className="dashboard-card rounded-2xl p-5 dashboard-card-hover">
            <div className="flex items-start justify-between">
              <p className="text-sm text-text-secondary font-medium">{item.label}</p>
              <item.icon className="w-4 h-4 text-primary" />
            </div>
            <p className="text-2xl font-bold text-foreground mt-2">{item.value}</p>
            <p className="text-xs text-text-muted mt-1">{item.sub}</p>
          </div>
        ))}
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">

          {/* ── Recent Analyses ──────────────────────────────────────────────── */}
          <section className="dashboard-card rounded-2xl p-5 animate-fade-in-up stagger-3">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Recent Analyses</h2>
              <Link href="/dashboard/projects" className="text-sm text-primary font-medium hover:underline">View all →</Link>
            </div>
            {recentJobs.length === 0 ? (
              <div className="text-center py-10">
                <FileUp className="w-10 h-10 text-text-muted mx-auto mb-3" />
                <p className="text-sm text-text-secondary">No files uploaded yet.</p>
                <Link href="/dashboard/upload">
                  <Button size="sm" className="mt-4">Upload your first file</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentJobs.map((job) => (
                  <div key={job.id} className="rounded-xl border border-border bg-card/60 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-semibold text-foreground">{job.filename}</p>
                        <p className="text-xs text-text-muted">Job #{job.id} · {timeAgo(job.created_at)}</p>
                      </div>
                      <Badge variant={jobStatusVariant(job.status)}>{jobStatusLabel(job.status)}</Badge>
                    </div>
                    {job.quality_score != null && (
                      <p className="text-xs text-text-muted mt-2">
                        Data Quality Score: <span className="font-semibold text-foreground">{job.quality_score}/100</span>
                      </p>
                    )}
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-xs font-medium text-primary">
                      {job.status === 'completed' && (
                        <Link href={`/dashboard/project/${job.id}/visualize`} className="hover:underline">View Charts</Link>
                      )}
                      {job.status === 'awaiting_review' && (
                        <Link href={`/dashboard/project/new/profile?jobId=${job.id}`} className="hover:underline text-warning">Resume Review</Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* ── Latest Insights ──────────────────────────────────────────────── */}
          <section className="dashboard-card rounded-2xl p-5 animate-fade-in-up stagger-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Latest Insights</h2>
            </div>
            {recentInsights.length === 0 ? (
              <div className="text-center py-10">
                <Sparkles className="w-10 h-10 text-text-muted mx-auto mb-3" />
                <p className="text-sm text-text-secondary">No insights yet. Complete the analytics step to generate AI insights.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentInsights.map((insight) => (
                  <div key={insight.id} className="rounded-xl border border-border bg-card/60 p-4">
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="info">{insight.confidence.toUpperCase()}</Badge>
                        {insight.is_ai_generated != null && (
                          <Badge variant={insight.is_ai_generated ? 'info' : 'default'}>
                            {insight.is_ai_generated ? 'AI' : 'Computed'}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-text-muted">Score: {Math.round(insight.confidence_score * 100)}%</p>
                    </div>
                    <p className="text-sm text-foreground leading-relaxed">{insight.content}</p>
                    {insight.recommendations && insight.recommendations.length > 0 && (
                      <p className="text-xs text-text-muted mt-2 italic">
                        → {insight.recommendations[0].action}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="space-y-6">

          {/* ── Charts ───────────────────────────────────────────────────────── */}
          <section className="dashboard-card rounded-2xl p-5 animate-fade-in-up stagger-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Your Charts</h2>
              {completedJobs > 0 && (
                <Link href={`/dashboard/project/${jobs.find(j => j.status === 'completed')?.id}/visualize`} className="text-sm text-primary font-medium hover:underline">Open →</Link>
              )}
            </div>
            {recentCharts.length === 0 ? (
              <div className="text-center py-10">
                <BarChart3 className="w-10 h-10 text-text-muted mx-auto mb-3" />
                <p className="text-sm text-text-secondary">No charts yet. Complete the analytics step.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentCharts.map((chart) => (
                  <div key={chart.id} className="rounded-xl border border-border bg-card/60 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-medium text-foreground text-sm truncate">{chart.title}</p>
                        <p className="text-xs text-text-muted">{chart.x_header}{chart.y_header ? ` vs ${chart.y_header}` : ''}</p>
                      </div>
                      <Badge variant="default">{chart.chart_type}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* ── Smart Recommendations ────────────────────────────────────────── */}
          <section className="dashboard-card rounded-2xl p-5 animate-fade-in-up stagger-6">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">RefineX Recommends</h2>
            </div>
            <p className="text-xs text-text-muted mb-4">Next steps based on your workspace</p>
            <div className="space-y-3">
              {noData ? (
                <div className="rounded-xl border border-border bg-card/60 p-4">
                  <Badge variant="info" className="mb-2">GET STARTED</Badge>
                  <p className="text-sm font-semibold text-foreground">Upload your first dataset</p>
                  <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                    Upload a CSV or Excel file. RefineX will clean it, detect issues, and generate AI insights automatically.
                  </p>
                  <Link href="/dashboard/upload">
                    <Button size="sm" className="mt-3 h-8 px-3 text-xs">Upload a File →</Button>
                  </Link>
                </div>
              ) : (
                <>
                  {awaitingReview > 0 && (
                    <div className="rounded-xl border border-border bg-card/60 p-4">
                      <Badge variant="warning" className="mb-2">ACTION NEEDED</Badge>
                      <p className="text-sm font-semibold text-foreground">{awaitingReview} file{awaitingReview > 1 ? 's' : ''} awaiting column review</p>
                      <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                        Review and confirm the columns detected in your upload to continue processing.
                      </p>
                      <Link href="/dashboard/projects">
                        <Button size="sm" variant="outline" className="mt-3 h-8 px-3 text-xs">Review Now →</Button>
                      </Link>
                    </div>
                  )}
                  {completedJobs > 0 && charts.length === 0 && (
                    <div className="rounded-xl border border-border bg-card/60 p-4">
                      <Badge variant="info" className="mb-2">NEXT STEP</Badge>
                      <p className="text-sm font-semibold text-foreground">Generate charts for your data</p>
                      <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                        Your data is clean. Select analytics and let RefineX generate visualizations.
                      </p>
                      <Link href={`/dashboard/project/new/analytics?jobId=${jobs.find(j => j.status === 'completed')?.id}`}>
                        <Button size="sm" className="mt-3 h-8 px-3 text-xs">Run Analytics →</Button>
                      </Link>
                    </div>
                  )}
                  {completedJobs > 0 && charts.length > 0 && insights.length === 0 && (
                    <div className="rounded-xl border border-border bg-card/60 p-4">
                      <Badge variant="info" className="mb-2">OPPORTUNITY</Badge>
                      <p className="text-sm font-semibold text-foreground">Generate AI insights from your charts</p>
                      <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                        Open a chart and click "Generate AI Insight" to get data-driven recommendations.
                      </p>
                      <Link href={`/dashboard/project/${jobs.find(j => j.status === 'completed')?.id}/visualize`}>
                        <Button size="sm" variant="outline" className="mt-3 h-8 px-3 text-xs">Open Charts →</Button>
                      </Link>
                    </div>
                  )}
                  {completedJobs > 0 && (
                    <div className="rounded-xl border border-border bg-card/60 p-4">
                      <Badge variant="default" className="mb-2">EXPLORE</Badge>
                      <p className="text-sm font-semibold text-foreground">Upload another dataset to compare</p>
                      <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                        RefineX can detect changes between uploads and highlight significant differences.
                      </p>
                      <Link href="/dashboard/upload">
                        <Button size="sm" variant="outline" className="mt-3 h-8 px-3 text-xs">Upload New File →</Button>
                      </Link>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* ── Upload CTA ─────────────────────────────────────────────────────── */}
      <section className="dashboard-card rounded-2xl p-5 border-dashed border border-primary/30 animate-fade-in-up stagger-7">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p className="font-semibold text-foreground">+ Analyze a new file</p>
            <p className="text-sm text-text-secondary">Drop a file here or click to browse · Accepts CSV, XLSX, XLS</p>
          </div>
          <Link href="/dashboard/upload">
            <Button size="sm" className="h-10 px-4">
              <FileUp className="w-4 h-4 mr-2" />
              Analyze a File →
            </Button>
          </Link>
        </div>
      </section>
    </div>
  )
}
