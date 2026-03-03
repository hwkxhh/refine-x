import Link from 'next/link'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const analyses = [
  {
    id: 1,
    file: 'Raw_Data.xlsx',
    goal: 'Track rider payment accuracy',
    status: 'Issues Found',
    score: 90,
    meta: '415 rows · 13 columns · 8 issues found',
  },
  {
    id: 2,
    file: 'Monthly_Sales_Feb.csv',
    goal: 'Understand monthly sales trends',
    status: 'Complete',
    score: 96,
    meta: '1,218 rows · 9 columns · 2 issues found',
  },
  {
    id: 3,
    file: 'Admissions_Q1.xlsx',
    goal: 'Increase student admissions',
    status: 'Needs Review',
    score: 84,
    meta: '782 rows · 16 columns · 6 issues found',
  },
]

export default function AnalysesPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Analyses</h1>
          <p className="text-sm text-text-secondary">All files you've analyzed in this workspace</p>
        </div>
        <Link href="/dashboard/upload">
          <Button size="sm">Upload a File →</Button>
        </Link>
      </div>

      <div className="dashboard-card rounded-2xl p-5">
        <div className="grid gap-3 md:grid-cols-3 mb-4">
          <input className="h-10 rounded-lg border border-input bg-card px-3 text-sm" placeholder="Search by file name or goal..." />
          <select defaultValue="All Statuses" className="h-10 rounded-lg border border-input bg-card px-3 text-sm">
            <option>All Statuses</option>
            <option>Complete</option>
            <option>Issues Found</option>
            <option>Needs Review</option>
          </select>
          <select defaultValue="Most Recent" className="h-10 rounded-lg border border-input bg-card px-3 text-sm">
            <option>Most Recent</option>
            <option>Oldest</option>
            <option>Highest Quality Score</option>
            <option>Lowest Quality Score</option>
          </select>
        </div>

        <div className="space-y-3">
          {analyses.map((analysis) => (
            <div key={analysis.id} className="rounded-xl border border-border bg-card/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-semibold text-foreground">{analysis.file}</p>
                  <p className="text-xs text-text-muted">{analysis.goal}</p>
                </div>
                <Badge variant={analysis.status === 'Complete' ? 'success' : analysis.status === 'Issues Found' ? 'warning' : 'info'}>{analysis.status}</Badge>
              </div>
              <p className="text-sm text-text-secondary mt-2">{analysis.meta}</p>
              <div className="mt-3 flex items-center justify-between">
                <p className="text-xs text-text-muted">Data Quality Score: <span className="font-semibold text-foreground">{analysis.score}/100</span></p>
                <Link href="/dashboard/project/1/insights" className="text-xs font-medium text-primary hover:underline">View Report</Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
