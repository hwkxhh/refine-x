export const mockChartData = [
  { month: 'Jan', revenue: 45000, orders: 234, customers: 156 },
  { month: 'Feb', revenue: 52000, orders: 267, customers: 189 },
  { month: 'Mar', revenue: 48000, orders: 245, customers: 172 },
  { month: 'Apr', revenue: 61000, orders: 312, customers: 218 },
  { month: 'May', revenue: 55000, orders: 289, customers: 195 },
  { month: 'Jun', revenue: 67000, orders: 345, customers: 241 },
  { month: 'Jul', revenue: 72000, orders: 378, customers: 267 },
  { month: 'Aug', revenue: 69000, orders: 356, customers: 249 },
  { month: 'Sep', revenue: 58000, orders: 298, customers: 203 },
  { month: 'Oct', revenue: 64000, orders: 328, customers: 229 },
  { month: 'Nov', revenue: 71000, orders: 365, customers: 254 },
  { month: 'Dec', revenue: 78000, orders: 401, customers: 289 }
]

export const mockCategoryData = [
  { name: 'Electronics', value: 385000, percentage: 42 },
  { name: 'Furniture', value: 276000, percentage: 30 },
  { name: 'Supplies', value: 147000, percentage: 16 },
  { name: 'Software', value: 92000, percentage: 10 },
  { name: 'Other', value: 18000, percentage: 2 }
]

export const mockRegionData = [
  { region: 'North America', sales: 425000, growth: 12.5 },
  { region: 'Europe', sales: 312000, growth: 8.3 },
  { region: 'Asia Pacific', sales: 278000, growth: 24.7 },
  { region: 'Latin America', sales: 145000, growth: 15.2 },
  { region: 'Middle East', sales: 98000, growth: 18.9 }
]

export const topProductsData = [
  { name: 'MacBook Pro 14"', revenue: 142000, units: 87, growth: 18 },
  { name: 'Ergonomic Chair', revenue: 98000, units: 245, growth: 31 },
  { name: 'Office Suite Pro', revenue: 76000, units: 312, growth: 42 },
  { name: 'Standing Desk', revenue: 62000, units: 134, growth: 12 },
  { name: 'Wireless Headset', revenue: 48000, units: 523, growth: 27 },
]

export const salespersonData = [
  { name: 'Sarah Chen', revenue: 128000, target: 101200, deals: 34 },
  { name: 'Marcus Reid', revenue: 104000, target: 95000, deals: 28 },
  { name: 'Priya Nair', revenue: 89000, target: 95000, deals: 23 },
  { name: "James O'Brien", revenue: 76000, target: 110000, deals: 19 },
  { name: 'Fatima Al-Zahra', revenue: 71000, target: 105000, deals: 18 },
]

export const goalVsActualData = [
  { metric: 'Revenue', goal: 680000, actual: 740000 },
  { metric: 'Orders', goal: 3200, actual: 3653 },
  { metric: 'Customers', goal: 2650, actual: 2543 },
  { metric: 'Avg Order Value', goal: 190, actual: 203 },
]

export const mockInsights = [
  {
    id: '1',
    type: 'positive',
    title: 'Revenue Peak Detected',
    description: 'December showed the highest revenue of $78,000, representing a 23% increase from the monthly average.',
    confidence: 95
  },
  {
    id: '2',
    type: 'trend',
    title: 'Consistent Growth Pattern',
    description: 'Electronics category maintains 42% market share with steady month-over-month growth of 8-12%.',
    confidence: 88
  },
  {
    id: '3',
    type: 'alert',
    title: 'Regional Opportunity',
    description: 'Asia Pacific region shows strongest growth at 24.7%, suggesting expansion potential.',
    confidence: 92
  },
  {
    id: '4',
    type: 'negative',
    title: 'Lowest Performance Period',
    description: 'March recorded the lowest revenue at $48,000, possibly due to seasonal factors.',
    confidence: 85
  }
]
