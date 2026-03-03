'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Download, BarChart3, Loader2, Search, FileSpreadsheet } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { listJobs } from '@/lib/api/upload'
import { exportCSV } from '@/lib/api/cleaning'
import type { UploadJobListResponse } from '@/lib/api/types'

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

export default function DatasetsPage() {
  const [jobs, setJobs] = useState<UploadJobListResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'completed' | 'awaiting_review'>('all')
  const [downloading, setDownloading] = useState<number | null>(null)

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false))
  }, [])

  const visible = jobs.filter(j => {
    const matchSearch = j.filename.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filter === 'all' || j.status === filter
    return matchSearch && matchFilter
  })

  async function handleDownload(jobId: number, filename: string) {
    setDownloading(jobId)
    try {
      const blob = await exportCSV(jobId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename.replace(/\.[^.]+$/, '_cleaned.csv')
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Download failed. The cleaned file may not be ready yet.')
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Datasets</h1>
        <p className="text-sm text-text-secondary">Cleaned datasets generated from your analyses</p>
      </div>

      <div className="dashboard-card rounded-2xl p-5">
        <div className="grid gap-3 sm:grid-cols-2 mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              className="h-10 w-full rounded-lg border border-input bg-card pl-9 pr-3 text-sm"
              placeholder="Search datasets..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <select
            value={filter}
            onChange={e => setFilter(e.target.value as typeof filter)}
            className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
          >
            <option value="all">All</option>
            <option value="awaiting_review">Needs Review</option>
            <option value="completed">Ready</option>
          </select>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : visible.length === 0 ? (
          <div className="text-center py-12">
            <FileSpreadsheet className="w-10 h-10 text-text-muted mx-auto mb-3" />
            <p className="text-sm text-text-secondary">
              {jobs.length === 0 ? 'No datasets yet. Upload a file to get started.' : 'No datasets match your search.'}
            </p>
            {jobs.length === 0 && (
              <Link href="/dashboard/upload">
                <Button size="sm" className="mt-4">Upload a file</Button>
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {visible.map((job) => (
              <div key={job.id} className="rounded-xl border border-border bg-card/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-foreground">{job.filename}</p>
                  <Badge variant={job.status === 'completed' ? 'success' : job.status === 'awaiting_review' ? 'warning' : job.status === 'failed' ? 'error' : 'info'}>
                    {job.status === 'completed' ? 'Ready' : job.status === 'awaiting_review' ? 'Needs Review' : job.status === 'failed' ? 'Failed' : 'Processing'}
                  </Badge>
                </div>
                <p className="text-sm text-text-secondary mt-1">
                  Job #{job.id} · {timeAgo(job.created_at)}
                  {job.quality_score != null && ` · Data Quality ${job.quality_score}/100`}
                </p>
                <div className="mt-3 flex items-center gap-2 flex-wrap">
                  {job.status === 'completed' && (
                    <>
                      <Link href={`/dashboard/project/${job.id}/visualize`}>
                        <Button size="sm" variant="outline" className="h-8 px-3 text-xs gap-1">
                          <BarChart3 className="w-3 h-3" /> View Analysis
                        </Button>
                      </Link>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 px-3 text-xs gap-1"
                        onClick={() => handleDownload(job.id, job.filename)}
                        disabled={downloading === job.id}
                      >
                        <Download className="w-3 h-3" />
                        {downloading === job.id ? 'Downloading…' : 'Download CSV'}
                      </Button>
                    </>
                  )}
                  {job.status === 'awaiting_review' && (
                    <Link href="/dashboard/upload">
                      <Button size="sm" variant="outline" className="h-8 px-3 text-xs">Review Columns</Button>
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
