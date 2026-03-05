'use client'

import { useState, useEffect, use } from 'react'
import Link from 'next/link'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  ScatterChart, Scatter, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import {
  TrendingUp, BarChart3, PieChart as PieIcon, Download,
  Sparkles, Target, Activity, Award, Loader2, AlertCircle, Plus,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { listCharts, getChart, getGoal, getRecommendations, generateChart } from '@/lib/api/charts'
import { generateInsight, listInsights } from '@/lib/api/insights'
import { getCleaningSummary, exportCSV } from '@/lib/api/cleaning'
import type { ChartResponse, ChartListItem, InsightResponse, CleaningSummaryResponse, GoalResponse, RecommendationItem } from '@/lib/api/types'

// -- Theme-aligned chart palette ----------------------------------------------
const CHART_COLORS = ['#6366f1', '#818cf8', '#a5b4fc', '#67e8f9', '#f9a8d4', '#93c5fd']

// -- Shared tooltip -----------------------------------------------------------
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-foreground text-white px-4 py-3 rounded-xl shadow-lg text-sm">
      <p className="font-semibold mb-1.5">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-xs flex items-center gap-2 mt-1">
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ background: entry.color || entry.fill }}
          />
          <span className="opacity-70">{entry.name}:</span>
          <span className="font-semibold">{typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}</span>
        </p>
      ))}
    </div>
  )
}

// -- AI Insight block ---------------------------------------------------------
function InsightBlock({ insights }: { insights: string[] }) {
  if (!insights.length) return null
  return (
    <div className="border-t border-primary/10 bg-gradient-to-br from-primary/[0.05] to-transparent px-6 py-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-[10px] font-bold text-primary uppercase tracking-widest mb-2">AI Insight</p>
          <div className="space-y-1.5">
            {insights.map((text, i) => (
              <p key={i} className="text-sm text-text-secondary leading-relaxed">
                {i > 0 && <span className="text-primary/40 mr-1.5 select-none">�</span>}
                {text}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// -- Helpers -----------------------------------------------------------------
/** True when all values look like calendar years (1800–2100). */
function isYearLike(vals: number[]): boolean {
  return vals.length > 0 && vals.every(v => v >= 1800 && v <= 2100)
}

/** Compute a sensible XAxis / YAxis domain. Never starts at 0 for year data. */
function numDomain(
  vals: number[],
  yearLike: boolean,
): [number, number] | ['dataMin', 'dataMax'] {
  if (!vals.length) return ['dataMin', 'dataMax']
  const lo = Math.min(...vals)
  const hi = Math.max(...vals)
  if (yearLike) return [lo - 1, hi + 1]
  const span = hi - lo || 1
  return [lo - span * 0.05, hi + span * 0.05]
}

// -- Fix A: Universal x-axis tick formatter -----------------------------------
const formatXAxisTick = (value: string | number): string => {
  const s = String(value)

  // Remove time components from date strings
  const cleaned = s
    .replace(/T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?/g, '')
    .replace(/\s+\d{2}:\d{2}:\d{2}/g, '')
    .replace(/\.000000000/g, '')
    .trim()

  // If it looks like a full date, format it
  const dt = new Date(cleaned)
  if (!isNaN(dt.getTime()) && cleaned.includes('-')) {
    return dt.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  }

  // Truncate long category names
  if (cleaned.length > 15) {
    return cleaned.substring(0, 13) + '...'
  }

  return cleaned
}

// -- Fix D: Number formatting on axes -----------------------------------------
const formatAxisNumber = (value: number, unit?: string): string => {
  if (typeof value !== 'number' || isNaN(value)) return String(value)
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(0)}K`
  if (unit === 'percent') return `${value.toFixed(1)}%`
  return value.toFixed(0)
}

// -- Fix C: Max pie slices constant -------------------------------------------
const MAX_PIE_SLICES = 6

// -- Dynamic chart renderer ---------------------------------------------------
function DynamicChart({ chart }: { chart: ChartResponse }) {
  const data = chart.data as any[]
  if (!data || data.length === 0) {
    return <p className="text-sm text-text-muted text-center py-8">No data available</p>
  }

  const cfg = chart.config ?? {}
  const xLabel = cfg.xLabel ?? chart.x_header
  const yLabel = cfg.yLabel ?? chart.y_header ?? 'Value'
  const seriesKeys: string[] = Array.isArray(cfg.series_keys) ? cfg.series_keys as string[] : []
  const isGrouped = cfg.grouped === true && seriesKeys.length > 0

  // Fix B: Use the actual column name as dataKey (from backend data_key), with 'y' fallback for legacy data
  const dataKey = (cfg.data_key as string) || 'y'
  const xDataKey = (cfg.x_data_key as string) || 'x'
  const yUnit = (cfg.y_unit as string) || 'plain'

  // Fix D: Y-axis formatter aware of unit type
  const fmtYTick = (v: any) => formatAxisNumber(Number(v), yUnit)

  // Composite key for a data point — avoids duplicate-key React warnings
  const rowKey = (row: any, idx: number): string => {
    const vals = Object.values(row)
      .map(v => (v == null ? 'null' : String(v)))
      .join('_')
    return `${idx}_${vals}`
  }

  // ── Fix C: Pie/donut with too many slices → fall back to horizontal bar ──
  if ((chart.chart_type === 'pie' || chart.chart_type === 'donut') && data.length > MAX_PIE_SLICES) {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" barSize={data.length > 20 ? 10 : 16} margin={{ left: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
          <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
          <YAxis dataKey="name" type="category" stroke="#9ca3af" tick={{ fontSize: 10 }} width={75} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" name={yLabel} radius={[0, 5, 5, 0]}>
            {data.map((entry, i) => (
              <Cell key={rowKey(entry, i)} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    )
  }

  // ── Multi-series line (grouped by entity) ────────────────────────────────
  if (isGrouped && chart.chart_type === 'line') {
    const xVals = data.map(d => d.x).filter((v): v is number => typeof v === 'number')
    const yearX = isYearLike(xVals)
    const xDomainProp = yearX || cfg.xDomain ? numDomain(xVals, yearX) : undefined
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
          <XAxis
            dataKey="x"
            stroke="#9ca3af"
            tick={{ fontSize: 11 }}
            tickFormatter={formatXAxisTick}
            {...(xDomainProp ? { type: 'number', domain: xDomainProp, scale: 'linear' } : {})}
          />
          <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
          <Tooltip content={<CustomTooltip />} />
          <Legend iconSize={10} />
          {seriesKeys.map((key, i) => (
            <Line
              key={`series_${key}`}
              type="monotone"
              dataKey={key}
              name={key}
              stroke={CHART_COLORS[i % CHART_COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    )
  }

  // ── Multi-series bar (grouped by entity) ─────────────────────────────────
  if (isGrouped && (chart.chart_type === 'bar' || chart.chart_type === 'stacked_bar')) {
    const isStacked = chart.chart_type === 'stacked_bar'
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barSize={Math.max(4, Math.floor(40 / seriesKeys.length))}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
          <XAxis dataKey="x" stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={formatXAxisTick} />
          <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
          <Tooltip content={<CustomTooltip />} />
          <Legend iconSize={10} />
          {seriesKeys.map((key, i) => (
            <Bar
              key={`series_${key}`}
              dataKey={key}
              name={key}
              fill={CHART_COLORS[i % CHART_COLORS.length]}
              radius={[3, 3, 0, 0]}
              {...(isStacked ? { stackId: 'a' } : {})}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    )
  }

  // ── Single-series charts ─────────────────────────────────────────────────
  switch (chart.chart_type) {
    case 'line': {
      const seen = new Set<unknown>()
      const dedupedData = data.filter(d => {
        if (seen.has(d.x)) return false
        seen.add(d.x)
        return true
      })
      const xVals = dedupedData.map(d => d.x).filter((v): v is number => typeof v === 'number')
      const yearX = isYearLike(xVals)
      const xDomainProp = yearX ? numDomain(xVals, true) : undefined
      const yVals = dedupedData.map(d => d[dataKey]).filter((v): v is number => typeof v === 'number')
      const yDomainProp = yVals.length ? numDomain(yVals, false) : undefined
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dedupedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis
              dataKey="x"
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
              tickFormatter={formatXAxisTick}
              {...(xDomainProp ? { type: 'number', domain: xDomainProp, scale: 'linear' } : {})}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
              tickFormatter={fmtYTick}
              {...(yDomainProp ? { domain: yDomainProp } : {})}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone" dataKey={dataKey} name={yLabel}
              stroke="#6366f1" strokeWidth={2.5}
              dot={{ r: 3, fill: '#6366f1', stroke: 'white', strokeWidth: 2 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )
    }

    case 'bar':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={data.length > 20 ? 10 : 18}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis dataKey="x" stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={formatXAxisTick} interval={data.length > 15 ? Math.floor(data.length / 10) : 0} />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={dataKey} name={yLabel} radius={[5, 5, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={rowKey(entry, i)} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )

    case 'pie':
    case 'donut':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data} cx="50%" cy="50%"
              innerRadius={chart.chart_type === 'donut' ? 55 : 0}
              outerRadius={85}
              paddingAngle={3} dataKey="value" nameKey="name"
            >
              {data.map((entry, i) => (
                <Cell key={rowKey(entry, i)} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend iconSize={10} />
          </PieChart>
        </ResponsiveContainer>
      )

    case 'scatter': {
      const xKey = xDataKey
      const yKey = dataKey
      const xVals = data.map(d => d[xKey]).filter((v): v is number => typeof v === 'number')
      const yVals = data.map(d => d[yKey]).filter((v): v is number => typeof v === 'number')
      const yearX = isYearLike(xVals)
      const yearY = isYearLike(yVals)
      const xDomainProp = xVals.length ? numDomain(xVals, yearX) : undefined
      const yDomainProp = yVals.length ? numDomain(yVals, yearY) : undefined
      return (
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis
              dataKey={xKey}
              name={xLabel}
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
              type="number"
              domain={xDomainProp}
              tickFormatter={formatXAxisTick}
            />
            <YAxis
              dataKey={yKey}
              name={yLabel !== xLabel ? yLabel : `${yLabel} (Y)`}
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
              type="number"
              domain={yDomainProp}
              tickFormatter={fmtYTick}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter name={`${yLabel} vs ${xLabel}`} data={data} fill="#6366f1" />
          </ScatterChart>
        </ResponsiveContainer>
      )
    }

    case 'area': {
      const seen = new Set<unknown>()
      const dedupedData = data.filter(d => {
        if (seen.has(d.x)) return false
        seen.add(d.x)
        return true
      })
      const xVals = dedupedData.map(d => d.x).filter((v): v is number => typeof v === 'number')
      const yearX = isYearLike(xVals)
      const xDomainProp = yearX ? numDomain(xVals, true) : undefined
      const yVals = dedupedData.map(d => d[dataKey]).filter((v): v is number => typeof v === 'number')
      const yDomainProp = yVals.length ? numDomain(yVals, false) : undefined
      return (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={dedupedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis
              dataKey="x"
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
              tickFormatter={formatXAxisTick}
              {...(xDomainProp ? { type: 'number', domain: xDomainProp, scale: 'linear' } : {})}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
              tickFormatter={fmtYTick}
              {...(yDomainProp ? { domain: yDomainProp } : {})}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey={dataKey} name={yLabel}
              stroke="#6366f1" strokeWidth={2}
              fill="#6366f1" fillOpacity={0.15}
              dot={{ r: 2, fill: '#6366f1', stroke: 'white', strokeWidth: 1 }}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )
    }

    case 'horizontal_bar':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" barSize={data.length > 20 ? 10 : 16} margin={{ left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
            <YAxis dataKey="x" type="category" stroke="#9ca3af" tick={{ fontSize: 10 }} width={75} tickFormatter={(v: string) => v.length > 12 ? v.substring(0, 10) + '...' : v} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={dataKey} name={yLabel} radius={[0, 5, 5, 0]}>
              {data.map((entry, i) => (
                <Cell key={rowKey(entry, i)} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )

    case 'stacked_bar':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={data.length > 20 ? 10 : 18}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis dataKey="x" stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={formatXAxisTick} />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={dataKey} name={yLabel} stackId="a" radius={[5, 5, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={rowKey(entry, i)} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )

    default:
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barSize={18}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis dataKey="x" stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={formatXAxisTick} />
            <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} tickFormatter={fmtYTick} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={dataKey} name={yLabel} fill="#818cf8" radius={[5, 5, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )
  }
}

// -- Chart type icon helper ---------------------------------------------------
function chartTypeIcon(type: string) {
  switch (type) {
    case 'line': return <TrendingUp className="w-4 h-4 text-primary" />
    case 'area': return <TrendingUp className="w-4 h-4 text-primary" />
    case 'pie': return <PieIcon className="w-4 h-4 text-primary" />
    case 'donut': return <PieIcon className="w-4 h-4 text-primary" />
    case 'scatter': return <Activity className="w-4 h-4 text-primary" />
    case 'horizontal_bar': return <BarChart3 className="w-4 h-4 text-primary" />
    case 'stacked_bar': return <BarChart3 className="w-4 h-4 text-primary" />
    default: return <BarChart3 className="w-4 h-4 text-primary" />
  }
}

// -- Page ---------------------------------------------------------------------
export default function VisualizePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const jobId = Number(id)

  const [charts, setCharts] = useState<ChartResponse[]>([])
  const [insights, setInsights] = useState<Record<number, string[]>>({})
  const [summary, setSummary] = useState<CleaningSummaryResponse | null>(null)
  const [goal, setGoalState] = useState<GoalResponse | null>(null)
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generatingChart, setGeneratingChart] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const [chartList, sum, goalRes, recs, insightList] = await Promise.all([
          listCharts(jobId),
          getCleaningSummary(jobId).catch(() => null),
          getGoal(jobId).catch(() => null),
          getRecommendations(jobId).catch(() => []),
          listInsights(jobId).catch(() => []),
        ])

        setSummary(sum)
        setGoalState(goalRes)
        setRecommendations(recs as RecommendationItem[])

        // Fetch full chart data for each
        const fullCharts = await Promise.all(
          (chartList as ChartListItem[]).map(c => getChart(jobId, c.id))
        )
        setCharts(fullCharts)

        // Organize insights by chart_id
        const insightMap: Record<number, string[]> = {}
        for (const ins of (insightList as InsightResponse[])) {
          const cid = ins.chart_id ?? 0
          if (!insightMap[cid]) insightMap[cid] = []
          insightMap[cid].push(ins.content)
        }
        setInsights(insightMap)
      } catch {
        setError('Failed to load visualizations')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jobId])

  const handleGenerateInsight = async (chartId: number) => {
    try {
      const res = await generateInsight(chartId)
      setInsights(prev => ({
        ...prev,
        [chartId]: [...(prev[chartId] || []), res.content],
      }))
    } catch { /* silent */ }
  }

  const handleGenerateRecommended = async (rec: RecommendationItem) => {
    setGeneratingChart(true)
    try {
      const newChart = await generateChart(jobId, rec.x_col, rec.y_col ?? undefined, true, rec.group_by ?? undefined)
      const full = await getChart(jobId, newChart.id)
      setCharts(prev => [...prev, full])
      setRecommendations(prev => prev.filter(r => r !== rec))
    } catch { /* silent */ }
    finally { setGeneratingChart(false) }
  }

  const handleExport = async () => {
    try {
      const blob = await exportCSV(jobId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `job-${jobId}-export.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* silent */ }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-text-secondary">Loading visualizations�</p>
      </div>
    )
  }

  if (error && charts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="w-12 h-12 text-error" />
        <p className="text-error font-medium">{error}</p>
      </div>
    )
  }

  const totalCols = summary?.column_metadata ? Object.keys(summary.column_metadata).length : 0
  const totalRows = summary?.row_count_cleaned ?? summary?.row_count_original ?? 0
  const qualityScore = summary?.quality_score

  // Responsive grid slicing
  const topRow = charts.slice(0, 3)
  const midRow = charts.slice(3, 6)
  const bottomRow = charts.slice(6)

  return (
    <div className="p-6 lg:p-8 space-y-6">

      {/* -- Header ---------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {goal?.goal_text || 'Data Visualization'}
          </h1>
          <p className="text-sm text-text-secondary mt-0.5">Interactive data visualization and insights</p>
        </div>
        <div className="flex gap-2.5">
          <Button variant="outline" size="sm" className="gap-2" onClick={handleExport}>
            <Download className="w-4 h-4" /> Export
          </Button>
          <Link href={`/dashboard/project/${id}/insights`}>
            <Button size="sm" className="gap-2">
              <TrendingUp className="w-4 h-4" /> View Insights
            </Button>
          </Link>
        </div>
      </div>

      {/* -- KPI Cards ------------------------------------------------------- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {([
          { label: 'Charts Generated', value: String(charts.length), Icon: BarChart3, ic: 'text-primary', bg: 'bg-primary/10' },
          { label: 'Total Rows', value: totalRows.toLocaleString(), Icon: TrendingUp, ic: 'text-info', bg: 'bg-info/20' },
          { label: 'Total Columns', value: String(totalCols), Icon: Activity, ic: 'text-warning', bg: 'bg-warning/30' },
          { label: 'Quality Score', value: qualityScore != null ? `${qualityScore}%` : '�', Icon: Award, ic: 'text-pink-400', bg: 'bg-pink-100' },
        ] as const).map(({ label, value, Icon, ic, bg }) => (
          <Card key={label}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-text-muted">{label}</span>
                <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${ic}`} />
                </div>
              </div>
              <p className="text-2xl font-bold text-foreground">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* -- Charts ---------------------------------------------------------- */}
      {charts.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <BarChart3 className="w-12 h-12 text-text-muted mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No charts yet</h3>
            <p className="text-text-secondary mb-6">Generate charts from the recommendations below, or go back and run analytics.</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Top row — up to 3 */}
          {topRow.length > 0 && (
            <div className="space-y-4">
              <div className={`grid grid-cols-1 ${topRow.length >= 3 ? 'lg:grid-cols-3' : topRow.length === 2 ? 'lg:grid-cols-2' : ''} gap-6`}>
                {topRow.map((chart) => (
                  <Card key={chart.id} className="overflow-hidden">
                    <CardHeader className="pb-1 flex flex-row items-center justify-between">
                      <CardTitle className="text-base flex items-center gap-2">
                        {chartTypeIcon(chart.chart_type)}
                        {chart.title}
                      </CardTitle>
                      <Badge variant="default">{chart.chart_type}</Badge>
                    </CardHeader>
                    {chart.reason && (
                      <div className="px-6 pb-2">
                        <p className="text-xs italic text-text-muted leading-relaxed">{chart.reason}</p>
                      </div>
                    )}
                    <CardContent className="pb-4">
                      <div className="h-[240px]">
                        <DynamicChart chart={chart} />
                      </div>
                    </CardContent>
                    {!insights[chart.id] ? (
                      <div className="px-6 pb-4">
                        <Button variant="outline" size="sm" className="gap-2 w-full" onClick={() => handleGenerateInsight(chart.id)}>
                          <Sparkles className="w-3.5 h-3.5" /> Generate AI Insight
                        </Button>
                      </div>
                    ) : (
                      <InsightBlock insights={insights[chart.id]} />
                    )}
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Middle row — next 3 */}
          {midRow.length > 0 && (
            <div className={`grid grid-cols-1 ${midRow.length >= 3 ? 'lg:grid-cols-3' : midRow.length === 2 ? 'lg:grid-cols-2' : ''} gap-6`}>
              {midRow.map((chart) => (
                <Card key={chart.id} className="overflow-hidden">
                  <CardHeader className="pb-1 flex flex-row items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      {chartTypeIcon(chart.chart_type)}
                      {chart.title}
                    </CardTitle>
                    <Badge variant="default">{chart.chart_type}</Badge>
                  </CardHeader>
                  {chart.reason && (
                    <div className="px-6 pb-2">
                      <p className="text-xs italic text-text-muted leading-relaxed">{chart.reason}</p>
                    </div>
                  )}
                  <CardContent className="pb-4">
                    <div className="h-[260px]">
                      <DynamicChart chart={chart} />
                    </div>
                  </CardContent>
                  {!insights[chart.id] ? (
                    <div className="px-6 pb-4">
                      <Button variant="outline" size="sm" className="gap-2 w-full" onClick={() => handleGenerateInsight(chart.id)}>
                        <Sparkles className="w-3.5 h-3.5" /> Generate AI Insight
                      </Button>
                    </div>
                  ) : (
                    <InsightBlock insights={insights[chart.id]} />
                  )}
                </Card>
              ))}
            </div>
          )}

          {/* Bottom rows — 2 cols */}
          {bottomRow.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {bottomRow.map((chart) => (
                <Card key={chart.id} className="overflow-hidden">
                  <CardHeader className="pb-1 flex flex-row items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      {chartTypeIcon(chart.chart_type)}
                      {chart.title}
                    </CardTitle>
                    <Badge variant="default">{chart.chart_type}</Badge>
                  </CardHeader>
                  {chart.reason && (
                    <div className="px-6 pb-2">
                      <p className="text-xs italic text-text-muted leading-relaxed">{chart.reason}</p>
                    </div>
                  )}
                  <CardContent className="pb-4">
                    <div className="h-[260px]">
                      <DynamicChart chart={chart} />
                    </div>
                  </CardContent>
                  {!insights[chart.id] ? (
                    <div className="px-6 pb-4">
                      <Button variant="outline" size="sm" className="gap-2 w-full" onClick={() => handleGenerateInsight(chart.id)}>
                        <Sparkles className="w-3.5 h-3.5" /> Generate AI Insight
                      </Button>
                    </div>
                  ) : (
                    <InsightBlock insights={insights[chart.id]} />
                  )}
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* -- Recommendations � generate more charts -------------------------- */}
      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="w-4 h-4 text-primary" />
              Recommended Charts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-muted/60 hover:bg-muted transition-colors">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 text-white text-sm font-bold"
                    style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                  >
                    {rec.chart_type.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {rec.y_col ? `${rec.y_col} by ${rec.x_col}` : `Distribution of ${rec.x_col}`}
                    </p>
                    <p className="text-xs text-text-muted mt-0.5">{rec.chart_type} chart � {Math.round(rec.relevance_score * 100)}% relevance</p>
                    <p className="text-xs text-text-secondary mt-1 line-clamp-2">{rec.reasoning}</p>
                    <Button
                      variant="outline" size="sm"
                      className="mt-2 gap-1.5"
                      disabled={generatingChart}
                      onClick={() => handleGenerateRecommended(rec)}
                    >
                      <Plus className="w-3.5 h-3.5" /> Generate
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
