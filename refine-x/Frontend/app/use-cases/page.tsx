'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence, useInView } from 'framer-motion'
import { ArrowRight, Quote } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

const industries = [
  'Schools & Universities',
  'Hospitals & Clinics',
  'NGOs & Non-profits',
  'Retail & Supermarkets',
  'Logistics & Delivery',
  'Businesses & Corporates',
  'Government & Public Sector',
  'Research & Academia',
]

const useCases = [
  {
    id: 'schools',
    heroLabel: 'FOR EDUCATION',
    headline: 'Your enrollment data\nis trying to tell you something.\nRefineX helps you hear it.',
    subheadline: 'Schools collect years of data — admissions, attendance, exam results, ECA activities, teacher records — but rarely have the tools to analyze it. RefineX changes that.',
    challenge: 'School administrators are not data analysts. But they\'re expected to make data-driven decisions about admissions strategy, resource allocation, program quality, and teacher performance.\n\nTheir data lives in Excel files, Google Sheets, and student management systems — in different formats, maintained by different people, with years of accumulated inconsistencies.',
    scenarios: [
      { title: 'Admissions trend analysis', body: 'Upload year-by-year admission records. RefineX cleans the data, unifies the formats, and shows you which programs are growing, which are declining, and when applications peak during the year.', insight: '"Science stream admissions dropped 18% in Q2 compared to the prior year. March historically shows the highest drop-off rate — this may indicate a mismatch in exam-season counseling timing."' },
      { title: 'Exam result analysis', body: 'Track pass rates, subject-wise performance, and year-over-year improvement. Identify which subjects consistently produce low scores — and in which classes.', insight: '"Mathematics pass rate in Grade 10 has declined 3 consecutive years. The decline began in 2022, coinciding with a curriculum change."' },
      { title: 'Student attendance patterns', body: 'Monthly attendance data cleaned, standardized, and analyzed for patterns. Which students are at dropout risk? Which days have the highest absences?', insight: '"Absences spike every 3rd Monday across all grades. The pattern suggests a systemic scheduling or transport issue rather than individual student factors."' },
      { title: 'Teacher and staff records', body: 'Track staff count, tenure, qualifications, and workload. Clean messy HR data and identify understaffing patterns before they affect student outcomes.' },
      { title: 'ECA and program tracking', body: 'Which extracurricular activities have the most participation? How has participation changed over time? Are certain activities tied to better academic outcomes?' },
    ],
    dataTypes: ['Student admission records (names, dates, ID numbers, addresses)', 'Exam result sheets (scores, grades, pass/fail, subject names)', 'Attendance logs (dates, student IDs, present/absent flags)', 'Staff records (names, qualifications, joining dates, salaries)', 'Fee collection records (amounts, dates, payment status)', 'ECA participation logs (student names, activity, date, duration)'],
    testimonial: { quote: 'I uploaded three years of admission data and within 90 seconds I understood why our Science stream was shrinking. That analysis would have taken me a full weekend in Excel.', attribution: 'Academic Coordinator · Private School, Kathmandu' },
    cta: 'Try RefineX with your school data',
  },
  {
    id: 'hospitals',
    heroLabel: 'FOR HEALTHCARE',
    headline: 'Patient records deserve\nbetter than a spreadsheet\nwith 6 years of inconsistencies.',
    subheadline: 'Clinical data is complex, sensitive, and often messy. RefineX cleans it safely, flags PII automatically, and turns patient records into operational insights.',
    challenge: 'Healthcare organizations collect enormous amounts of data — patient demographics, diagnosis codes, bed occupancy, medicine usage, appointment logs, staff schedules.\n\nMost of it lives in spreadsheets. Most of it is inconsistent. Date formats differ. Diagnosis names are abbreviated differently by different doctors. Patient IDs are duplicated. Phone numbers are stored in four different formats.\n\nBad data in healthcare doesn\'t just produce wrong reports. It produces wrong decisions.',
    scenarios: [
      { title: 'Patient record cleaning and deduplication', body: 'The same patient appears three times with different name spellings and the same phone number. RefineX detects it, flags it, and helps you merge the records correctly.', insight: '"14 patient records appear to be duplicates based on matching phone numbers with minor name spelling variations. Review before proceeding."' },
      { title: 'Bed occupancy and patient flow', body: 'Track daily bed occupancy rates, average length of stay, admission-to-discharge timelines, and peak period identification.', insight: '"Average patient wait time increased 23 minutes over the last 6 weeks. Tuesday afternoons between 2–5 PM show the highest congestion across all wards."' },
      { title: 'Diagnosis and treatment patterns', body: 'Clean ICD code columns, standardize diagnosis names, expand abbreviations (HTN → Hypertension), and analyze which conditions are most frequently treated — and in which wards.' },
      { title: 'Medicine usage tracking', body: 'Track which medicines are being used, in which quantities, and how usage has changed over time. Identify potential stockout risks from usage trend data.' },
      { title: 'Staff performance and workload', body: 'Analyze patient-to-staff ratios, doctor consultation counts, nurse shift coverage, and overtime patterns.' },
    ],
    piiNote: 'Healthcare data requires extra care. RefineX automatically identifies and tags all PII columns — patient names, phone numbers, national IDs, diagnoses, addresses. These columns are flagged for restricted export and excluded from any AI processing outside the session. We never store, share, or train on patient data.',
    dataTypes: ['Patient demographics (names, DOB, gender, phone, address, blood group)', 'Admission and discharge records (dates, ward, diagnosis, status)', 'ICD-10 diagnosis codes and condition names', 'Medicine inventory and usage logs', 'Appointment schedules and no-show rates', 'Staff rosters and shift logs'],
    cta: 'Try RefineX with your clinic data',
  },
  {
    id: 'ngos',
    heroLabel: 'FOR CIVIL SOCIETY',
    headline: 'Your impact is real.\nYour data should\nreflect that clearly.',
    subheadline: 'Field data is messy by nature. RefineX makes it donor-ready — without a data science team.',
    challenge: 'NGOs operate with lean teams in the field. Data comes in from multiple collectors, across multiple locations, in multiple formats. By the time it reaches the program manager, it\'s a patchwork of inconsistencies.\n\nDonors want clean data and clear impact metrics. Beneficiaries deserve decisions made from accurate records. RefineX bridges the gap between field reality and reporting standards.',
    scenarios: [
      { title: 'Beneficiary data cleaning', body: 'Beneficiary records collected by different field workers will have name spelling variations, different date formats, missing values, and duplicate entries. RefineX normalizes all of it.' },
      { title: 'Program reach and coverage tracking', body: 'How many beneficiaries reached? Which districts? Which demographics? How has coverage changed quarter over quarter?', insight: '"Program coverage increased 34% this quarter. Northern districts remain underserved — only 12% of target beneficiaries have been reached."' },
      { title: 'Fund utilization analysis', body: 'Track expenditure against budget. Which programs are over or under-spending? Where is money being most effectively used?' },
      { title: 'Outcome measurement', body: 'Before/after data for program participants. Did school enrollment increase? Did income levels rise? Did health indicators improve? Clean the data and compare periods.' },
      { title: 'Donor report preparation', body: 'Upload your raw field data. Export a clean, analyzed dataset with charts and insights ready to share with donors — without hours of manual formatting.' },
    ],
    dataTypes: [],
    cta: 'Try RefineX with your program data',
  },
  {
    id: 'retail',
    heroLabel: 'FOR RETAIL',
    headline: 'Your sales data knows\nwhat to stock next month.\nIt just can\'t tell you yet.',
    subheadline: 'From weekly sales sheets to salesperson performance to seasonal demand — RefineX turns retail records into retail strategy.',
    challenge: 'Retail businesses generate data every single day — sales transactions, stock levels, customer purchases, salesperson records, supplier deliveries.\n\nMost of it is exported from POS systems in inconsistent formats. Product names vary between exports. Dates are formatted differently by different systems. Amounts have currency symbols in some files and not others.\n\nBy the time the data is in a presentable state, the week is over and the decision moment has passed.',
    scenarios: [
      { title: 'Sales performance by product and category', body: 'Which products are driving revenue? Which categories are shrinking? Which SKUs are moving faster than you expected?', insight: '"Category B products generate 67% of revenue but occupy only 31% of shelf space. Category A products show a 3-month declining trend."' },
      { title: 'Salesperson performance tracking', body: 'Track individual salesperson contribution, conversion rates, and trend over time. Identify top performers and those who may need support.' },
      { title: 'Seasonal demand patterns', body: 'Six months of sales data is enough for RefineX to identify seasonal peaks. Plan stock, staff, and promotions in advance.', insight: '"Sales consistently peak in the 2nd week of November and the 1st week of January. Stock levels in these periods have historically run 22% below demand."' },
      { title: 'Inventory and stockout analysis', body: 'Cross-reference sales velocity with stock levels. Identify which products are at stockout risk before the stockout happens.' },
      { title: 'Supplier and delivery tracking', body: 'Track delivery timelines, supplier reliability, and order fulfillment rates. Which suppliers consistently deliver late?' },
    ],
    dataTypes: [],
    cta: 'Try RefineX with your sales data',
  },
  {
    id: 'logistics',
    heroLabel: 'FOR LOGISTICS',
    headline: 'Every route. Every rider.\nEvery rupee. Accounted for.',
    subheadline: 'Delivery operations run on data. RefineX makes sure that data is clean, correct, and telling you exactly what\'s happening on the ground.',
    challenge: 'Logistics teams manage large volumes of operational data — rider records, delivery orders, route distances, store-level performance, payment calculations.\n\nErrors in this data don\'t just produce wrong reports. They produce wrong paychecks. Disputes. Churn.\n\nA formula error in a payment sheet that goes undetected for six weeks costs real money and real trust. RefineX finds it in the first scan.',
    scenarios: [
      { title: 'Rider payment accuracy verification', body: 'Upload your rider payment sheet. RefineX detects the payment formula, verifies it row by row, and flags every rider whose payment doesn\'t add up.', insight: '"In a live test with a 415-rider payment sheet, RefineX detected three payment formulas, verified all 415 rows, and found zero calculation errors — in under 60 seconds."' },
      { title: 'Store-level performance comparison', body: 'Which stores have the highest orders per rider? Which stores have the highest MG dependency? Which stores are consistently outperforming or underperforming?' },
      { title: 'Rider productivity analysis', body: 'Order distribution, earnings distribution, single-order riders, high-performer identification. Understand your rider base as a whole.', insight: '"8 riders completed only 1 order and earned under ₹50 this period. Consider a review process for single-order riders who may be at churn risk."' },
      { title: 'Multi-period performance tracking', body: 'Upload weekly payment files. RefineX tracks rider performance month over month — who improved, who declined, who dropped off entirely.' },
      { title: 'Minimum guarantee cost analysis', body: 'Track MG dependency rates by store and over time. When 83% of riders receive the MG floor, that\'s a signal worth understanding.' },
    ],
    dataTypes: [],
    cta: 'Try RefineX with your delivery data',
  },
]

function UseCaseSection({ useCase, index }: { useCase: typeof useCases[number]; index: number }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, amount: 0.1 })

  return (
    <motion.section
      ref={ref}
      id={useCase.id}
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : {}}
      transition={{ duration: 0.6 }}
      className={`py-20 lg:py-28 ${index % 2 === 1 ? 'bg-gradient-to-b from-primary/[0.02] to-transparent' : ''}`}
    >
      <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
        {/* Use Case Hero */}
        <div className="mb-16">
          <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">{useCase.heroLabel}</p>
          <h2 className="text-3xl lg:text-5xl font-bold text-foreground leading-[1.15] whitespace-pre-line mb-5">{useCase.headline}</h2>
          <p className="text-lg text-text-secondary max-w-2xl leading-relaxed">{useCase.subheadline}</p>
        </div>

        {/* Challenge */}
        <div className="dashboard-card rounded-2xl p-8 mb-12">
          <h3 className="text-lg font-bold text-foreground mb-3">The Challenge</h3>
          <p className="text-text-secondary leading-relaxed whitespace-pre-line">{useCase.challenge}</p>
        </div>

        {/* Scenarios */}
        <div className="mb-12">
          <h3 className="text-xl font-bold text-foreground mb-6">What RefineX does</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {useCase.scenarios.map((scenario, sIdx) => (
              <motion.div
                key={scenario.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: sIdx * 0.08 }}
                className="dashboard-card dashboard-card-hover rounded-2xl p-6 flex flex-col"
              >
                <span className="text-xs font-bold text-primary mb-2">SCENARIO {sIdx + 1}</span>
                <h4 className="text-base font-bold text-foreground mb-2">{scenario.title}</h4>
                <p className="text-sm text-text-secondary leading-relaxed flex-1">{scenario.body}</p>
                {scenario.insight && (
                  <div className="mt-4 p-4 rounded-xl border border-primary/20 bg-primary/5">
                    <p className="text-xs font-semibold text-primary mb-1">SAMPLE INSIGHT</p>
                    <p className="text-sm text-foreground font-medium italic">{scenario.insight}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* PII Note (hospitals) */}
        {useCase.piiNote && (
          <div className="dashboard-card rounded-2xl p-8 mb-12 border-l-4 border-primary">
            <h3 className="text-lg font-bold text-foreground mb-3">PII & Sensitivity Handling</h3>
            <p className="text-text-secondary leading-relaxed">{useCase.piiNote}</p>
          </div>
        )}

        {/* Data Types */}
        {useCase.dataTypes.length > 0 && (
          <div className="dashboard-card rounded-2xl p-8 mb-12">
            <h3 className="text-lg font-bold text-foreground mb-4">Data types commonly cleaned</h3>
            <div className="grid sm:grid-cols-2 gap-2.5">
              {useCase.dataTypes.map((dt) => (
                <div key={dt} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                  {dt}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Testimonial */}
        {useCase.testimonial && (
          <div className="dashboard-card rounded-2xl p-8 mb-12">
            <Quote className="w-8 h-8 text-primary/30 mb-3" />
            <p className="text-lg text-foreground font-medium italic leading-relaxed mb-4">&ldquo;{useCase.testimonial.quote}&rdquo;</p>
            <p className="text-sm text-text-muted">{useCase.testimonial.attribution}</p>
          </div>
        )}

        {/* CTA */}
        <Link href="/auth/signup">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-8 h-12 rounded-2xl card-gradient text-white font-bold text-sm shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
          >
            {useCase.cta} <ArrowRight className="w-4 h-4" />
          </motion.button>
        </Link>
      </div>
    </motion.section>
  )
}

export default function UseCasesPage() {
  const [activeIndustry, setActiveIndustry] = useState(0)

  const scrollToCase = (id: string) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

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
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">WHO IT&apos;S FOR</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-6">
              Built for every organization<br />
              that keeps records<br />
              <span className="text-primary">and needs to understand them.</span>
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed max-w-2xl">
              RefineX was not built for data scientists. It was built for the people data scientists were supposed to serve — but never had time for.
            </p>
          </motion.div>

          {/* Industry Selector Tabs */}
          <div className="mt-10 flex gap-2 overflow-x-auto pb-3 scrollbar-hide">
            {industries.map((industry, idx) => (
              <button
                key={industry}
                onClick={() => {
                  setActiveIndustry(idx)
                  if (idx < useCases.length) scrollToCase(useCases[idx].id)
                }}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                  activeIndustry === idx
                    ? 'bg-primary text-white shadow-md'
                    : 'bg-card text-text-secondary border border-border hover:text-foreground hover:border-primary/30'
                }`}
              >
                {industry}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Use Case Sections */}
      {useCases.map((useCase, index) => (
        <UseCaseSection key={useCase.id} useCase={useCase} index={index} />
      ))}

      {/* Bottom Section — Works for Any Organization */}
      <section className="py-20 lg:py-28 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">WORKS FOR ANY ORGANIZATION</p>
            <h2 className="text-3xl lg:text-5xl font-bold text-foreground mb-6">
              If it has rows and columns,<br />
              <span className="text-primary">RefineX can analyze it.</span>
            </h2>
            <p className="text-lg text-text-secondary max-w-3xl leading-relaxed mb-4">
              The five use cases above are where RefineX is most commonly used. But the underlying platform is domain-agnostic — built to work with any structured data from any industry.
            </p>
            <div className="text-text-secondary leading-relaxed mb-8 space-y-1">
              <p>Importers and exporters tracking shipments.</p>
              <p>Research teams managing survey data.</p>
              <p>HR departments analyzing recruitment funnels.</p>
              <p>Finance teams verifying budget vs actual.</p>
              <p>Government offices processing public records.</p>
            </div>
            <p className="text-lg text-foreground font-semibold mb-8">If your organization keeps structured records, RefineX is built for you.</p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-10 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Start for Free <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="/contact" className="text-primary font-semibold flex items-center gap-1 px-4 h-14">
                Talk to us about your specific use case <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
