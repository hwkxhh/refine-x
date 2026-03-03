export interface Project {
  id: string
  name: string
  description: string
  status: 'active' | 'completed' | 'archived'
  rows: number
  columns: number
  lastModified: string
  createdAt: string
  domain: string
}

export const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Q4 Sales Analysis',
    description: 'Quarterly sales performance by region',
    status: 'active',
    rows: 12543,
    columns: 18,
    lastModified: '2026-02-04T10:30:00',
    createdAt: '2026-01-15T09:00:00',
    domain: 'Sales'
  },
  {
    id: '2',
    name: 'Customer Churn Study',
    description: 'Identifying patterns in customer retention',
    status: 'completed',
    rows: 8932,
    columns: 24,
    lastModified: '2026-01-28T14:22:00',
    createdAt: '2026-01-10T11:30:00',
    domain: 'Customer Analytics'
  },
  {
    id: '3',
    name: 'Inventory Optimization',
    description: 'Stock levels and turnover analysis',
    status: 'active',
    rows: 3421,
    columns: 15,
    lastModified: '2026-02-03T16:45:00',
    createdAt: '2026-01-22T08:15:00',
    domain: 'Operations'
  },
  {
    id: '4',
    name: 'Marketing Campaign ROI',
    description: 'Performance metrics across channels',
    status: 'completed',
    rows: 5678,
    columns: 21,
    lastModified: '2026-01-30T13:10:00',
    createdAt: '2026-01-05T10:00:00',
    domain: 'Marketing'
  },
  {
    id: '5',
    name: 'Employee Satisfaction Survey',
    description: 'Annual survey results analysis',
    status: 'archived',
    rows: 1250,
    columns: 32,
    lastModified: '2025-12-15T09:20:00',
    createdAt: '2025-12-01T10:00:00',
    domain: 'HR'
  }
]

export const mockTemplates = [
  {
    id: 't1',
    name: 'Sales Performance Template',
    description: 'Pre-configured analytics for sales data',
    category: 'Sales',
    uses: 1243
  },
  {
    id: 't2',
    name: 'Customer Analytics Template',
    description: 'Track customer behavior and trends',
    category: 'Customer Analytics',
    uses: 892
  },
  {
    id: 't3',
    name: 'Financial Report Template',
    description: 'Financial metrics and KPI tracking',
    category: 'Finance',
    uses: 2156
  },
  {
    id: 't4',
    name: 'Marketing Campaign Template',
    description: 'Campaign performance and ROI analysis',
    category: 'Marketing',
    uses: 745
  }
]
