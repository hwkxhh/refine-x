'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { FolderOpen, MoreVertical, Search, Plus, Download, Trash2, Archive, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/ui/empty-state'
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

function statusVariant(status: string): 'info' | 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'completed': return 'success'
    case 'awaiting_review': return 'warning'
    case 'processing': return 'info'
    case 'failed': return 'error'
    default: return 'default'
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'completed': return 'Completed'
    case 'awaiting_review': return 'Awaiting Review'
    case 'processing': return 'Processing'
    case 'failed': return 'Failed'
    default: return 'Pending'
  }
}

export default function ProjectsPage() {
  const [jobs, setJobs] = useState<UploadJobListResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'awaiting_review' | 'processing' | 'failed'>('all')
  const [showMenu, setShowMenu] = useState<number | null>(null)
  const [downloading, setDownloading] = useState<number | null>(null)

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = jobs.filter(job => {
    const matchesSearch = job.filename.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterStatus === 'all' || job.status === filterStatus
    return matchesSearch && matchesFilter
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

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Projects</h1>
          <p className="text-text-secondary">Manage and view your uploaded datasets</p>
        </div>
        <Link href="/dashboard/upload">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search projects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                icon={<Search className="w-4 h-4" />}
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {(['all', 'completed', 'awaiting_review', 'processing', 'failed'] as const).map(s => (
                <Button
                  key={s}
                  variant={filterStatus === s ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setFilterStatus(s)}
                >
                  {s === 'all' ? 'All' : statusLabel(s)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Projects Grid */}
      {filtered.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((job) => (
            <Card key={job.id} className="group hover:shadow-lg transition-shadow duration-200">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <FolderOpen className="w-6 h-6 text-primary" />
                  </div>
                  <div className="relative">
                    <button
                      onClick={() => setShowMenu(showMenu === job.id ? null : job.id)}
                      className="p-1 text-text-muted hover:text-foreground hover:bg-muted rounded transition-colors"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>
                    {showMenu === job.id && (
                      <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg py-2 z-10">
                        <Link
                          href={`/dashboard/project/${job.id}/visualize`}
                          className="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:bg-muted"
                          onClick={() => setShowMenu(null)}
                        >
                          <FolderOpen className="w-4 h-4" />
                          Open
                        </Link>
                        <button
                          className="flex items-center gap-2 px-4 py-2 text-sm text-text-secondary hover:bg-muted w-full text-left"
                          onClick={() => { setShowMenu(null); handleDownload(job.id, job.filename) }}
                        >
                          <Download className="w-4 h-4" />
                          {downloading === job.id ? 'Downloading…' : 'Export CSV'}
                        </button>
                        <hr className="my-2 border-border" />
                        <button className="flex items-center gap-2 px-4 py-2 text-sm text-text-muted hover:bg-muted w-full text-left cursor-not-allowed opacity-50">
                          <Archive className="w-4 h-4" />
                          Archive
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 text-sm text-error hover:bg-muted w-full text-left cursor-not-allowed opacity-50">
                          <Trash2 className="w-4 h-4" />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <Link href={job.status === 'completed' ? `/dashboard/project/${job.id}/visualize` : `/dashboard/upload`}>
                  <h3 className="font-semibold text-foreground mb-1 hover:text-primary transition-colors truncate">
                    {job.filename}
                  </h3>
                  <p className="text-xs text-text-muted mb-3">Job #{job.id} · {timeAgo(job.created_at)}</p>

                  {job.quality_score != null && (
                    <p className="text-sm text-text-secondary mb-3">
                      Data Quality: <span className="font-semibold text-foreground">{job.quality_score}/100</span>
                    </p>
                  )}

                  <div className="flex items-center justify-between">
                    <Badge variant={statusVariant(job.status)}>
                      {statusLabel(job.status)}
                    </Badge>
                    <span className="text-xs text-text-disabled">
                      {new Date(job.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon="search"
          title={jobs.length === 0 ? 'No projects yet' : 'No projects found'}
          description={jobs.length === 0 ? 'Upload a file to create your first project' : 'Try adjusting your search or filter'}
        />
      )}
    </div>
  )
}


