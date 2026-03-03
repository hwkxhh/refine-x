'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Check, X, ChevronDown, GraduationCap } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

const plans = [
  {
    name: 'Starter',
    tagline: 'For individuals exploring their data',
    priceMonthly: 'Free',
    priceAnnual: 'Free',
    subNote: 'Forever. No credit card required.',
    cta: 'Start Free',
    ctaSub: 'No card. No commitment. No expiry.',
    popular: false,
    variant: 'outline' as const,
    sections: [
      { title: 'Analyses & Files', items: ['5 analyses per month', 'Files up to 5MB', 'CSV and XLSX support', '1 workspace'] },
      { title: 'Cleaning', items: ['Structural cleaning (Phase 1 & 2)', 'Basic value standardization (15 formula types)', 'Missing value prompts'] },
      { title: 'Insights & Visualizations', items: ['3 chart types (Bar, Line, Pie)', 'Basic AI summary (1 insight per analysis)', 'PNG chart export'] },
      { title: 'History & Collaboration', items: ['7-day analysis history', '1 team member (just you)'] },
      { title: 'Support', items: ['Email support', 'Documentation access'] },
    ],
  },
  {
    name: 'Professional',
    tagline: 'For teams making data-driven decisions',
    badge: 'Most Popular',
    priceMonthly: '₹2,499 / $29',
    priceAnnual: '₹1,999 / $23',
    subNote: 'Per workspace · Unlimited users on that workspace',
    cta: 'Start 14-Day Free Trial',
    ctaSub: 'No credit card required for trial',
    popular: true,
    variant: 'primary' as const,
    sections: [
      { title: 'Analyses & Files', items: ['Unlimited analyses', 'Files up to 100MB', 'CSV, XLSX, XLS, TSV support', 'Unlimited workspaces', 'Multi-sheet Excel support'] },
      { title: 'Cleaning', items: ['Full cleaning pipeline (40+ formula types, all 47 HTYPEs)', 'Word-to-number conversion', 'Formula discovery and row-by-row verification', 'Cross-column conditional validation', 'Multi-file structural detection (wide-to-long, merged rows)'] },
      { title: 'Insights & Visualizations', items: ['All 14 chart types', 'Unlimited AI insights per analysis', 'Visualization Studio (custom chart builder)', 'PNG, SVG, PDF, CSV export', 'Embed code for charts'] },
      { title: 'Multi-File Analysis', items: ['Period-over-period comparison', 'Trend and seasonality detection', 'Cohort tracking', 'Multi-file anomaly detection'] },
      { title: 'History & Collaboration', items: ['Unlimited analysis history', 'Full audit trail with Formula IDs', 'Downloadable audit log (CSV)', 'Up to 5 team members', 'Role-based access (Admin, Analyst, Viewer)', 'Issue assignment and commenting', 'Shared insights and datasets'] },
      { title: 'Support', items: ['Priority email support (24-hour response)', 'Live chat support', 'Onboarding call (1 session)'] },
    ],
  },
  {
    name: 'Organization',
    tagline: 'For large teams, enterprises, and institutions',
    priceMonthly: 'Custom',
    priceAnnual: 'Custom',
    subNote: 'Priced per team size and usage. Annual contracts.',
    cta: 'Talk to Sales',
    ctaSub: 'We respond within 1 business day',
    popular: false,
    variant: 'outline' as const,
    sections: [
      { title: 'Everything in Professional, plus:', items: ['Unlimited team members', 'SSO / SAML authentication', 'Custom data retention policy', 'On-premise deployment option', 'Private cloud deployment', 'SLA uptime guarantee (99.9%)'] },
      { title: 'Advanced Features', items: ['API access (REST API)', 'Webhook integration', 'Custom HTYPE definitions (add your own column types)', 'Custom formula rules (define your own business rules)', 'Bulk upload (multiple files in one batch)', 'Scheduled analysis (auto-run on new file upload)'] },
      { title: 'Security & Compliance', items: ['SOC 2 Type II report available', 'Custom DPA (Data Processing Agreement)', 'IP allowlisting', 'Dedicated encryption keys'] },
      { title: 'Support', items: ['Dedicated account manager', 'Onboarding program (3 sessions)', 'Custom training for your team', 'Direct Slack channel with RefineX team', '24/7 emergency support line'] },
    ],
  },
]

const comparisonData: { category: string; rows: [string, string, string, string][] }[] = [
  {
    category: 'ANALYSES & FILES',
    rows: [
      ['Analyses per month', '5', 'Unlimited', 'Unlimited'],
      ['File size limit', '5MB', '100MB', 'Custom'],
      ['File formats', 'CSV, XLSX', 'CSV, XLSX, XLS, TSV', 'All + custom connectors'],
      ['Workspaces', '1', 'Unlimited', 'Unlimited'],
      ['Multi-sheet Excel', '❌', '✅', '✅'],
    ],
  },
  {
    category: 'CLEANING',
    rows: [
      ['Header Types (HTYPE)', '15', 'All 47', 'All 47 + custom'],
      ['Cleaning formulas', '15 types', '40+ types', '40+ types + custom'],
      ['Word-to-number conversion', '❌', '✅', '✅'],
      ['Formula discovery & verification', '❌', '✅', '✅'],
      ['Cross-column validation', '❌', '✅', '✅'],
      ['Structural format detection', '❌', '✅', '✅'],
    ],
  },
  {
    category: 'INSIGHTS',
    rows: [
      ['AI insights per analysis', '1', 'Unlimited', 'Unlimited'],
      ['Chart types', '3', '14', '14'],
      ['Visualization Studio', '❌', '✅', '✅'],
      ['Chart embed code', '❌', '✅', '✅'],
      ['Export formats', 'PNG', 'PNG, SVG, PDF, CSV', 'All'],
    ],
  },
  {
    category: 'MULTI-FILE ANALYSIS',
    rows: [
      ['Period comparison', '❌', '✅', '✅'],
      ['Trend detection', '❌', '✅', '✅'],
      ['Seasonality detection', '❌', '✅', '✅'],
      ['Cohort tracking', '❌', '✅', '✅'],
    ],
  },
  {
    category: 'HISTORY & AUDIT',
    rows: [
      ['History retention', '7 days', 'Unlimited', 'Unlimited'],
      ['Full audit trail', '❌', '✅', '✅'],
      ['Downloadable audit log', '❌', '✅', '✅'],
    ],
  },
  {
    category: 'TEAM',
    rows: [
      ['Team members', '1', '5', 'Unlimited'],
      ['Role-based access', '❌', '✅', '✅'],
      ['Issue assignment', '❌', '✅', '✅'],
      ['SSO / SAML', '❌', '❌', '✅'],
    ],
  },
  {
    category: 'SECURITY',
    rows: [
      ['PII auto-tagging', '✅', '✅', '✅'],
      ['Encrypted at rest', '✅', '✅', '✅'],
      ['Custom data retention', '❌', '✅', '✅'],
      ['On-premise deployment', '❌', '❌', '✅'],
      ['SOC 2 report', '❌', '❌', '✅'],
    ],
  },
  {
    category: 'SUPPORT',
    rows: [
      ['Documentation', '✅', '✅', '✅'],
      ['Email support', '✅', '✅ (24hr)', '✅ (24hr)'],
      ['Live chat', '❌', '✅', '✅'],
      ['Onboarding call', '❌', '1 session', '3 sessions'],
      ['Dedicated account manager', '❌', '❌', '✅'],
      ['24/7 emergency support', '❌', '❌', '✅'],
      ['SLA guarantee', '❌', '❌', '99.9%'],
    ],
  },
]

const faqs = [
  { q: 'Can I really use RefineX for free forever?', a: 'Yes. The Starter plan has no time limit and no credit card requirement. You get 5 analyses per month indefinitely. It\'s enough to explore what RefineX can do and analyze smaller datasets on a regular basis.' },
  { q: 'What counts as one "analysis"?', a: 'One analysis = one file upload processed through the full cleaning pipeline. If you re-run the same file (e.g., after making changes to your source data), that counts as a new analysis. Downloading charts or reviewing history does not count as an analysis.' },
  { q: 'What happens when my 14-day trial ends?', a: 'If you don\'t add a payment method, you automatically move to the Starter free plan. Your existing analyses, datasets, and history are kept for 90 days, after which they\'re archived. You won\'t lose access to past results — you just won\'t be able to run new Professional-tier analyses without upgrading.' },
  { q: 'Can I switch plans anytime?', a: 'Yes. Upgrade, downgrade, or cancel at any time from your account settings. If you upgrade mid-month, you\'re charged a pro-rated amount for the rest of the month. If you downgrade, the change takes effect at the next billing cycle.' },
  { q: 'What\'s the difference between monthly and annual billing?', a: 'Annual billing gives you a 20% discount compared to monthly. You pay for 12 months upfront. Annual plans are not refundable after the first 14 days, so we recommend starting with monthly if you\'re uncertain.' },
  { q: 'Is there a discount for NGOs, schools, or government organizations?', a: 'Yes. We offer a 30% discount for registered non-profit organizations, educational institutions, and government bodies. Contact us with proof of status and we\'ll apply the discount to your account.' },
  { q: 'Can I add more team members beyond the 5 included in Professional?', a: 'Yes. Additional members can be added at ₹499/$6 per member per month on the Professional plan. If you need more than 10 members, the Organization plan is likely more cost-effective — talk to our sales team.' },
  { q: 'Do you offer a free trial for the Organization plan?', a: 'We offer a 30-day pilot for Organization plan evaluation. Contact our sales team to set it up. The pilot includes onboarding support and a custom configuration session.' },
  { q: 'What payment methods do you accept?', a: 'We accept all major credit and debit cards (Visa, Mastercard, Amex, RuPay), UPI, and net banking. For Organization plans, we accept bank transfers and can issue invoices.' },
  { q: 'Is my payment data secure?', a: 'All payments are processed by Stripe (or Razorpay for India). RefineX never stores your card details. Transactions are PCI-DSS compliant.' },
]

export default function PricingPage() {
  const [billing, setBilling] = useState<'monthly' | 'annual'>('monthly')
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <PageLayout>
      {/* Hero Section */}
      <section className="relative py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-center max-w-3xl mx-auto"
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">PRICING</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-6">
              Simple pricing.<br />
              No surprise bills.<br />
              <span className="text-primary">No contracts.</span>
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed">
              Start with the free plan and stay as long as you like. Upgrade when your needs grow. Downgrade or cancel anytime in two clicks.
            </p>

            {/* Billing Toggle */}
            <div className="mt-8 inline-flex items-center gap-2 rounded-2xl border border-border bg-card p-1.5">
              <button
                onClick={() => setBilling('monthly')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${billing === 'monthly' ? 'bg-primary text-white shadow-md' : 'text-text-secondary hover:text-foreground'}`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBilling('annual')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 ${billing === 'annual' ? 'bg-primary text-white shadow-md' : 'text-text-secondary hover:text-foreground'}`}
              >
                Annual
                <span className={`text-xs px-2 py-0.5 rounded-full ${billing === 'annual' ? 'bg-white/20' : 'bg-primary/10 text-primary'}`}>Save 20%</span>
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Plan Cards */}
      <section className="pb-20">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <div className="grid lg:grid-cols-3 gap-6">
            {plans.map((plan, idx) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className={`dashboard-card rounded-2xl p-8 flex flex-col relative ${plan.popular ? 'border-2 border-primary/40 shadow-lg' : ''}`}
              >
                {plan.badge && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-primary text-white text-xs font-bold">
                    {plan.badge}
                  </span>
                )}

                <div className="mb-6">
                  <h2 className="text-xl font-bold text-foreground">{plan.name}</h2>
                  <p className="text-sm text-text-muted mt-1">{plan.tagline}</p>
                </div>

                <div className="mb-6">
                  <p className="text-3xl lg:text-4xl font-bold text-foreground">
                    {billing === 'monthly' ? plan.priceMonthly : plan.priceAnnual}
                  </p>
                  {plan.name !== 'Starter' && plan.name !== 'Organization' && (
                    <p className="text-sm text-text-muted mt-1">per month{billing === 'annual' ? ' (billed annually)' : ''}</p>
                  )}
                  <p className="text-xs text-text-muted mt-1">{plan.subNote}</p>
                </div>

                <Link href={plan.name === 'Organization' ? '/contact' : '/auth/signup'}>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`w-full h-12 rounded-2xl font-bold text-sm transition-all ${
                      plan.popular
                        ? 'card-gradient text-white shadow-lg hover:shadow-xl'
                        : 'border border-border text-foreground hover:border-primary/40 hover:text-primary'
                    }`}
                  >
                    {plan.cta}
                  </motion.button>
                </Link>
                <p className="text-xs text-text-muted text-center mt-2">{plan.ctaSub}</p>

                <div className="mt-8 space-y-5 flex-1">
                  {plan.sections.map((section) => (
                    <div key={section.title}>
                      <p className="text-xs font-bold text-text-muted uppercase tracking-wide mb-2">{section.title}</p>
                      <ul className="space-y-2">
                        {section.items.map((item) => (
                          <li key={item} className="text-sm text-text-secondary flex items-start gap-2">
                            <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1200px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-8 text-center">Compare plans in detail</h2>

            <div className="dashboard-card rounded-2xl p-6 lg:p-8 overflow-x-auto">
              <table className="w-full text-sm min-w-[700px]">
                <thead>
                  <tr className="text-left border-b border-border">
                    <th className="py-3 text-text-muted font-medium">Feature</th>
                    <th className="py-3 text-text-muted font-medium">Starter</th>
                    <th className="py-3 text-primary font-bold">Professional</th>
                    <th className="py-3 text-text-muted font-medium">Organization</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.map((section) => (
                    <>
                      <tr key={section.category}>
                        <td colSpan={4} className="pt-6 pb-2 text-xs font-bold text-primary tracking-wide uppercase">{section.category}</td>
                      </tr>
                      {section.rows.map((row) => (
                        <tr key={row[0]} className="border-b border-border/40">
                          <td className="py-3 font-medium text-foreground">{row[0]}</td>
                          <td className="py-3 text-text-secondary">{row[1]}</td>
                          <td className="py-3 text-text-secondary font-medium">{row[2]}</td>
                          <td className="py-3 text-text-secondary">{row[3]}</td>
                        </tr>
                      ))}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[900px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-8 text-center">Questions about pricing</h2>
          </motion.div>

          <div className="space-y-3">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: index * 0.03 }}
                className="dashboard-card rounded-2xl overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                  className="w-full text-left p-6 flex items-center justify-between gap-4"
                >
                  <span className="font-semibold text-foreground">{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-text-muted shrink-0 transition-transform ${openFaq === index ? 'rotate-180' : ''}`} />
                </button>
                <AnimatePresence>
                  {openFaq === index && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <p className="px-6 pb-6 text-sm text-text-secondary leading-relaxed">{faq.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* NGO / Education Discount Callout */}
      <section className="py-12">
        <div className="mx-auto px-6 lg:px-12 max-w-[900px]">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="dashboard-card rounded-2xl p-8 lg:p-10 border-l-4 border-primary"
          >
            <div className="flex items-start gap-4">
              <GraduationCap className="w-8 h-8 text-primary shrink-0 mt-1" />
              <div>
                <h3 className="text-xl font-bold text-foreground mb-2">Non-profit & Education Discount</h3>
                <p className="text-text-secondary leading-relaxed mb-4">
                  Schools, universities, registered NGOs, and government organizations get 30% off all paid plans. No complicated application. Just contact us with proof of status and we&apos;ll apply it immediately.
                </p>
                <Link href="/contact" className="text-primary font-semibold text-sm hover:underline inline-flex items-center gap-1">
                  Apply for Discount <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="dashboard-card rounded-3xl p-12 lg:p-16 text-center"
          >
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              Not sure which plan is right?<br />
              <span className="text-primary">Start free and decide later.</span>
            </h2>
            <p className="text-lg text-text-secondary mb-8">
              The Starter plan has no time limit. Upgrade only when you need to.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-10 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Start for Free <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="/contact" className="text-primary font-semibold flex items-center justify-center gap-1 px-4 h-14">
                Or talk to us <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
