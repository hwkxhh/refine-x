'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, ChevronDown } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

const phases = [
  {
    number: '01',
    title: 'Upload & Structure Analysis',
    duration: 'Happens in under 3 seconds',
    body: 'The moment your file arrives, RefineX begins reading its structure — before touching a single value. This phase answers: Is the file well-formed? Are there multiple sheets? Is there a header row? Are there summary rows? Merged cells? Empty rows? Encoding issues? None of this requires AI. It\'s pure structural logic.',
    actions: [
      'File format detected (CSV, XLSX, XLS, TSV)',
      'Character encoding normalized (UTF-8 enforced)',
      'BOM characters removed (common in Excel exports)',
      'Multiple sheets identified and relationship assessed',
      'Header row located (even if it\'s not row 1)',
      'Summary/totals rows detected and separated',
      'Merged Excel cells filled via forward-fill',
      'Empty rows removed',
      'Column names cleaned (spaces stripped, snake_case applied)',
      'Duplicate column names flagged',
    ],
    example: `File uploaded: Raw_Data.xlsx
├── 2 sheets detected
├── Sheet 1: "Payment Sheet" — 418 rows, 13 columns
│   ├── Row 416 identified as TOTAL summary row → separated
│   ├── Rows 417–418 identified as empty → removed
│   └── Column "Fule" identified as likely spelling error
└── Sheet 2: "Store Avg. Orders" — 25 rows, 4 columns
    └── Appears to be a summary of Sheet 1 → flagged for cross-check`,
  },
  {
    number: '02',
    title: 'Column Classification',
    duration: 'Under 5 seconds for most files',
    body: 'Every column gets a Header Type (HTYPE) — one of 47 categories that determines which cleaning formulas will run on it. Classification uses a priority order: 1) Exact column name match, 2) Keyword in column name, 3) Value pattern regex, 4) Data type + range analysis, 5) Value set cardinality, 6) Reference list matching, 7) AI classification (last resort).',
    htypes: {
      'Personal & Identity': 'Full Name · First Name · Last Name · Middle Name · Unique ID · Age · Gender · National ID · Blood Group · Nationality · Education Level · Marital Status',
      'Date & Time': 'Date · Time · DateTime · Duration · Fiscal/Academic Period',
      'Contact & Location': 'Phone Number · Email · Full Address · City/Region · Country · Postal Code · Coordinates',
      'Numeric & Financial': 'Currency Amount · Quantity/Count · Percentage/Rate · Score/Grade/GPA · Currency Code · Rank/Ordinal · Calculated Column',
      'Classification & Status': 'Boolean/Flag · Category · Status · Survey/Likert Response · Multi-Value Tag',
      'Organizational & Product': 'Product Name · Product Code/SKU · Organization Name · Job Title · Department · Serial/Reference Number · Version Number',
      'Medical': 'Medical Diagnosis · Physical Measurement',
      'Text & Technical': 'Free Text/Notes · URL · IP Address · File Path/Name',
    },
    example: `Payment Sheet columns classified:
Store Name         → HTYPE-026: Organization Name
Contact Number     → HTYPE-009: Phone Number
Rider First Name   → HTYPE-002: First Name
Rider Last Name    → HTYPE-002: Last Name
Order Count        → HTYPE-016: Quantity/Count
Store Avg.         → HTYPE-017: Percentage/Rate
Sum of Distance    → HTYPE-015: Numeric Amount
Payment on Orders  → HTYPE-015: Currency Amount
Fuel               → HTYPE-015: Currency Amount
Total Earning      → HTYPE-044: Calculated/Derived Column`,
  },
  {
    number: '03',
    title: 'Value Cleaning — Formula Execution',
    duration: 'Scales with file size. Usually under 30 seconds.',
    body: 'Now that every column has been typed, the appropriate cleaning formulas run on every value in every column. This is the largest phase — spelling errors corrected, formats unified, written numbers converted, invalid values flagged, missing values evaluated. Every change is logged with the Formula ID that triggered it.',
    examples: [
      { type: 'Name columns', items: ['"gangirala" → "Gangirala" (FNAME-01: Title Case)', '"AVULA" → "Avula" (FNAME-01: Title Case)', '"Doe, John" → "John Doe" (FNAME-10: Name Swap Detection)'] },
      { type: 'Date columns', items: ['"2021-11-23, 1:40 pm" → parsed correctly as 2021-11-23 13:40', '"01/02/2024" → resolved via majority pattern in column', '"01/01/1900" → flagged as placeholder'] },
      { type: 'Phone columns', items: ['6305784695.0 → "6305784695" (PHONE-03: Float to String)', '"+1 (555) 123-4567" → "15551234567" (PHONE-03: Non-Numeric Strip)'] },
      { type: 'Numeric columns', items: ['"eleven" → 11 (QTY-01: Word-to-Number Conversion)', '"elven" → "eleven" → 11 (QTY-02: Typo Correction then Conversion)', '"₹1,250.00" → 1250.00 (AMT-01: Symbol + Separator Removal)'] },
      { type: 'Gender columns', items: ['"prefer not to say" → "Prefer Not to Say" — valid data, NOT missing (GEN-03)', '"m" → "Male" (GEN-01: Standardization)'] },
    ],
  },
  {
    number: '04',
    title: 'Missing Value Resolution',
    duration: 'Simultaneous with Phase 03',
    body: 'Every null or empty cell is evaluated individually. RefineX follows a strict decision tree: Can this value be calculated from other columns? → Calculate it. Can this value be logically inferred with high confidence? → Infer it. Can this value only be provided by the user? → Prompt the user. Never guess.',
    predictions: [
      { missing: 'Age (when DOB exists)', predictable: true, action: 'Auto-calculate: today − DOB' },
      { missing: 'Full name (when first + last exist)', predictable: true, action: 'Auto-combine: First + " " + Last' },
      { missing: 'Total (when amount + qty exist)', predictable: true, action: 'Auto-calculate: qty × price' },
      { missing: 'Duration (when start + end date exist)', predictable: true, action: 'Auto-calculate: end − start' },
      { missing: 'City (when full address exists)', predictable: true, action: 'Extract from address string' },
      { missing: 'Date (surrounded by sequential dates)', predictable: false, action: 'Suggest interpolated date. You confirm.' },
      { missing: 'Gender (when name suggests it)', predictable: false, action: 'Suggest only. You must confirm.' },
      { missing: 'Email', predictable: false, action: 'Prompt user.' },
      { missing: 'Phone number', predictable: false, action: 'Prompt user.' },
      { missing: 'Medical diagnosis', predictable: false, action: 'Prompt user.' },
    ],
  },
  {
    number: '05',
    title: 'Formula & Consistency Verification',
    duration: 'Under 5 seconds',
    body: 'After cleaning individual values, RefineX looks across columns to verify that relationships between columns are correct. This is where formula errors are caught. This is where logical inconsistencies surface. This is where a "Total" column that doesn\'t match its components gets flagged.',
    verifications: [
      { type: 'Formula discovery', desc: 'RefineX tests whether any column\'s values can be derived from other columns using common operations (×, +, −, ÷). If Total Earning ≈ Payment + Fuel across all rows, the formula is detected with high confidence.' },
      { type: 'Row-by-row formula check', desc: 'Once a formula is confirmed, it\'s verified for every row. Any row where the math doesn\'t add up is flagged, with the expected vs actual values shown side by side.' },
      { type: 'Conditional logic checks', desc: 'If status = "Discharged" → discharge_date must not be null. If score = 72 and pass_fail = "Fail" → inconsistent. If admission_date > graduation_date → impossible.' },
      { type: 'Cross-sheet validation', desc: 'If multiple sheets are present, RefineX checks whether values that should match between sheets actually do. Example: Rider counts in a summary sheet vs individual rider records in the main sheet.' },
    ],
  },
  {
    number: '06',
    title: 'AI Insight Generation',
    duration: '15–45 seconds depending on dataset size',
    body: 'Cleaning is complete. The data is verified. Now, and only now, does the AI take over. The AI reads your cleaned dataset, takes your stated goal into account, and generates plain-language observations — specific to your data, not generic. It does not make decisions. It does not modify data. It reads, interprets, and reports.',
    generates: [
      'Executive summary (what this dataset is, overall condition, top finding)',
      'Anomaly narrations (unusual values explained in context)',
      'Performance observations (who/what is above or below average)',
      'Trend observations (is a metric going up, down, or flat?)',
      'Data quality observations (what was found and fixed)',
      'Actionable recommendations (tied to your stated goal)',
      'Chart recommendations (which visualizations will show what matters most)',
    ],
    doesNot: [
      'Modify any data value',
      'Make decisions that should be made by a human',
      'Access data from outside this session',
      'Train itself on your data',
    ],
  },
]

const faqs = [
  { q: 'Does RefineX change my original file?', a: 'Never. Your original file is always preserved exactly as uploaded. RefineX creates a cleaned copy. You can compare original vs cleaned at any time, and you can undo any individual change from the cleaned version.' },
  { q: 'What if RefineX cleans something it shouldn\'t have?', a: 'Every auto-fix is reversible. Open the Issues tab, find the fix, and click Undo. The value is restored to its original state instantly. The undo action is also logged in the audit trail.' },
  { q: 'How does RefineX handle sensitive data like names and phone numbers?', a: 'Columns containing personal data are automatically tagged as PII (Personally Identifiable Information) and can be restricted from export. We never use your data to train AI models. Data is encrypted in transit and at rest. You can delete everything at any time.' },
  { q: 'What if my column isn\'t one of the 47 types?', a: 'RefineX will classify it as a general text or numeric column and apply universal rules (whitespace, encoding, placeholder detection). You can also manually override the classification for any column.' },
  { q: 'How long does analysis take?', a: 'For most files under 10MB, analysis completes in under 60 seconds. Larger files or files with complex cross-sheet relationships may take 2–3 minutes. You\'ll be notified by email when it\'s done.' },
  { q: 'Can RefineX handle files in languages other than English?', a: 'RefineX handles UTF-8 encoded files and recognizes values in multiple languages. Column name detection works best in English, but value cleaning (dates, numbers, phone formats) is country-configurable. Multi-language UI support is on our roadmap.' },
]

export default function HowItWorksPage() {
  const [activePhase, setActivePhase] = useState(0)
  const [openFaq, setOpenFaq] = useState<number | null>(null)
  const phase = phases[activePhase]

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
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">THE PROCESS</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-6">
              RefineX doesn&apos;t guess.<br />
              <span className="text-primary">It follows a rulebook.</span>
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed max-w-2xl">
              Every transformation is governed by a documented formula. Every AI decision is logged and explained. Here is exactly what happens to your data — start to finish.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Phase Timeline */}
      <section className="py-12 lg:py-20">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          {/* Phase Navigation */}
          <div className="flex gap-2 overflow-x-auto pb-4 mb-12 scrollbar-hide">
            {phases.map((p, idx) => (
              <button
                key={p.number}
                onClick={() => setActivePhase(idx)}
                className={`flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                  activePhase === idx
                    ? 'bg-primary text-white shadow-md'
                    : 'bg-card text-text-secondary border border-border hover:text-foreground hover:border-primary/30'
                }`}
              >
                <span className="text-xs font-bold">{p.number}</span>
                <span>{p.title}</span>
              </button>
            ))}
          </div>

          {/* Active Phase Detail */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activePhase}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
            >
              <div className="grid lg:grid-cols-3 gap-8">
                {/* Phase Info */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="dashboard-card rounded-2xl p-8">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold">PHASE {phase.number}</span>
                      <span className="text-xs text-text-muted">{phase.duration}</span>
                    </div>
                    <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-4">{phase.title}</h2>
                    <p className="text-text-secondary leading-relaxed">{phase.body}</p>
                  </div>

                  {/* Phase-specific content */}
                  {phase.actions && (
                    <div className="dashboard-card rounded-2xl p-8">
                      <h3 className="text-lg font-bold text-foreground mb-4">Specific actions in this phase</h3>
                      <ul className="space-y-2.5">
                        {phase.actions.map((action) => (
                          <li key={action} className="text-sm text-text-secondary flex items-start gap-2">
                            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {phase.htypes && (
                    <div className="dashboard-card rounded-2xl p-8">
                      <h3 className="text-lg font-bold text-foreground mb-4">The 47 Header Types (grouped)</h3>
                      <div className="space-y-4">
                        {Object.entries(phase.htypes).map(([group, types]) => (
                          <div key={group}>
                            <p className="text-sm font-bold text-foreground mb-1">{group}</p>
                            <p className="text-xs text-text-secondary">{types}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {phase.examples && (
                    <div className="dashboard-card rounded-2xl p-8">
                      <h3 className="text-lg font-bold text-foreground mb-4">Examples per column type</h3>
                      <div className="space-y-5">
                        {phase.examples.map((ex) => (
                          <div key={ex.type}>
                            <p className="text-sm font-bold text-foreground mb-2">{ex.type}</p>
                            <ul className="space-y-1.5">
                              {ex.items.map((item) => (
                                <li key={item} className="text-xs text-text-secondary font-mono bg-muted/30 rounded-lg px-3 py-2">{item}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {phase.predictions && (
                    <div className="dashboard-card rounded-2xl p-8 overflow-x-auto">
                      <h3 className="text-lg font-bold text-foreground mb-4">Predictable vs Non-predictable</h3>
                      <table className="w-full text-sm min-w-[500px]">
                        <thead>
                          <tr className="text-left text-text-muted border-b border-border">
                            <th className="py-2">Missing Value</th>
                            <th className="py-2">Predictable?</th>
                            <th className="py-2">Action</th>
                          </tr>
                        </thead>
                        <tbody className="text-text-secondary">
                          {phase.predictions.map((pred) => (
                            <tr key={pred.missing} className="border-b border-border/60">
                              <td className="py-2 font-medium text-foreground">{pred.missing}</td>
                              <td className="py-2">{pred.predictable ? '✅ Yes' : pred.action.includes('Suggest') ? '⚠️ Suggest' : '❌ No'}</td>
                              <td className="py-2">{pred.action}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <div className="mt-4 p-4 rounded-xl border-l-4 border-primary bg-primary/5">
                        <p className="text-sm text-text-secondary italic">RefineX never fills a value it cannot justify. If it fills something, it tells you why. If it can only guess, it asks you first.</p>
                      </div>
                    </div>
                  )}

                  {phase.verifications && (
                    <div className="dashboard-card rounded-2xl p-8">
                      <h3 className="text-lg font-bold text-foreground mb-4">Types of Verification</h3>
                      <div className="space-y-4">
                        {phase.verifications.map((v) => (
                          <div key={v.type} className="p-4 rounded-xl bg-muted/20">
                            <p className="text-sm font-bold text-foreground mb-1">{v.type}</p>
                            <p className="text-sm text-text-secondary leading-relaxed">{v.desc}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {phase.generates && (
                    <div className="grid sm:grid-cols-2 gap-6">
                      <div className="dashboard-card rounded-2xl p-8">
                        <h3 className="text-lg font-bold text-foreground mb-4">What the AI generates</h3>
                        <ul className="space-y-2.5">
                          {phase.generates.map((item) => (
                            <li key={item} className="text-sm text-text-secondary flex items-start gap-2">
                              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                      {phase.doesNot && (
                        <div className="dashboard-card rounded-2xl p-8">
                          <h3 className="text-lg font-bold text-foreground mb-4">What the AI does NOT do</h3>
                          <ul className="space-y-2.5">
                            {phase.doesNot.map((item) => (
                              <li key={item} className="text-sm text-text-secondary flex items-start gap-2">
                                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-error shrink-0" />
                                {item}
                              </li>
                            ))}
                          </ul>
                          <div className="mt-4 p-4 rounded-xl border-l-4 border-primary bg-primary/5">
                            <p className="text-sm text-text-secondary italic">AI is used where human judgment is needed for language and interpretation — not where rules and logic are enough. If a formula can solve it, a formula solves it.</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Right sidebar — Example */}
                <div className="space-y-6">
                  {phase.example && (
                    <div className="dashboard-card rounded-2xl p-6">
                      <h3 className="text-sm font-bold text-foreground mb-3">Real Example</h3>
                      <pre className="text-xs text-text-secondary leading-relaxed font-mono bg-[#0F0F0F] text-gray-300 rounded-xl p-4 overflow-x-auto whitespace-pre-wrap">{phase.example}</pre>
                    </div>
                  )}

                  {/* Timeline mini-nav */}
                  <div className="dashboard-card rounded-2xl p-6">
                    <h3 className="text-sm font-bold text-foreground mb-3">All Phases</h3>
                    <div className="space-y-2">
                      {phases.map((p, idx) => (
                        <button
                          key={p.number}
                          onClick={() => setActivePhase(idx)}
                          className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                            activePhase === idx
                              ? 'bg-primary text-white'
                              : 'text-text-secondary hover:text-foreground hover:bg-muted/30'
                          }`}
                        >
                          <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                            activePhase === idx ? 'bg-white/20' : 'bg-primary/10 text-primary'
                          }`}>
                            {p.number}
                          </span>
                          <span className="text-xs font-medium">{p.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </section>

      {/* Transparency Section */}
      <section className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">TRANSPARENCY</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-6">
              We tell you everything<br />we did to your data.
            </h2>
            <p className="text-lg text-text-secondary max-w-3xl leading-relaxed mb-8">
              Every action RefineX takes is recorded in your audit trail: the Formula ID that triggered it, what changed, the before and after values, and whether it was automatic or manual. You can review every single transformation. You can undo any auto-fix. You can export the full log as a CSV. There are no black boxes in RefineX.
            </p>

            <div className="dashboard-card rounded-2xl p-7 border-l-4 border-primary">
              <h3 className="text-lg font-bold text-foreground mb-2">The Formula Rulebook</h3>
              <p className="text-sm text-text-secondary leading-relaxed mb-3">
                Every cleaning formula is publicly documented in the RefineX Formula Rulebook — 47 Header Types, 200+ formulas, every trigger condition defined. If you want to know what will happen to your data before you upload it, you can read the rulebook first.
              </p>
              <Link href="#" className="text-primary font-semibold text-sm hover:underline inline-flex items-center gap-1">
                Read the Formula Rulebook <ArrowRight className="w-4 h-4" />
              </Link>
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
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">COMMON QUESTIONS</p>
            <h2 className="text-3xl lg:text-4xl font-bold text-foreground mb-8">Questions about the process</h2>
          </motion.div>

          <div className="space-y-3">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
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
              The best way to understand<br />RefineX is to use it.
            </h2>
            <p className="text-lg text-text-secondary mb-8">
              Upload your first file free. See the whole process in action.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-10 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Analyze a File Now — Free
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="#" className="text-primary font-semibold flex items-center justify-center gap-1 px-4 h-14">
                Or try with our sample dataset
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
