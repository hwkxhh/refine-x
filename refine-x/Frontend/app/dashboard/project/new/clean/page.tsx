'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Wand2, RefreshCw, AlertCircle, CheckCircle, Eye, EyeOff, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert } from '@/components/ui/alert'
import { getCleaningSummary, getAuditTrail, getMissingFields } from '@/lib/api/cleaning'
import type { CleaningSummaryResponse, AuditLogEntry, MissingFieldsResponse, ColumnMeta } from '@/lib/api/types'

interface ColumnIssue {
  name: string
  missingPercent: number
  missingCount: number
}

export default function DataCleanPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = searchParams.get('jobId')
  const [autoClean, setAutoClean] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showBefore, setShowBefore] = useState(true)
  const [cleaningLog, setCleaningLog] = useState<string[]>([])

  const [summary, setSummary] = useState<CleaningSummaryResponse | null>(null)
  const [columnIssues, setColumnIssues] = useState<ColumnIssue[]>([])
  const [auditTrail, setAuditTrail] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) { setLoading(false); return }
    const id = Number(jobId)
    Promise.all([
      getCleaningSummary(id),
      getAuditTrail(id),
      getMissingFields(id).catch(() => null),
    ])
      .then(([sum, trail, missing]) => {
        setSummary(sum)
        setAuditTrail(trail)
        // derive column issues from metadata
        if (sum.column_metadata) {
          const issues: ColumnIssue[] = []
          for (const [name, meta] of Object.entries(sum.column_metadata)) {
            if (meta.null_count > 0) {
              const total = (sum.row_count_original ?? sum.row_count_cleaned ?? 1)
              issues.push({
                name,
                missingCount: meta.null_count,
                missingPercent: Math.round((meta.null_count / total) * 100),
              })
            }
          }
          setColumnIssues(issues)
        }
        // Build initial cleaning log from audit trail
        if (trail.length > 0) {
          const logs = trail.slice(0, 10).map(e => `✓ ${e.action}${e.column_name ? ` on "${e.column_name}"` : ''} — ${e.reason}`)
          setCleaningLog(logs)
        }
      })
      .catch(() => setError('Failed to load cleaning data'))
      .finally(() => setLoading(false))
  }, [jobId])

  const handleAutoClean = () => {
    setIsProcessing(true)
    setCleaningLog([])
    // Re-fetch audit trail to show any new cleaning actions
    const id = Number(jobId)
    getAuditTrail(id)
      .then((trail) => {
        if (trail.length > 0) {
          const logs = trail.slice(0, 10).map(e => `✓ ${e.action}${e.column_name ? ` on "${e.column_name}"` : ''} — ${e.reason}`)
          setCleaningLog(logs)
        } else {
          setCleaningLog(['✓ No additional cleaning actions needed — data is already clean'])
        }
      })
      .catch(() => setCleaningLog(['✗ Failed to retrieve cleaning log']))
      .finally(() => setIsProcessing(false))
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
          <h1 className="text-3xl font-bold text-foreground mb-2">Data Cleaning</h1>
          <p className="text-text-secondary">Clean and prepare your data for analysis</p>
        </div>
        <Button onClick={() => router.push(`/dashboard/project/new/domain?jobId=${jobId}`)}>
          Next: Domain Detection
        </Button>
      </div>

      {/* Auto-Clean Toggle */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Wand2 className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">Auto-Clean Data</h3>
                <p className="text-sm text-text-secondary">Let AI automatically fix common data quality issues</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoClean}
                  onChange={(e) => setAutoClean(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
              {autoClean && (
                <Button onClick={handleAutoClean} isLoading={isProcessing}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Run Auto-Clean
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cleaning Log */}
      {cleaningLog.length > 0 && (
        <Alert variant="success">
          <strong>Cleaning complete!</strong>
          <div className="mt-2 space-y-1">
            {cleaningLog.map((log, i) => (
              <div key={i} className="text-sm">{log}</div>
            ))}
          </div>
        </Alert>
      )}

      {/* Cleaning Summary Stats */}
      {summary && (
        <div className="grid md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">{summary.row_count_original ?? '—'}</p>
              <p className="text-xs text-text-muted">Original Rows</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">{summary.row_count_cleaned ?? '—'}</p>
              <p className="text-xs text-text-muted">Cleaned Rows</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">{summary.duplicates_removed}</p>
              <p className="text-xs text-text-muted">Duplicates Removed</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">{summary.quality_score != null ? `${summary.quality_score}%` : '—'}</p>
              <p className="text-xs text-text-muted">Quality Score</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Audit Trail */}
      {auditTrail.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Cleaning Audit Trail</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border border-border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-foreground border-b border-border">Action</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground border-b border-border">Column</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground border-b border-border">Before</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground border-b border-border">After</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground border-b border-border">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditTrail.slice(0, 20).map((entry) => (
                      <tr key={entry.id} className="hover:bg-muted/50">
                        <td className="px-4 py-3 border-b border-border text-text-secondary">{entry.action}</td>
                        <td className="px-4 py-3 border-b border-border text-text-secondary">{entry.column_name ?? '—'}</td>
                        <td className="px-4 py-3 border-b border-border text-error">{entry.original_value ?? '—'}</td>
                        <td className="px-4 py-3 border-b border-border text-success font-medium">{entry.new_value ?? '—'}</td>
                        <td className="px-4 py-3 border-b border-border text-text-secondary text-xs">{entry.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Column Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Column-Level Actions</CardTitle>
        </CardHeader>
        <CardContent>
          {columnIssues.length === 0 ? (
            <div className="flex items-center gap-3 p-4 text-success">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">All columns are complete — no missing values detected.</span>
            </div>
          ) : (
            <div className="space-y-3">
              {columnIssues.map((column, index) => (
                <div key={index} className="flex items-center justify-between p-4 rounded-lg border border-border">
                  <div className="flex items-center gap-4">
                    <AlertCircle className="w-5 h-5 text-warning" />
                    <div>
                      <h4 className="font-medium text-foreground">{column.name}</h4>
                      <p className="text-sm text-text-secondary">{column.missingPercent}% missing ({column.missingCount} values)</p>
                    </div>
                  </div>
                  <select className="h-9 px-3 rounded-lg border border-input bg-card text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    <option>Fill with mean</option>
                    <option>Fill with median</option>
                    <option>Fill with mode</option>
                    <option>Fill with zero</option>
                    <option>Drop rows</option>
                  </select>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => router.back()}>
          Back
        </Button>
        <Button onClick={() => router.push(`/dashboard/project/new/domain?jobId=${jobId}`)}>
          Continue to Domain Detection
        </Button>
      </div>
    </div>
  )
}
