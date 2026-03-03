'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { motion } from 'framer-motion'
import { ArrowRight, Lock, Shield, Tag, Trash2, Clock, Building, UserPlus, Flag, MessageCircle, Share2, Eye, Check, X } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

const featureNavItems = [
  { label: 'Data Cleaning', anchor: '#data-cleaning' },
  { label: 'AI Insights', anchor: '#ai-insights' },
  { label: 'Visualizations', anchor: '#visualizations' },
  { label: 'Formula Intelligence', anchor: '#formula-intelligence' },
  { label: 'Data Quality Score', anchor: '#data-quality-score' },
  { label: 'History & Audit', anchor: '#history-audit' },
  { label: 'Team Collaboration', anchor: '#team-collaboration' },
  { label: 'Multi-File Analysis', anchor: '#multi-file' },
  { label: 'Security & Privacy', anchor: '#security-privacy' },
]

export default function FeaturesPage() {
  const [activeNav, setActiveNav] = useState('#data-cleaning')

  return (
    <PageLayout>
      {/* Hero Section */}
      <section className="relative py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-3xl"
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">WHAT REFINEX DOES</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-6">
              Every feature built{' '}
              <span className="text-primary">for one purpose:</span>{' '}
              turning messy data into clear decisions.
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed max-w-2xl mb-8">
              RefineX is not a dashboard builder or a reporting tool. It is a complete data intelligence platform — from the moment your file is uploaded to the moment you understand what your data is telling you.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-8 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Start for Free — No Credit Card
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="#" className="text-primary font-semibold flex items-center gap-1 px-4 h-14">
                See a live demo →
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Feature Navigation - Sticky sub-nav */}
      <div className="sticky top-20 z-40 bg-white/90 backdrop-blur-md border-y border-border">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <div className="flex gap-1 overflow-x-auto py-3 scrollbar-hide">
            {featureNavItems.map((item) => (
              <a
                key={item.anchor}
                href={item.anchor}
                onClick={() => setActiveNav(item.anchor)}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  activeNav === item.anchor
                    ? 'bg-primary text-white'
                    : 'bg-muted/50 text-text-secondary hover:text-foreground hover:bg-muted'
                }`}
              >
                {item.label}
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* FEATURE 1: DATA CLEANING */}
      <section id="data-cleaning" className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 01 — DATA CLEANING</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              40+ cleaning formulas.<br />Zero guesswork.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-4">
              Every column type has its own set of documented rules. Names are cleaned differently from dates. Dates are cleaned differently from phone numbers. Nothing is treated generically.
            </p>
            <p className="text-text-secondary max-w-3xl mb-12 leading-relaxed">
              RefineX identifies the type of data in every column — whether it&apos;s a name, a date, a phone number, a currency amount, a score, a status, or one of 40+ other types — and applies the appropriate set of cleaning formulas automatically. The result is a dataset that&apos;s consistent, structured, and ready for analysis. Every change is logged. Every decision is explained. And anything RefineX isn&apos;t sure about, it asks you.
            </p>
          </motion.div>

          {/* 4-Phase Pipeline */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {[
              {
                phase: 'Phase 01',
                title: 'Structural Cleanup',
                description: 'Before touching a single value, RefineX fixes the structure of your file. Duplicate rows removed. Summary/totals rows separated. Merged Excel cells filled. Empty rows eliminated. Column names normalized.',
                tags: ['Removes TOTAL rows', 'Fills merged cells', 'Strips BOM characters'],
              },
              {
                phase: 'Phase 02',
                title: 'Column Classification',
                description: 'Every column is assigned a Header Type — one of 47 categories including Name, Date, Phone, Amount, Score, Status, Category, and more. Classification uses column name keywords, value pattern matching, and data type analysis. AI is only used as a last resort.',
                tags: ['47 Header Types', 'Pattern-based detection', 'AI fallback for ambiguous columns'],
              },
              {
                phase: 'Phase 03',
                title: 'Value Standardization',
                description: 'Within each column, every value is cleaned against its Header Type\'s formula set. Names get Title Case. Dates get unified to a single format. Phone numbers get type-converted. Currencies get symbols stripped. Written numbers ("eleven") get converted to digits.',
                tags: ['"elven" → 11', '"01/02/24" → 2024-02-01', '"Fule" → "Fuel"'],
              },
              {
                phase: 'Phase 04',
                title: 'Missing Value Resolution',
                description: 'For each null cell, RefineX evaluates whether it can predict the value from other data (like calculating age from date of birth), whether it should ask you, or whether it should mark it as intentionally absent. It never fills a value it cannot justify.',
                tags: ['Derives age from DOB', 'Calculates totals from components', 'Prompts for unpredictable values'],
              },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="dashboard-card dashboard-card-hover rounded-2xl p-7"
              >
                <p className="text-xs font-bold text-primary mb-2">{item.phase}</p>
                <h3 className="text-xl font-bold text-foreground mb-3">{item.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed mb-4">{item.description}</p>
                <div className="flex flex-wrap gap-2">
                  {item.tags.map((tag) => (
                    <span key={tag} className="px-3 py-1 rounded-full bg-primary/5 text-primary text-xs font-medium">
                      {tag}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Formula Rulebook Callout */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="dashboard-card rounded-2xl p-7 border-l-4 border-primary"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">📋</span>
              <div>
                <h3 className="text-lg font-bold text-foreground mb-2">The Formula Rulebook</h3>
                <p className="text-sm text-text-secondary leading-relaxed mb-3">
                  Every cleaning formula RefineX applies is publicly documented. No black boxes. No hidden logic. You can read exactly what will happen to your data before it happens.
                </p>
                <Link href="#" className="text-primary font-semibold text-sm hover:underline">
                  Read the Complete Rulebook →
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FEATURE 2: AI INSIGHTS */}
      <section id="ai-insights" className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 02 — AI INSIGHTS</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              The AI reads your data<br />so you don&apos;t have to wade through<br />400 rows to find what matters.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-4">
              After cleaning, RefineX AI generates plain-language observations about your data — specific, actionable, and always tied to the goal you defined.
            </p>
            <p className="text-text-secondary max-w-3xl mb-12 leading-relaxed">
              This is where RefineX earns its place. Not in replacing you, but in doing the part of analysis that is tedious and time-consuming: reading through hundreds of rows and identifying what deserves your attention. The AI does not make decisions for you. It tells you what it found. You decide what to do with it.
            </p>
          </motion.div>

          {/* What the AI Does vs Doesn't */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="dashboard-card rounded-2xl p-7"
            >
              <h3 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Check className="w-4 h-4 text-primary" />
                </div>
                The AI Does
              </h3>
              <ul className="space-y-3 text-sm text-text-secondary">
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Generates natural language summaries of your data</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Identifies anomalies that don&apos;t fit known patterns</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Narrates why a data point is unusual</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Recommends which columns to visualize for your goal</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Answers plain-language questions about your dataset</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Tags free-text notes with sentiment and keywords</li>
              </ul>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="dashboard-card rounded-2xl p-7"
            >
              <h3 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-error/10 flex items-center justify-center">
                  <X className="w-4 h-4 text-error" />
                </div>
                The AI Doesn&apos;t
              </h3>
              <ul className="space-y-3 text-sm text-text-secondary">
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-error shrink-0" />Clean your data (logic handles that)</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-error shrink-0" />Auto-delete or modify values without your approval</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-error shrink-0" />Design charts or choose visualization types</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-error shrink-0" />Make decisions that belong to you</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-error shrink-0" />Invent data or fill values it cannot justify</li>
                <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-error shrink-0" />Access your data outside the analysis session</li>
              </ul>
            </motion.div>
          </div>

          {/* Insight Types */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { badge: 'ANOMALY', color: 'bg-error/10 text-error', example: '"Row 416 has an Order Count of 4,470 — equal to the sum of all other rows. This is almost certainly a totals row included in the data body by mistake."' },
              { badge: 'TREND', color: 'bg-primary/10 text-primary', example: '"Student admissions have grown 14% year-over-year for three consecutive years, with the sharpest growth occurring in Q1 each year."' },
              { badge: 'PERFORMANCE', color: 'bg-success/10 text-green-700', example: '"Manikonda store delivers 42% more orders per rider than the network average. Attapur is 23% below average and may benefit from staffing review."' },
              { badge: 'DATA QUALITY', color: 'bg-info/10 text-blue-700', example: '"All three payment formulas (Fuel, Payment on Orders, Total Earning) were verified across 415 rows. No calculation errors found."' },
              { badge: 'OPPORTUNITY', color: 'bg-warning/10 text-amber-700', example: '"You now have 6 months of data in the same format. RefineX can run a seasonality analysis — this typically reveals 2–3 actionable patterns."' },
              { badge: 'WARNING', color: 'bg-error/10 text-red-700', example: '"The summary sheet reports 567 riders but the payment sheet contains only 415. 152 records are unaccounted for. Investigate before using this data for payroll."' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="dashboard-card rounded-2xl p-6"
              >
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold mb-3 ${item.color}`}>
                  {item.badge}
                </span>
                <p className="text-sm text-text-secondary leading-relaxed italic">{item.example}</p>
              </motion.div>
            ))}
          </div>

          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-text-secondary text-sm mt-8 dashboard-card rounded-xl p-5 border-l-4 border-primary"
          >
            Insights are generated after every analysis — automatically. You don&apos;t need to ask. But you can ask follow-up questions in plain language and RefineX will answer from your data.
          </motion.p>
        </div>
      </section>

      {/* FEATURE 3: VISUALIZATIONS */}
      <section id="visualizations" className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 03 — VISUALIZATIONS</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              Charts that were chosen<br />for your data, not picked<br />from a template.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-4">
              RefineX selects the most appropriate chart type based on what your columns contain and what your goal is. You can always override, customize, or build your own from scratch.
            </p>
            <p className="text-text-secondary max-w-3xl mb-12 leading-relaxed">
              Generic BI tools give you a chart builder and leave you to figure out what chart makes sense. RefineX starts with a recommendation — then lets you take over. When you define a goal like &quot;track monthly sales trends,&quot; RefineX knows to prioritize time-series line charts over pie charts.
            </p>
          </motion.div>

          {/* Chart Types Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
            {[
              { chart: 'Bar Chart', best: 'Comparing values across categories' },
              { chart: 'Line Chart', best: 'Trends over time' },
              { chart: 'Scatter Plot', best: 'Correlation between two numeric columns' },
              { chart: 'Histogram', best: 'Distribution of values' },
              { chart: 'Pie / Donut Chart', best: 'Part-of-whole composition' },
              { chart: 'Stacked Bar', best: 'Composition change over time' },
              { chart: 'Area Chart', best: 'Volume trends over time' },
              { chart: 'Heatmap', best: 'Patterns across two dimensions' },
              { chart: 'Treemap', best: 'Hierarchical data composition' },
              { chart: 'Funnel Chart', best: 'Stage-by-stage drop-off' },
              { chart: 'Radar / Spider', best: 'Multi-variable comparison' },
              { chart: 'Box Plot', best: 'Statistical spread and outliers' },
              { chart: 'Bubble Chart', best: 'Three-variable relationship' },
              { chart: 'Waterfall Chart', best: 'Incremental increases/decreases' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="dashboard-card rounded-xl p-4 hover:border-primary/20 transition-all"
              >
                <p className="text-sm font-bold text-foreground mb-1">{item.chart}</p>
                <p className="text-xs text-text-secondary">{item.best}</p>
              </motion.div>
            ))}
          </div>

          {/* Customization & Export */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="dashboard-card rounded-2xl p-7">
              <h3 className="text-lg font-bold text-foreground mb-4">Customization Options</h3>
              <ul className="space-y-2.5 text-sm text-text-secondary">
                {['Title and subtitle text', 'X-axis and Y-axis labels', 'Color scheme (from palette or custom hex)', 'Data labels on/off', 'Legend position', 'Gridlines on/off', 'Reference line (add a target/benchmark line)', 'Annotations (add a text note to any data point)', 'Filter by column value'].map((item) => (
                  <li key={item} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="dashboard-card rounded-2xl p-7">
              <h3 className="text-lg font-bold text-foreground mb-4">Export Options</h3>
              <div className="space-y-3">
                {[
                  { format: 'PNG', desc: 'High resolution, for presentations' },
                  { format: 'SVG', desc: 'Vector, for print or web' },
                  { format: 'PDF', desc: 'For reports' },
                  { format: 'CSV', desc: 'The underlying chart data' },
                  { format: 'Embed code', desc: 'For websites (Pro plan)' },
                ].map((item) => (
                  <div key={item.format} className="flex items-center gap-3 p-3 rounded-xl bg-muted/30">
                    <span className="px-2 py-1 rounded-lg bg-primary/10 text-primary text-xs font-bold">{item.format}</span>
                    <span className="text-sm text-text-secondary">{item.desc}</span>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-6 border-t border-border">
                <h4 className="text-base font-bold text-foreground mb-2">The Visualization Studio</h4>
                <p className="text-sm text-text-secondary leading-relaxed mb-3">
                  Beyond automatic charts, the Visualization Studio lets you build any chart from scratch using your cleaned data. Pick your dataset. Pick your columns. Pick your chart type. RefineX renders it instantly.
                </p>
                <Link href="#" className="text-primary font-semibold text-sm hover:underline">
                  Open Visualization Studio →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURE 4: FORMULA INTELLIGENCE */}
      <section id="formula-intelligence" className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 04 — FORMULA INTELLIGENCE</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              If your data has math in it,<br />RefineX checks the math.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-4">
              Calculated columns, derived values, and formula-based fields are detected automatically and verified row by row. Every mismatch is flagged before it becomes a payroll error or a wrong board report.
            </p>
            <p className="text-text-secondary max-w-3xl mb-12 leading-relaxed">
              Most spreadsheets contain columns that are derived from other columns. Total = Quantity × Price. Fuel = Distance × 3. Pass/Fail = Score ≥ 40%. These formulas are usually invisible — no one documents them, and no tool verifies them. A single broken formula can silently corrupt an entire dataset for months. RefineX detects these relationships automatically, confirms the formula with you, and then checks every row.
            </p>
          </motion.div>

          {/* Formula Examples */}
          <div className="space-y-4 mb-12">
            {[
              { scenario: 'Fuel = Distance × ₹3/km — RefineX detects and verifies this formula across all 415 rows.', badge: '✅ 415/415 rows verified. No errors.', badgeColor: 'bg-success/10 text-green-700' },
              { scenario: 'Total Earnings = Payment + Fuel — RefineX detects and verifies.', badge: '⚠️ 2 rows have mismatches. Flagged for review.', badgeColor: 'bg-warning/10 text-amber-700' },
              { scenario: 'Age and Date of Birth both exist — RefineX checks if age is consistent with DOB.', badge: '⚠️ 3 rows show age inconsistent with DOB by more than 1 year.', badgeColor: 'bg-warning/10 text-amber-700' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="dashboard-card rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <p className="text-sm text-text-secondary leading-relaxed">{item.scenario}</p>
                <span className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap ${item.badgeColor}`}>
                  {item.badge}
                </span>
              </motion.div>
            ))}
          </div>

          {/* Cross-column Validation */}
          <div className="dashboard-card rounded-2xl p-7 border-l-4 border-primary">
            <h3 className="text-lg font-bold text-foreground mb-3">Cross-column Conditional Validation</h3>
            <p className="text-sm text-text-secondary leading-relaxed mb-4">
              Formula intelligence goes beyond math. RefineX also validates logical conditions across columns:
            </p>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />If Status = &quot;Discharged&quot; → Discharge Date must not be empty</li>
              <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />If Score = 72 and Pass/Fail = &quot;Fail&quot; → Flagged (threshold is 40)</li>
              <li className="flex items-start gap-2"><span className="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />If Country = &quot;India&quot; and Phone starts with +1 → Flagged</li>
            </ul>
            <p className="text-sm text-text-secondary mt-4">These rules catch data entry errors that formulas alone miss.</p>
          </div>
        </div>
      </section>

      {/* FEATURE 5: DATA QUALITY SCORE */}
      <section id="data-quality-score" className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 05 — DATA QUALITY SCORE</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              One number that tells you<br />how much to trust your data.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-12">
              Every analysis produces a Data Quality Score — a 0–100 rating per column and for the dataset as a whole. Based on five dimensions used by professional data governance teams worldwide.
            </p>
          </motion.div>

          {/* Five Dimensions */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-12">
            {[
              { name: 'Completeness', weight: '30%', desc: 'What percentage of cells have actual data? A column that\'s 60% empty scores low here.', formula: 'Non-null values ÷ Total rows × 100' },
              { name: 'Validity', weight: '25%', desc: 'What percentage of values pass their format and range rules?', formula: 'Values passing rules ÷ Total values × 100' },
              { name: 'Uniqueness', weight: '20%', desc: 'For ID columns: are they actually unique? For others: how many suspicious duplicates?', formula: 'Unique values ÷ Total values × 100' },
              { name: 'Consistency', weight: '15%', desc: 'Do cross-column rules hold? Do formulas verify? Are date sequences logical?', formula: '' },
              { name: 'Accuracy', weight: '10%', desc: 'For columns with known reference lists — what percentage match the reference?', formula: '' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="dashboard-card rounded-2xl p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-foreground">{item.name}</h4>
                  <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-bold">{item.weight}</span>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed mb-2">{item.desc}</p>
                {item.formula && (
                  <p className="text-xs text-text-muted font-mono bg-muted/30 rounded-lg px-3 py-1.5">{item.formula}</p>
                )}
              </motion.div>
            ))}
          </div>

          {/* Score Interpretation */}
          <div className="dashboard-card rounded-2xl p-7 mb-8">
            <h3 className="text-lg font-bold text-foreground mb-4">Score Interpretation</h3>
            <div className="space-y-3">
              {[
                { range: '90–100', label: '🟢 Excellent', meaning: 'Ready for analysis. Minimal intervention needed.' },
                { range: '75–89', label: '🟡 Good', meaning: 'Minor issues found and resolved. Solid data.' },
                { range: '60–74', label: '🟠 Fair', meaning: 'Notable quality issues. Review before acting on findings.' },
                { range: '40–59', label: '🔴 Poor', meaning: 'Significant problems. Use insights with caution.' },
                { range: '0–39', label: '⛔ Critical', meaning: 'Major structural issues. Not ready for analysis.' },
              ].map((item) => (
                <div key={item.range} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 p-3 rounded-xl bg-muted/20">
                  <span className="text-sm font-bold text-foreground w-20">{item.range}</span>
                  <span className="text-sm font-semibold w-32">{item.label}</span>
                  <span className="text-sm text-text-secondary">{item.meaning}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sample DQS Report */}
          <div className="dashboard-card rounded-2xl p-7 mb-8">
            <h3 className="text-lg font-bold text-foreground mb-4">Sample Column Report Card</h3>
            <div className="font-mono text-sm bg-[#0F0F0F] text-gray-300 rounded-xl p-6 leading-relaxed">
              <p className="text-white font-bold mb-2">Column: rider_email</p>
              <p>  Completeness:   94%  <span className="text-gray-500">(12 missing values)</span></p>
              <p>  Validity:       88%  <span className="text-gray-500">(18 invalid email formats)</span></p>
              <p>  Uniqueness:    99.7% <span className="text-gray-500">(2 duplicate emails found)</span></p>
              <p>  Consistency:   100%  <span className="text-gray-500">(no cross-column conflicts)</span></p>
              <p>  Accuracy:       91%  <span className="text-gray-500">(2 flagged as disposable email domains)</span></p>
              <p className="mt-2 border-t border-gray-700 pt-2">  Column Score:  <span className="text-amber-400 font-bold">74.4 / 100   🟠 Fair</span></p>
            </div>
          </div>

          {/* Trend Over Time */}
          <div className="dashboard-card rounded-2xl p-7">
            <h3 className="text-lg font-bold text-foreground mb-3">Trend Over Time</h3>
            <p className="text-sm text-text-secondary leading-relaxed mb-4">
              If you upload the same dataset format regularly (weekly, monthly), RefineX tracks your Data Quality Score over time. Watch your team&apos;s data hygiene improve. Spot when a new data entry process introduced new problems.
            </p>
            {/* Simple visual representation of DQS trend */}
            <div className="flex items-end gap-3 h-24">
              {[61, 78, 84, 88, 90, 93].map((score, index) => (
                <div key={index} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs font-bold text-primary">{score}</span>
                  <motion.div
                    initial={{ height: 0 }}
                    whileInView={{ height: `${(score / 100) * 80}px` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                    className="w-full rounded-t-lg"
                    style={{ background: 'linear-gradient(180deg, #6366f1 0%, #a5b4fc 100%)' }}
                  />
                  <span className="text-xs text-text-muted">M{index + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FEATURE 6: HISTORY & AUDIT TRAIL */}
      <section id="history-audit" className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 06 — HISTORY & AUDIT TRAIL</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              Every change. Every decision.<br />Every click. Permanently logged.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-4">
              RefineX maintains a complete, immutable audit trail of every transformation applied to your data. Know exactly what changed, who changed it, when, and why.
            </p>
            <p className="text-text-secondary max-w-3xl mb-12 leading-relaxed">
              In professional data environments, auditability is not optional. When a number in a report is questioned, you need to be able to show every step taken to arrive at it. RefineX creates that trail automatically. No setup required.
            </p>
          </motion.div>

          {/* What Gets Logged */}
          <div className="dashboard-card rounded-2xl p-7 mb-8 overflow-x-auto">
            <h3 className="text-lg font-bold text-foreground mb-4">What Gets Logged</h3>
            <table className="w-full text-sm min-w-[600px]">
              <thead>
                <tr className="text-left text-text-muted border-b border-border">
                  <th className="py-3 pr-4">Event Type</th>
                  <th className="py-3">Example Log Entry</th>
                </tr>
              </thead>
              <tbody className="text-text-secondary">
                {[
                  ['File uploaded', 'Raw_Data.xlsx uploaded by Aarav Sharma · 22 Feb 2026, 14:30'],
                  ['Auto-fix applied', 'Column "Fule" renamed to "Fuel" — spelling correction · Auto'],
                  ['Manual decision', 'Title Case applied to 255 rider names · By: Aarav Sharma'],
                  ['Issue flagged', 'Cross-sheet discrepancy flagged: 152 riders unaccounted for'],
                  ['Issue resolved', 'Discrepancy marked as "different time periods" by Priya Mehta'],
                  ['Insight generated', '5 insights generated from cleaned dataset · AI'],
                  ['Chart downloaded', '"Orders by Store" exported as PNG · By: Aarav Sharma'],
                  ['Dataset shared', 'Dataset shared with: ravi@company.com · Viewer access'],
                  ['Issue undone', 'Auto-fix undone: Column rename reverted by user'],
                ].map(([type, entry]) => (
                  <tr key={type} className="border-b border-border/60">
                    <td className="py-3 pr-4 font-medium text-foreground whitespace-nowrap">{type}</td>
                    <td className="py-3 text-text-secondary">{entry}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="dashboard-card rounded-2xl p-7">
            <p className="text-sm text-text-secondary leading-relaxed mb-3">
              The full audit log can be exported as a CSV at any time from the History tab. Use it for compliance reporting, team reviews, or just peace of mind.
            </p>
            <Link href="#" className="text-primary font-semibold text-sm hover:underline">
              Download Sample Audit Log (CSV) →
            </Link>
          </div>
        </div>
      </section>

      {/* FEATURE 7: TEAM COLLABORATION */}
      <section id="team-collaboration" className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 07 — TEAM COLLABORATION</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              Data cleaning is a team sport.<br />RefineX makes it one.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-12">
              Invite teammates. Assign issues for review. See who changed what. Share datasets and insights instantly. Everyone on your team sees the same clean, verified truth.
            </p>
          </motion.div>

          {/* Collaboration Features */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {[
              { icon: <UserPlus className="w-5 h-5 text-primary" />, title: 'Invite teammates in seconds', body: 'Add team members via email. Choose their role — Admin, Analyst, or Viewer. They get access immediately.' },
              { icon: <Flag className="w-5 h-5 text-primary" />, title: 'Assign issues for review', body: 'Flag specific issues for a team member to resolve. They\'ll be notified instantly and can resolve from the web or mobile app.' },
              { icon: <MessageCircle className="w-5 h-5 text-primary" />, title: 'Comment on any issue', body: 'Leave context on a flagged issue. "This is expected — it\'s a seasonal supplier" is infinitely more useful than just marking it resolved.' },
              { icon: <Share2 className="w-5 h-5 text-primary" />, title: 'Share datasets and insights', body: 'Share a cleaned dataset or a specific insight with anyone on your team — or with an external stakeholder via a view-only link.' },
              { icon: <Eye className="w-5 h-5 text-primary" />, title: 'See team activity in real time', body: 'The History tab shows every action taken by every team member, in chronological order. No more "who changed this?"' },
              { icon: <Lock className="w-5 h-5 text-primary" />, title: 'Role-based access control', body: 'Admins control everything. Analysts can upload and edit. Viewers can read but not modify. Sensitive columns can be restricted further.' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="dashboard-card dashboard-card-hover rounded-2xl p-6"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                  {item.icon}
                </div>
                <h3 className="text-base font-bold text-foreground mb-2">{item.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{item.body}</p>
              </motion.div>
            ))}
          </div>

          {/* Roles Table */}
          <div className="dashboard-card rounded-2xl p-7 overflow-x-auto">
            <h3 className="text-lg font-bold text-foreground mb-4">Roles & Permissions</h3>
            <table className="w-full text-sm min-w-[500px]">
              <thead>
                <tr className="text-left text-text-muted border-b border-border">
                  <th className="py-3">Permission</th>
                  <th className="py-3 text-center">Admin</th>
                  <th className="py-3 text-center">Analyst</th>
                  <th className="py-3 text-center">Viewer</th>
                </tr>
              </thead>
              <tbody className="text-text-secondary">
                {[
                  ['Upload files', true, true, false],
                  ['Run analyses', true, true, false],
                  ['Resolve issues', true, true, false],
                  ['Create charts', true, true, false],
                  ['View analyses', true, true, true],
                  ['View insights', true, true, true],
                  ['Download data', true, true, true],
                  ['Invite members', true, false, false],
                  ['Manage billing', true, false, false],
                  ['Delete data', true, false, false],
                ].map(([perm, admin, analyst, viewer]) => (
                  <tr key={perm as string} className="border-b border-border/60">
                    <td className="py-3 font-medium text-foreground">{perm as string}</td>
                    <td className="py-3 text-center">{admin ? '✅' : '❌'}</td>
                    <td className="py-3 text-center">{analyst ? '✅' : '❌'}</td>
                    <td className="py-3 text-center">{viewer ? '✅' : '❌'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FEATURE 8: MULTI-FILE ANALYSIS */}
      <section id="multi-file" className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 08 — MULTI-FILE ANALYSIS</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-4">
              One file tells you what happened.<br />Multiple files tell you why.
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mb-4">
              Upload monthly payroll files, quarterly sales records, or annual enrollment data. RefineX aligns them, compares them, and surfaces what changed — and what&apos;s trending.
            </p>
            <p className="text-text-secondary max-w-3xl mb-12 leading-relaxed">
              The real power of RefineX is not in a single analysis. It&apos;s in the third one. The sixth one. The one where patterns start to emerge. When you upload the same file format across multiple periods, RefineX detects the structure, aligns the data, and runs period-over-period comparisons automatically.
            </p>
          </motion.div>

          {/* Analysis Types */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { title: 'Period-over-Period Comparison', desc: 'This month vs last month. This year vs last year. Any two periods compared, metric by metric.', example: '"Average orders per rider increased from 9.3 to 11.4 between March and April — a 22% improvement."' },
              { title: 'Trend Detection', desc: 'Across 3+ periods, RefineX identifies upward, downward, or flat trends for every tracked metric.', example: '"Rider count has grown consistently month-over-month for 5 consecutive months (+8% average MoM)."' },
              { title: 'Seasonality Recognition', desc: 'With 6+ months of data, RefineX can identify recurring seasonal patterns.', example: '"Order volume consistently peaks in the 3rd week of every month — historically 18–22% above average."' },
              { title: 'Cohort Tracking', desc: 'Track the same group of entities across time to measure retention, growth, or performance change.', example: '"Riders who joined in January 2025 have 34% higher average orders in their 3rd month than those who joined in October 2024."' },
              { title: 'Anomaly in Context', desc: 'Something unusual in this month\'s data. Was it unusual last month too? Or is this the first time? Multi-file context answers that.', example: '' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="dashboard-card dashboard-card-hover rounded-2xl p-6"
              >
                <h3 className="text-base font-bold text-foreground mb-2">{item.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed mb-3">{item.desc}</p>
                {item.example && (
                  <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
                    <p className="text-xs text-foreground italic">{item.example}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURE 9: SECURITY & PRIVACY */}
      <section id="security-privacy" className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">FEATURE 09 — SECURITY & PRIVACY</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-12">
              Your data is yours.<br />We take that seriously.
            </h2>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {[
              { icon: <Lock className="w-5 h-5 text-primary" />, title: 'Encrypted in transit and at rest', body: 'All data is encrypted using TLS 1.3 in transit and AES-256 at rest. Your files are never stored unencrypted anywhere in our infrastructure.' },
              { icon: <Shield className="w-5 h-5 text-primary" />, title: 'We never train models on your data', body: 'Your uploaded files are never used to train any AI model — ours or any third party\'s. Your proprietary data stays proprietary.' },
              { icon: <Tag className="w-5 h-5 text-primary" />, title: 'Automatic PII detection and tagging', body: 'Columns containing personal data (names, emails, phone numbers, government IDs, medical diagnoses) are automatically tagged and can be restricted from export.' },
              { icon: <Trash2 className="w-5 h-5 text-primary" />, title: 'Delete your data anytime', body: 'Delete any analysis, any dataset, or your entire account at any time. Deletion is permanent and complete within 24 hours.' },
              { icon: <Clock className="w-5 h-5 text-primary" />, title: 'Configurable data retention', body: 'Set how long RefineX retains your data — 30 days, 90 days, 1 year, or indefinitely. You control the retention window.' },
              { icon: <Building className="w-5 h-5 text-primary" />, title: 'Enterprise-grade infrastructure', body: 'Hosted on SOC 2-compliant infrastructure. Uptime SLA available for Organization plan customers. Status page at status.refinex.io.' },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="dashboard-card dashboard-card-hover rounded-2xl p-6"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                  {item.icon}
                </div>
                <h3 className="text-base font-bold text-foreground mb-2">{item.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{item.body}</p>
              </motion.div>
            ))}
          </div>

          <div className="dashboard-card rounded-2xl p-7 text-center">
            <h3 className="text-lg font-bold text-foreground mb-2">Questions about how we handle your data?</h3>
            <p className="text-sm text-text-secondary mb-4">Read our Privacy Policy or contact our team directly.</p>
            <div className="flex justify-center gap-4">
              <Link href="#" className="text-primary font-semibold text-sm hover:underline">Read Privacy Policy →</Link>
              <Link href="/contact" className="text-primary font-semibold text-sm hover:underline">Contact Us →</Link>
            </div>
          </div>
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
              Everything your data team<br />needs in one platform.
            </h2>
            <p className="text-lg text-text-secondary mb-8">
              Start with your first file. Free. No credit card. No setup.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-10 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Analyze Your First File
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="/pricing" className="text-primary font-semibold flex items-center justify-center gap-1 px-4 h-14">
                Compare plans →
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
