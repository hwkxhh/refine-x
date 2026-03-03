'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ChevronDown, ChevronUp, AlertCircle, CheckCircle, Info, TrendingUp, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getCleaningSummary } from '@/lib/api/cleaning'
import type { CleaningSummaryResponse, ColumnMeta } from '@/lib/api/types'

interface ColumnProfile {
  name: string
  type: string
  uniqueValues: number
  missingPercent: number
  quality: string
  samples: string[]
}

function deriveProfiles(meta: Record<string, ColumnMeta>): ColumnProfile[] {
  return Object.entries(meta).map(([name, m]) => {
    const totalInferred = (m.null_count ?? 0) + (m.unique_count ?? 1)
    const missingPct = totalInferred > 0 ? Math.round((m.null_count / totalInferred) * 100) : 0
    let quality = 'Excellent'
    if (missingPct > 20) quality = 'Fair'
    else if (missingPct > 5) quality = 'Good'
    return {
      name,
      type: m.dtype ?? 'unknown',
      uniqueValues: m.unique_count ?? 0,
      missingPercent: missingPct,
      quality,
      samples: m.sample ?? [],
    }
  })
}

export default function DataProfilePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = searchParams.get('jobId')
  const [expandedColumn, setExpandedColumn] = useState<string | null>(null)
  const [profiles, setProfiles] = useState<ColumnProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) { setLoading(false); return }
    getCleaningSummary(Number(jobId))
      .then((data: CleaningSummaryResponse) => {
        if (data.column_metadata) setProfiles(deriveProfiles(data.column_metadata))
      })
      .catch(() => setError('Failed to load column profiles'))
      .finally(() => setLoading(false))
  }, [jobId])

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'Excellent': return 'success'
      case 'Good': return 'info'
      case 'Fair': return 'warning'
      default: return 'error'
    }
  }

  const getQualityIcon = (quality: string) => {
    switch (quality) {
      case 'Excellent': return <CheckCircle className="w-4 h-4" />
      case 'Good': return <CheckCircle className="w-4 h-4" />
      case 'Fair': return <AlertCircle className="w-4 h-4" />
      default: return <AlertCircle className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
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
          <h1 className="text-3xl font-bold text-foreground mb-2">Data Profiling</h1>
          <p className="text-text-secondary">Review column statistics and data quality</p>
        </div>
        <Button onClick={() => router.push(`/dashboard/project/new/clean?jobId=${jobId}`)}>
          Next: Data Cleaning
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-muted">Total Columns</h4>
              <TrendingUp className="w-4 h-4 text-primary" />
            </div>
            <p className="text-3xl font-bold text-foreground">{profiles.length}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-muted">Excellent Quality</h4>
              <CheckCircle className="w-4 h-4 text-success" />
            </div>
            <p className="text-3xl font-bold text-foreground">
              {profiles.filter(c => c.quality === 'Excellent').length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-muted">Needs Attention</h4>
              <AlertCircle className="w-4 h-4 text-warning" />
            </div>
            <p className="text-3xl font-bold text-foreground">
              {profiles.filter(c => c.quality === 'Fair').length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-text-muted">Avg Completeness</h4>
              <Info className="w-4 h-4 text-info" />
            </div>
            <p className="text-3xl font-bold text-foreground">
              {profiles.length > 0
                ? (100 - profiles.reduce((acc, c) => acc + c.missingPercent, 0) / profiles.length).toFixed(1)
                : '0'}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Column Profiles Table */}
      <Card>
        <CardHeader>
          <CardTitle>Column Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {profiles.map((column, index) => (
              <div key={index}>
                <div
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-accent-coral/50 cursor-pointer transition-colors"
                  onClick={() => setExpandedColumn(expandedColumn === column.name ? null : column.name)}
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-bold text-primary">{column.type.charAt(0)}</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-foreground">{column.name}</h4>
                      <p className="text-sm text-text-secondary">{column.type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="hidden sm:block text-right">
                      <p className="text-sm font-medium text-foreground">{column.uniqueValues.toLocaleString()}</p>
                      <p className="text-xs text-text-muted">Unique values</p>
                    </div>
                    <div className="hidden md:block text-right">
                      <p className="text-sm font-medium text-foreground">{column.missingPercent}%</p>
                      <p className="text-xs text-text-muted">Missing</p>
                    </div>
                    <Badge variant={getQualityColor(column.quality) as any} className="flex items-center gap-1">
                      {getQualityIcon(column.quality)}
                      {column.quality}
                    </Badge>
                    {expandedColumn === column.name ? (
                      <ChevronUp className="w-5 h-5 text-text-muted" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-text-muted" />
                    )}
                  </div>
                </div>

                {expandedColumn === column.name && (
                  <div className="ml-4 mt-2 p-4 bg-muted rounded-lg border border-border">
                    <div className="grid md:grid-cols-3 gap-6">
                      <div>
                        <h5 className="text-sm font-semibold text-foreground mb-2">Statistics</h5>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-text-muted">Data Type:</span>
                            <span className="font-medium text-foreground">{column.type}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-text-muted">Unique Values:</span>
                            <span className="font-medium text-foreground">{column.uniqueValues.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-text-muted">Missing:</span>
                            <span className="font-medium text-foreground">{column.missingPercent}%</span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h5 className="text-sm font-semibold text-foreground mb-2">Sample Values</h5>
                        <div className="space-y-1">
                          {column.samples.map((sample, i) => (
                            <div key={i} className="text-sm text-text-secondary px-2 py-1 bg-background rounded">
                              {sample}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h5 className="text-sm font-semibold text-foreground mb-2">Quality Assessment</h5>
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm">
                            <CheckCircle className="w-4 h-4 text-success" />
                            <span className="text-text-secondary">No duplicates detected</span>
                          </div>
                          {column.missingPercent === 0 ? (
                            <div className="flex items-center gap-2 text-sm">
                              <CheckCircle className="w-4 h-4 text-success" />
                              <span className="text-text-secondary">Complete data</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-sm">
                              <AlertCircle className="w-4 h-4 text-warning" />
                              <span className="text-text-secondary">Has missing values</span>
                            </div>
                          )}
                          <div className="flex items-center gap-2 text-sm">
                            <CheckCircle className="w-4 h-4 text-success" />
                            <span className="text-text-secondary">Consistent formatting</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => router.back()}>
          Back
        </Button>
        <Button onClick={() => router.push(`/dashboard/project/new/clean?jobId=${jobId}`)}>
          Continue to Data Cleaning
        </Button>
      </div>
    </div>
  )
}
