import { Button } from '@/components/ui/button'

const historyItems = [
  { id: 1, icon: '📤', event: 'File uploaded: Raw_Data.xlsx', time: '22 Feb 2026, 14:30' },
  { id: 2, icon: '🔧', event: 'Auto-fix applied: Column renamed "Fule" → "Fuel"', time: '22 Feb 2026, 14:31' },
  { id: 3, icon: '👤', event: 'You resolved: Name casing applied to 255 rows', time: '22 Feb 2026, 14:33' },
  { id: 4, icon: '💡', event: '5 insights generated', time: '22 Feb 2026, 14:32' },
  { id: 5, icon: '📊', event: 'Chart created: Orders by Store', time: '22 Feb 2026, 14:35' },
  { id: 6, icon: '⬇️', event: 'Chart downloaded: Orders by Store (PNG)', time: '22 Feb 2026, 14:40' },
]

export default function HistoryPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">History</h1>
          <p className="text-sm text-text-secondary">Every upload, every change, every insight — fully logged</p>
        </div>
        <Button size="sm" variant="outline">Download full audit log (CSV)</Button>
      </div>

      <div className="dashboard-card rounded-2xl p-5">
        <div className="grid gap-3 md:grid-cols-3 mb-4">
          <input className="h-10 rounded-lg border border-input bg-card px-3 text-sm" placeholder="Filter by action type" />
          <input className="h-10 rounded-lg border border-input bg-card px-3 text-sm" placeholder="Filter by date range" />
          <input className="h-10 rounded-lg border border-input bg-card px-3 text-sm" placeholder="Filter by workspace" />
        </div>

        <div className="space-y-3">
          {historyItems.map((item) => (
            <div key={item.id} className="rounded-xl border border-border bg-card/60 p-4 flex items-center justify-between gap-3">
              <p className="text-sm text-foreground"><span className="mr-2">{item.icon}</span>{item.event}</p>
              <p className="text-xs text-text-muted whitespace-nowrap">{item.time}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
