'use client'

import { useState } from 'react'
import { CreditCard, Calendar, Download, Check } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function BillingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly')

  const plans = [
    {
      name: 'Free',
      price: { monthly: 0, yearly: 0 },
      features: ['5 projects', '1GB storage', '100 rows per file', 'Basic analytics', 'Email support'],
      isCurrent: false
    },
    {
      name: 'Professional',
      price: { monthly: 29, yearly: 290 },
      features: ['Unlimited projects', '50GB storage', '1M rows per file', 'Advanced analytics', 'AI insights', 'Priority support'],
      isCurrent: true,
      popular: true
    },
    {
      name: 'Enterprise',
      price: { monthly: 99, yearly: 990 },
      features: ['Unlimited projects', 'Unlimited storage', 'Unlimited rows', 'Custom AI models', 'API access', '24/7 support', 'SLA guarantee'],
      isCurrent: false
    }
  ]

  const invoices = [
    { id: 'INV-001', date: '2024-01-01', amount: 29, status: 'paid' },
    { id: 'INV-002', date: '2023-12-01', amount: 29, status: 'paid' },
    { id: 'INV-003', date: '2023-11-01', amount: 29, status: 'paid' },
    { id: 'INV-004', date: '2023-10-01', amount: 29, status: 'paid' }
  ]

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Billing</h1>
        <p className="text-text-secondary">Manage your subscription and billing information</p>
      </div>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-2xl font-bold text-foreground mb-1">Professional</h3>
              <p className="text-text-secondary">Billed monthly</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-foreground">$29</div>
              <p className="text-sm text-text-secondary">per month</p>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-muted">
              <p className="text-sm text-text-secondary mb-1">Projects Used</p>
              <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-foreground">12</span>
                <span className="text-sm text-text-secondary mb-1">/ Unlimited</span>
              </div>
              <div className="w-full bg-border rounded-full h-2 mt-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: '15%' }}></div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-muted">
              <p className="text-sm text-text-secondary mb-1">Storage Used</p>
              <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-foreground">8.4</span>
                <span className="text-sm text-text-secondary mb-1">/ 50 GB</span>
              </div>
              <div className="w-full bg-border rounded-full h-2 mt-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: '17%' }}></div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-muted">
              <p className="text-sm text-text-secondary mb-1">API Calls</p>
              <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-foreground">2.3K</span>
                <span className="text-sm text-text-secondary mb-1">/ 10K</span>
              </div>
              <div className="w-full bg-border rounded-full h-2 mt-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: '23%' }}></div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button variant="outline">Cancel Subscription</Button>
            <Button variant="outline">Update Payment Method</Button>
          </div>
        </CardContent>
      </Card>

      {/* Plans Comparison */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Change Plan</CardTitle>
            <div className="flex items-center gap-2 p-1 bg-muted rounded-lg">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  billingPeriod === 'monthly' ? 'bg-card text-foreground shadow-sm' : 'text-text-secondary'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod('yearly')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  billingPeriod === 'yearly' ? 'bg-card text-foreground shadow-sm' : 'text-text-secondary'
                }`}
              >
                Yearly <span className="text-success ml-1">(Save 17%)</span>
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((plan, index) => (
              <div
                key={index}
                className={`p-6 rounded-xl border ${
                  plan.popular ? 'border-primary shadow-lg' : 'border-border'
                } relative`}
              >
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most Popular</Badge>
                )}
                
                <h3 className="text-xl font-bold text-foreground mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-foreground">
                    ${plan.price[billingPeriod]}
                  </span>
                  <span className="text-text-secondary">
                    /{billingPeriod === 'monthly' ? 'mo' : 'yr'}
                  </span>
                </div>

                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                      <span className="text-text-secondary">{feature}</span>
                    </li>
                  ))}
                </ul>

                {plan.isCurrent ? (
                  <Button variant="outline" className="w-full" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button variant={plan.popular ? 'primary' : 'outline'} className="w-full">
                    {index < 1 ? 'Downgrade' : 'Upgrade'}
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Payment Method */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Payment Method
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 border border-border rounded-lg">
            <div className="flex items-center gap-4">
              <div className="w-12 h-8 bg-gradient-to-br from-primary to-accent-coral rounded flex items-center justify-center">
                <CreditCard className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="font-medium text-foreground">•••• •••• •••• 4242</p>
                <p className="text-sm text-text-secondary">Expires 12/2025</p>
              </div>
            </div>
            <Button variant="outline" size="sm">Update</Button>
          </div>

          <Button variant="outline" className="mt-4">
            <CreditCard className="w-4 h-4 mr-2" />
            Add Payment Method
          </Button>
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Billing History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-text-secondary">Invoice</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-text-secondary">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-text-secondary">Amount</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-text-secondary">Status</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-text-secondary">Action</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-b border-border hover:bg-muted/50 transition-colors">
                    <td className="py-4 px-4 font-medium text-foreground">{invoice.id}</td>
                    <td className="py-4 px-4 text-text-secondary">{new Date(invoice.date).toLocaleDateString()}</td>
                    <td className="py-4 px-4 text-foreground">${invoice.amount}</td>
                    <td className="py-4 px-4">
                      <Badge variant="success">Paid</Badge>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <Button variant="ghost" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
