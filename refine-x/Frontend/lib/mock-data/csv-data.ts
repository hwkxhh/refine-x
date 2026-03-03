export const mockCSVData = {
  headers: ['Product', 'Category', 'Region', 'Sales', 'Quantity', 'Date', 'Customer_Segment', 'Revenue'],
  rows: [
    ['Laptop Pro', 'Electronics', 'North', '45000', '15', '2026-01-15', 'Enterprise', '67500'],
    ['Office Chair', 'Furniture', 'South', '12000', '48', '2026-01-16', 'SMB', '14400'],
    ['Wireless Mouse', 'Electronics', 'East', '3500', '120', '2026-01-17', 'Consumer', '4200'],
    ['Standing Desk', 'Furniture', 'West', '28000', '22', '2026-01-18', 'Enterprise', '33600'],
    ['USB-C Hub', 'Electronics', 'North', '5600', '85', '2026-01-19', 'SMB', '6720'],
    ['Monitor 27"', 'Electronics', 'South', '32000', '40', '2026-01-20', 'Enterprise', '48000'],
    ['Desk Lamp', 'Furniture', 'East', '4500', '95', '2026-01-21', 'Consumer', '5400'],
    ['Keyboard Mechanical', 'Electronics', 'West', '8900', '67', '2026-01-22', 'Consumer', '10680'],
    ['Conference Table', 'Furniture', 'North', '52000', '8', '2026-01-23', 'Enterprise', '62400'],
    ['Webcam HD', 'Electronics', 'South', '6700', '78', '2026-01-24', 'SMB', '8040'],
  ],
  stats: {
    totalRows: 12543,
    totalColumns: 8,
    missingValues: 127,
    duplicates: 23,
    fileSize: 2847563
  }
}

export const mockColumnProfiles = [
  {
    name: 'Product',
    type: 'Text',
    uniqueValues: 145,
    missingPercent: 0,
    quality: 'Excellent',
    samples: ['Laptop Pro', 'Office Chair', 'Wireless Mouse']
  },
  {
    name: 'Category',
    type: 'Category',
    uniqueValues: 5,
    missingPercent: 0.5,
    quality: 'Good',
    samples: ['Electronics', 'Furniture', 'Supplies']
  },
  {
    name: 'Region',
    type: 'Category',
    uniqueValues: 4,
    missingPercent: 0,
    quality: 'Excellent',
    samples: ['North', 'South', 'East', 'West']
  },
  {
    name: 'Sales',
    type: 'Numeric',
    uniqueValues: 8932,
    missingPercent: 1.2,
    quality: 'Good',
    samples: ['45000', '12000', '3500']
  },
  {
    name: 'Quantity',
    type: 'Numeric',
    uniqueValues: 542,
    missingPercent: 0.8,
    quality: 'Good',
    samples: ['15', '48', '120']
  },
  {
    name: 'Date',
    type: 'Date',
    uniqueValues: 365,
    missingPercent: 0,
    quality: 'Excellent',
    samples: ['2026-01-15', '2026-01-16', '2026-01-17']
  },
  {
    name: 'Customer_Segment',
    type: 'Category',
    uniqueValues: 3,
    missingPercent: 2.3,
    quality: 'Fair',
    samples: ['Enterprise', 'SMB', 'Consumer']
  },
  {
    name: 'Revenue',
    type: 'Numeric',
    uniqueValues: 9234,
    missingPercent: 1.2,
    quality: 'Good',
    samples: ['67500', '14400', '4200']
  }
]
