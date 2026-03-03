'use client'

import { useState } from 'react'
import { Search, BookOpen, HelpCircle, FileText, Mail, MessageCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function HelpPage() {
  const [activeSection, setActiveSection] = useState('getting-started')

  const faqItems = [
    {
      question: 'How do I upload a CSV file?',
      answer: 'Click on "Upload CSV" in the sidebar or dashboard. You can drag and drop your file or click to browse. We support files up to 100MB in size.'
    },
    {
      question: 'What file formats are supported?',
      answer: 'Currently we support CSV (.csv) files. Support for Excel (.xlsx) and JSON files is coming soon.'
    },
    {
      question: 'How accurate are the AI insights?',
      answer: 'Our AI models are trained on millions of datasets and provide insights with confidence scores. The accuracy typically ranges from 85-95% depending on data quality.'
    },
    {
      question: 'Can I export my analysis results?',
      answer: 'Yes! You can export your analysis as PDF reports, Excel files, or share interactive dashboards with your team.'
    },
    {
      question: 'Is my data secure?',
      answer: 'Absolutely. We use bank-level encryption (AES-256) for data at rest and in transit. Your data is never shared with third parties.'
    },
    {
      question: 'How do I cancel my subscription?',
      answer: 'Go to Settings > Billing and click "Cancel Subscription". Your access will continue until the end of your billing period.'
    }
  ]

  const sections = [
    { id: 'getting-started', name: 'Getting Started', icon: BookOpen },
    { id: 'features', name: 'Features', icon: FileText },
    { id: 'faq', name: 'FAQ', icon: HelpCircle }
  ]

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="grid lg:grid-cols-[240px,1fr] gap-8">
        {/* Sidebar */}
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-foreground mb-4">Documentation</h2>
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg text-left transition-colors ${
                activeSection === section.id
                  ? 'bg-primary text-white'
                  : 'text-text-secondary hover:bg-muted'
              }`}
            >
              <section.icon className="w-4 h-4" />
              {section.name}
            </button>
          ))}
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="Search documentation..."
              className="w-full pl-10 pr-4 py-3 rounded-lg border border-input bg-card focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Getting Started */}
          {activeSection === 'getting-started' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">Getting Started</h1>
                <p className="text-text-secondary">Learn how to use our platform in minutes</p>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>1. Upload Your Data</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-text-secondary">
                    Start by uploading your CSV file. Navigate to the Upload page from the dashboard or sidebar.
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Drag and drop your CSV file into the upload zone</li>
                    <li>Or click to browse and select a file from your computer</li>
                    <li>Files up to 100MB are supported (1M rows for Pro plan)</li>
                  </ul>
                  <div className="p-4 bg-muted rounded-lg mt-4">
                    <p className="text-sm text-text-secondary">
                      <strong className="text-foreground">Tip:</strong> Make sure your CSV has a header row with column names for best results.
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>2. Profile & Clean Your Data</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-text-secondary">
                    After upload, our AI automatically profiles your data to identify:
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Column types (text, number, date, categorical)</li>
                    <li>Missing values and data quality issues</li>
                    <li>Statistical summaries (min, max, mean, distribution)</li>
                    <li>Outliers and anomalies</li>
                  </ul>
                  <p className="text-text-secondary mt-4">
                    Use the Auto-Clean feature to automatically fix common issues, or manually adjust each column.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>3. Detect Domain & Select Analytics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-text-secondary">
                    Our AI analyzes your data structure to detect the domain (Sales, Marketing, Finance, etc.) and recommends relevant analytics.
                  </p>
                  <p className="text-text-secondary">
                    Select the analytics you want to run, and we'll generate insights automatically.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>4. Visualize & Get Insights</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-text-secondary">
                    View interactive charts and AI-generated insights about your data:
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Trend analysis with line and bar charts</li>
                    <li>Distribution analysis with pie charts</li>
                    <li>Key metrics and KPIs</li>
                    <li>AI-powered recommendations</li>
                  </ul>
                  <p className="text-text-secondary mt-4">
                    Export your results as PDF reports or share interactive dashboards with your team.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Features */}
          {activeSection === 'features' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">Features</h1>
                <p className="text-text-secondary">Explore what you can do with our platform</p>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>AI-Powered Data Profiling</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-text-secondary mb-4">
                    Automatically analyze your data structure, types, and quality with our advanced AI engine.
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Automatic type detection (text, number, date, categorical)</li>
                    <li>Missing value analysis</li>
                    <li>Statistical summaries (min, max, mean, median, std dev)</li>
                    <li>Outlier detection</li>
                    <li>Correlation analysis</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Smart Data Cleaning</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-text-secondary mb-4">
                    One-click data cleaning with intelligent suggestions for handling missing values and outliers.
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Auto-fill missing values (mean, median, mode)</li>
                    <li>Remove duplicate rows</li>
                    <li>Standardize formats (dates, currencies, etc.)</li>
                    <li>Handle outliers</li>
                    <li>Before/after comparison</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Interactive Visualizations</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-text-secondary mb-4">
                    Create beautiful, interactive charts that tell your data story.
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Line charts for trends over time</li>
                    <li>Bar charts for comparisons</li>
                    <li>Pie charts for distributions</li>
                    <li>Scatter plots for correlations</li>
                    <li>Export as PNG or SVG</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>AI Insights & Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-text-secondary mb-4">
                    Get actionable insights powered by machine learning models trained on millions of datasets.
                  </p>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    <li>Trend detection (growth, decline, seasonality)</li>
                    <li>Anomaly alerts</li>
                    <li>Business recommendations</li>
                    <li>Confidence scores for each insight</li>
                    <li>Natural language summaries</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          )}

          {/* FAQ */}
          {activeSection === 'faq' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">Frequently Asked Questions</h1>
                <p className="text-text-secondary">Quick answers to common questions</p>
              </div>

              <div className="space-y-4">
                {faqItems.map((item, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">{item.question}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-text-secondary">{item.answer}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Contact Support */}
          <Card>
            <CardHeader>
              <CardTitle>Need More Help?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary mb-4">
                Can't find what you're looking for? Our support team is here to help.
              </p>
              <div className="grid md:grid-cols-2 gap-4">
                <button className="p-4 border border-border rounded-lg hover:border-primary transition-colors text-left">
                  <Mail className="w-6 h-6 text-primary mb-2" />
                  <h4 className="font-medium text-foreground mb-1">Email Support</h4>
                  <p className="text-sm text-text-secondary">support@example.com</p>
                </button>
                <button className="p-4 border border-border rounded-lg hover:border-primary transition-colors text-left">
                  <MessageCircle className="w-6 h-6 text-primary mb-2" />
                  <h4 className="font-medium text-foreground mb-1">Live Chat</h4>
                  <p className="text-sm text-text-secondary">Available 9am - 5pm EST</p>
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
