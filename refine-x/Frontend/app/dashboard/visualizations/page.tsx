import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const charts = [
  { id: 1, title: 'Orders by Store — Current Period', type: 'Horizontal Bar Chart', insight: 'Nacharam leads with 355 orders. Attapur has the lowest volume at 67.' },
  { id: 2, title: 'Rider Earnings Distribution', type: 'Histogram', insight: 'Most riders earned between ₹600–₹800. 8 riders earned under ₹100.' },
  { id: 3, title: 'MG Dependency by Store', type: 'Stacked Bar', insight: 'Vanasthalipuram has 100% MG dependency.' },
  { id: 4, title: 'Order Count vs. Total Earning', type: 'Scatter Plot', insight: 'Strong positive correlation (r=0.87) with one outlier rider.' },
]

export default function VisualizationsPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Visualization Studio</h1>
          <p className="text-sm text-text-secondary">All charts from your analyses. Create new ones. Download any.</p>
        </div>
        <Button size="sm">+ New Chart</Button>
      </div>

      <div className="dashboard-card rounded-2xl p-5 space-y-3">
        {charts.map((chart) => (
          <div key={chart.id} className="rounded-xl border border-border bg-card/60 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-semibold text-foreground">{chart.title}</p>
              <Badge variant="default">{chart.type}</Badge>
            </div>
            <p className="text-xs text-text-secondary mt-2">{chart.insight}</p>
            <div className="mt-3 flex items-center gap-2">
              <Button size="sm" variant="outline" className="h-8 px-3 text-xs">Expand</Button>
              <Button size="sm" variant="outline" className="h-8 px-3 text-xs">Download PNG</Button>
              <Button size="sm" variant="outline" className="h-8 px-3 text-xs">Download SVG</Button>
              <Button size="sm" variant="outline" className="h-8 px-3 text-xs">Edit Chart</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
