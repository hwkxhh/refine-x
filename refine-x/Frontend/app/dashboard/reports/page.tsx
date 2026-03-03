'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Search, Download, Share2, Trash2, Eye, Filter, Calendar, FileText, TrendingUp, MoreVertical } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'

interface Report {
  id: string
  title: string
  domain: string
  createdAt: string
  status: 'completed' | 'processing' | 'draft'
  thumbnail: string
  metrics: {
    insights: number
    charts: number
    pages: number
  }
}

const mockReports: Report[] = [
  {
    id: '1',
    title: 'Q4 2025 Sales Analysis',
    domain: 'Sales Analytics',
    createdAt: '2026-02-01',
    status: 'completed',
    thumbnail: '/icons8/icons8-bar-chart-50.png',
    metrics: { insights: 12, charts: 8, pages: 15 }
  },
  {
    id: '2',
    title: 'Customer Segmentation Report',
    domain: 'Customer Insights',
    createdAt: '2026-01-28',
    status: 'completed',
    thumbnail: '/icons8/icons8-people-50.png',
    metrics: { insights: 8, charts: 5, pages: 10 }
  },
  {
    id: '3',
    title: 'Regional Performance Analysis',
    domain: 'Operations Data',
    createdAt: '2026-01-25',
    status: 'completed',
    thumbnail: '/icons8/icons8-statistics-50.png',
    metrics: { insights: 15, charts: 10, pages: 20 }
  },
  {
    id: '4',
    title: 'Product Inventory Deep Dive',
    domain: 'Operations Data',
    createdAt: '2026-01-20',
    status: 'processing',
    thumbnail: '/icons8/icons8-process-50.png',
    metrics: { insights: 0, charts: 0, pages: 0 }
  },
  {
    id: '5',
    title: 'Marketing Campaign ROI',
    domain: 'Marketing Analysis',
    createdAt: '2026-01-15',
    status: 'completed',
    thumbnail: '/icons8/icons8-increase-50.png',
    metrics: { insights: 10, charts: 7, pages: 12 }
  },
  {
    id: '6',
    title: 'Financial Summary 2025',
    domain: 'Financial Reporting',
    createdAt: '2026-01-10',
    status: 'draft',
    thumbnail: '/icons8/icons8-positive-dynamic-50.png',
    metrics: { insights: 5, charts: 3, pages: 8 }
  }
]

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing' | 'draft'>('all')
  const [dateFilter, setDateFilter] = useState<'all' | 'week' | 'month' | 'quarter'>('all')
  const [showMenu, setShowMenu] = useState<string | null>(null)

  const filteredReports = mockReports.filter(report => {
    const matchesSearch = report.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         report.domain.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || report.status === statusFilter
    
    let matchesDate = true
    if (dateFilter !== 'all') {
      const reportDate = new Date(report.createdAt)
      const now = new Date()
      const diffTime = Math.abs(now.getTime() - reportDate.getTime())
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (dateFilter === 'week') matchesDate = diffDays <= 7
      else if (dateFilter === 'month') matchesDate = diffDays <= 30
      else if (dateFilter === 'quarter') matchesDate = diffDays <= 90
    }
    
    return matchesSearch && matchesStatus && matchesDate
  })

  const getStatusBadge = (status: Report['status']) => {
    const styles = {
      completed: 'bg-success/20 text-success',
      processing: 'bg-warning/20 text-warning',
      draft: 'bg-gray-200 text-gray-600'
    }
    const labels = {
      completed: 'Completed',
      processing: 'Processing',
      draft: 'Draft'
    }
    return (
      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold text-foreground mb-2">Reports</h1>
        <p className="text-text-secondary">
          View, download, and share your generated analysis reports
        </p>
      </div>

      {/* Filters and Search */}
      <div className="dashboard-card rounded-2xl p-6 mb-6 animate-fade-in-up stagger-2">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="Search reports..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-11 pl-12 pr-4 rounded-xl border border-border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all"
            />
          </div>

          {/* Status Filter */}
          <div className="flex gap-2">
            {(['all', 'completed', 'processing', 'draft'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                  statusFilter === status
                    ? 'bg-primary text-white'
                    : 'bg-white border border-border text-text-secondary hover:border-primary hover:text-primary'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>

          {/* Date Filter */}
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value as any)}
            className="px-4 py-2 rounded-xl border border-border bg-white text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">All Time</option>
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="quarter">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      {filteredReports.length === 0 ? (
        <EmptyState
          icon="file"
          title="No reports found"
          description="Try adjusting your filters or create a new report"
          action={{
            label: "Create New Report",
            onClick: () => window.location.href = '/dashboard/upload'
          }}
        />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredReports.map((report, index) => (
            <div
              key={report.id}
              className="animate-fade-in-up"
              style={{ animationDelay: `${100 + index * 50}ms` }}
            >
              <div className="dashboard-card rounded-2xl overflow-hidden group hover:shadow-lg transition-all duration-200">
                {/* Thumbnail */}
                <div className="h-40 bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center relative overflow-hidden">
                  <Image
                    src={report.thumbnail}
                    alt={report.title}
                    width={80}
                    height={80}
                    className="opacity-30"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                  
                  {/* Quick Actions Overlay */}
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                    <Link href={`/dashboard/project/${report.id}/insights`}>
                      <button className="w-10 h-10 rounded-full bg-white flex items-center justify-center hover:scale-110 transition-transform">
                        <Eye className="w-5 h-5 text-gray-700" />
                      </button>
                    </Link>
                    <button className="w-10 h-10 rounded-full bg-white flex items-center justify-center hover:scale-110 transition-transform">
                      <Download className="w-5 h-5 text-gray-700" />
                    </button>
                    <button className="w-10 h-10 rounded-full bg-white flex items-center justify-center hover:scale-110 transition-transform">
                      <Share2 className="w-5 h-5 text-gray-700" />
                    </button>
                  </div>

                  {/* Status Badge */}
                  <div className="absolute top-3 right-3">
                    {getStatusBadge(report.status)}
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-foreground mb-1 truncate">
                        {report.title}
                      </h3>
                      <p className="text-sm text-text-secondary truncate">
                        {report.domain}
                      </p>
                    </div>
                    <div className="relative">
                      <button
                        onClick={() => setShowMenu(showMenu === report.id ? null : report.id)}
                        className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                      >
                        <MoreVertical className="w-4 h-4 text-text-muted" />
                      </button>
                      
                      {showMenu === report.id && (
                        <div className="absolute right-0 top-8 w-48 bg-white rounded-xl shadow-lg border border-border overflow-hidden z-10">
                          <Link href={`/dashboard/project/${report.id}/insights`}>
                            <button className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted flex items-center gap-3">
                              <Eye className="w-4 h-4" />
                              View Report
                            </button>
                          </Link>
                          <button className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted flex items-center gap-3">
                            <Download className="w-4 h-4" />
                            Download
                          </button>
                          <button className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted flex items-center gap-3">
                            <Share2 className="w-4 h-4" />
                            Share
                          </button>
                          <hr className="border-border" />
                          <button className="w-full px-4 py-2.5 text-left text-sm hover:bg-error/10 text-error flex items-center gap-3">
                            <Trash2 className="w-4 h-4" />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Metrics */}
                  {report.status === 'completed' && (
                    <div className="flex items-center gap-4 text-xs text-text-muted mb-3">
                      <div className="flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5" />
                        <span>{report.metrics.insights} insights</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        <span>{report.metrics.charts} charts</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{report.metrics.pages} pages</span>
                      </div>
                    </div>
                  )}

                  {/* Date */}
                  <div className="text-xs text-text-muted">
                    Created {new Date(report.createdAt).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric', 
                      year: 'numeric' 
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
