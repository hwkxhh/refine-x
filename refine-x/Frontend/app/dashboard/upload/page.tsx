'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, X, CheckCircle, AlertCircle, FileText, Loader2, ShieldCheck, ShieldX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { formatBytes } from '@/lib/utils'
import { uploadFile, getJobStatus, reviewColumns } from '@/lib/api/upload'
import type { JobStatusResponse, ColumnRelevanceResult } from '@/lib/api/types'

type Phase = 'idle' | 'uploading' | 'processing' | 'reviewing' | 'resuming' | 'completed' | 'failed'

export default function UploadPage() {
  const router = useRouter()
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [phase, setPhase] = useState<Phase>('idle')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [jobId, setJobId] = useState<number | null>(null)
  const [statusData, setStatusData] = useState<JobStatusResponse | null>(null)
  const [columnRelevance, setColumnRelevance] = useState<ColumnRelevanceResult | null>(null)
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(new Set())
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* ── Cleanup polling on unmount ─────────────────────────────────────── */
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  /* ── Polling logic ──────────────────────────────────────────────────── */
  const startPolling = useCallback((id: number) => {
    if (pollRef.current) clearInterval(pollRef.current)

    pollRef.current = setInterval(async () => {
      try {
        const status = await getJobStatus(id)
        setStatusData(status)
        setProgress(status.progress ?? 0)

        if (status.status === 'awaiting_review') {
          // Phase 1 done — show column review UI
          clearInterval(pollRef.current!)
          pollRef.current = null
          setColumnRelevance(status.column_relevance_result ?? null)
          // Pre-select columns recommended to "keep"
          if (status.column_relevance_result?.columns) {
            const keeps = new Set(
              status.column_relevance_result.columns
                .filter((c) => c.recommendation === 'keep')
                .map((c) => c.name),
            )
            setSelectedColumns(keeps)
          }
          setPhase('reviewing')
        } else if (status.status === 'completed') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          setPhase('completed')
        } else if (status.status === 'failed') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          setError(status.error_message || 'Processing failed')
          setPhase('failed')
        }
        // else keep polling (pending / processing)
      } catch {
        clearInterval(pollRef.current!)
        pollRef.current = null
        setError('Lost connection while checking status')
        setPhase('failed')
      }
    }, 2000)
  }, [])

  /* ── File handlers ──────────────────────────────────────────────────── */
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      handleFileUpload(file)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileUpload(file)
  }

  /* ── Upload to backend ──────────────────────────────────────────────── */
  const handleFileUpload = async (file: File) => {
    setSelectedFile(file)
    setPhase('uploading')
    setError('')
    setProgress(0)

    try {
      const job = await uploadFile(file)
      setJobId(job.id)
      setPhase('processing')
      startPolling(job.id)
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'detail' in err
          ? (err as { detail: string }).detail
          : 'Upload failed. Please try again.'
      setError(message)
      setPhase('failed')
    }
  }

  /* ── Column toggle ──────────────────────────────────────────────────── */
  const toggleColumn = (colName: string) => {
    setSelectedColumns((prev) => {
      const next = new Set(prev)
      if (next.has(colName)) next.delete(colName)
      else next.add(colName)
      return next
    })
  }

  /* ── Submit column review ───────────────────────────────────────────── */
  const handleReviewSubmit = async () => {
    if (!jobId || selectedColumns.size === 0) return
    setPhase('resuming')
    setError('')

    try {
      await reviewColumns(jobId, Array.from(selectedColumns))
      startPolling(jobId) // Phase 2 polling
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'detail' in err
          ? (err as { detail: string }).detail
          : 'Failed to submit review'
      setError(message)
      setPhase('failed')
    }
  }

  /* ── Reset ──────────────────────────────────────────────────────────── */
  const handleRemove = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    setSelectedFile(null)
    setPhase('idle')
    setProgress(0)
    setError('')
    setJobId(null)
    setStatusData(null)
    setColumnRelevance(null)
    setSelectedColumns(new Set())
  }

  /* ── Navigate to results ────────────────────────────────────────────── */
  const handleProceed = () => {
    if (jobId) router.push(`/dashboard/project/new/profile?jobId=${jobId}`)
  }

  /* ── Progress bar label ─────────────────────────────────────────────── */
  const progressLabel = () => {
    if (phase === 'uploading') return 'Uploading file...'
    if (phase === 'processing') return `Processing... ${progress}%`
    if (phase === 'resuming') return `Cleaning & analyzing... ${progress}%`
    if (phase === 'completed') return 'Complete!'
    return ''
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Upload CSV File</h1>
        <p className="text-text-secondary">Upload your data file to start analyzing</p>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="error" dismissible onDismiss={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* ── PHASE: IDLE — drop zone ─────────────────────────────────────── */}
      {phase === 'idle' && (
        <Card>
          <CardContent className="p-12">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${
                isDragging
                  ? 'border-primary bg-primary/5 scale-105'
                  : 'border-border hover:border-primary/50 hover:bg-muted/50'
              }`}
            >
              <div className="flex flex-col items-center gap-4">
                <div className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors ${
                  isDragging ? 'bg-primary' : 'bg-primary/10'
                }`}>
                  <Upload className={`w-10 h-10 ${isDragging ? 'text-primary-foreground' : 'text-primary'}`} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    {isDragging ? 'Drop your file here' : 'Drag and drop your file'}
                  </h3>
                  <p className="text-text-secondary mb-4">or click to browse from your computer</p>
                  <input
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <Button
                    type="button"
                    className="cursor-pointer"
                    onClick={() => document.getElementById('file-upload')?.click()}
                  >
                    Select File
                  </Button>
                </div>
                <div className="flex items-center gap-6 text-sm text-text-muted mt-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success" />
                    <span>Max file size: 50MB</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success" />
                    <span>Supported: CSV, XLSX, XLS</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── PHASE: UPLOADING / PROCESSING / RESUMING — progress ─────────── */}
      {(phase === 'uploading' || phase === 'processing' || phase === 'resuming') && selectedFile && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-lg flex items-center justify-center bg-primary/10">
                  <Loader2 className="w-7 h-7 text-primary animate-spin" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">{selectedFile.name}</h3>
                  <p className="text-sm text-text-secondary">{formatBytes(selectedFile.size)}</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={handleRemove}>
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">{progressLabel()}</span>
                <span className="font-medium text-foreground">{progress}%</span>
              </div>
              <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${Math.max(progress, phase === 'uploading' ? 10 : 0)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── PHASE: REVIEWING — column relevance gate ────────────────────── */}
      {phase === 'reviewing' && columnRelevance && (
        <>
          <Alert variant="info">
            <strong>Column Review Required</strong> — Our AI has analyzed your columns.
            Review the recommendations below, then confirm which columns to keep.
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Column Relevance Review</CardTitle>
              <p className="text-sm text-text-secondary mt-1">
                {columnRelevance.reason}
              </p>
            </CardHeader>
            <CardContent>
              <div className="border border-border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-foreground w-12">Keep</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground">Column Name</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground">AI Recommendation</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {columnRelevance.columns.map((col) => (
                      <tr
                        key={col.name}
                        className={`border-b border-border transition-colors ${
                          selectedColumns.has(col.name) ? 'bg-success/5' : 'bg-error/5'
                        }`}
                      >
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={selectedColumns.has(col.name)}
                            onChange={() => toggleColumn(col.name)}
                            className="w-4 h-4 rounded border-input accent-primary"
                          />
                        </td>
                        <td className="px-4 py-3 font-medium text-foreground">{col.name}</td>
                        <td className="px-4 py-3">
                          {col.recommendation === 'keep' ? (
                            <Badge variant="success" className="gap-1">
                              <ShieldCheck className="w-3 h-3" /> Keep
                            </Badge>
                          ) : (
                            <Badge variant="warning" className="gap-1">
                              <ShieldX className="w-3 h-3" /> Remove
                            </Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 text-text-secondary">{col.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-6">
                <p className="text-sm text-text-muted">
                  {selectedColumns.size} of {columnRelevance.columns.length} columns selected
                </p>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => {
                    // Select all
                    setSelectedColumns(new Set(columnRelevance.columns.map(c => c.name)))
                  }}>
                    Select All
                  </Button>
                  <Button onClick={handleReviewSubmit} disabled={selectedColumns.size === 0}>
                    Confirm & Continue ({selectedColumns.size} columns)
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* ── PHASE: COMPLETED ────────────────────────────────────────────── */}
      {phase === 'completed' && selectedFile && (
        <>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-lg flex items-center justify-center bg-success/10">
                    <CheckCircle className="w-7 h-7 text-success" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-1">{selectedFile.name}</h3>
                    <p className="text-sm text-text-secondary">{formatBytes(selectedFile.size)}</p>
                  </div>
                </div>
                <Badge variant="success">Processing Complete</Badge>
              </div>
            </CardContent>
          </Card>

          {statusData && (
            <div className="grid md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-foreground">Rows</h4>
                    <FileText className="w-5 h-5 text-primary" />
                  </div>
                  <p className="text-3xl font-bold text-foreground">
                    {statusData.row_count?.toLocaleString() ?? '—'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-foreground">Quality Score</h4>
                    <CheckCircle className="w-5 h-5 text-success" />
                  </div>
                  <p className="text-3xl font-bold text-foreground">
                    {statusData.quality_score != null
                      ? `${statusData.quality_score.toFixed(1)}%`
                      : '—'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-foreground">Status</h4>
                    <AlertCircle className="w-5 h-5 text-primary" />
                  </div>
                  <p className="text-3xl font-bold text-success">Complete</p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="flex justify-end gap-4">
            <Button variant="outline" onClick={handleRemove}>
              Upload Another
            </Button>
            <Button onClick={handleProceed} size="lg">
              Proceed to Analysis
            </Button>
          </div>
        </>
      )}

      {/* ── PHASE: FAILED ───────────────────────────────────────────────── */}
      {phase === 'failed' && (
        <div className="flex justify-center">
          <Button onClick={handleRemove}>Try Again</Button>
        </div>
      )}

      {/* Help Text */}
      {phase === 'idle' && (
        <Card className="border-info/20 bg-info/5">
          <CardContent className="p-6">
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-info/20 flex items-center justify-center flex-shrink-0">
                <span className="text-lg">ℹ️</span>
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-2">Tips for best results</h3>
                <ul className="space-y-1 text-sm text-text-secondary">
                  <li>• Ensure your CSV has column headers in the first row</li>
                  <li>• Remove any special characters or formatting from your data</li>
                  <li>• Keep file sizes under 50MB for optimal performance</li>
                  <li>• Use standard date formats (YYYY-MM-DD) for date columns</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
