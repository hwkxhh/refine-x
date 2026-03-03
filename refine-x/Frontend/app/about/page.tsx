'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

export default function AboutPage() {
  return (
    <PageLayout>
      <section className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1000px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">ABOUT US</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-10">
              Built by people who were tired<br />
              of <span className="text-primary">cleaning data manually.</span>
            </h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="dashboard-card rounded-2xl p-8 lg:p-10 space-y-5 text-text-secondary leading-relaxed text-lg"
          >
            <p>RefineX started as a frustration.</p>
            <p>We kept watching brilliant people — school administrators, clinic coordinators, NGO program managers, store owners — spend their best hours fighting spreadsheets instead of making decisions.</p>
            <p>The tools that existed were built for data scientists. The people who needed help weren&apos;t data scientists. They were just trying to do their jobs.</p>
            <p className="text-foreground font-semibold">So we built something for them.</p>
            <p>RefineX is a logic-first data intelligence platform. We don&apos;t rely on AI to guess what your data means. We follow a documented rulebook, built from 20+ years of data analyst best practices, and we explain every decision we make.</p>
            <p className="text-foreground font-medium italic">Because trust in your data starts with understanding what was done to it.</p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6 mt-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="dashboard-card rounded-2xl p-8"
            >
              <h2 className="text-xl font-bold text-foreground mb-3">Mission</h2>
              <p className="text-text-secondary leading-relaxed">To make data literacy accessible to every organization, regardless of technical capacity.</p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="dashboard-card rounded-2xl p-8"
            >
              <h2 className="text-xl font-bold text-foreground mb-3">Values</h2>
              <ul className="text-text-secondary space-y-2.5 leading-relaxed">
                <li className="flex items-start gap-2"><span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Transparency — Every decision explained. Every formula documented.</li>
                <li className="flex items-start gap-2"><span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Logic First — Deterministic before probabilistic. Rules before guesses.</li>
                <li className="flex items-start gap-2"><span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Respect for Data — We don&apos;t change what we can&apos;t verify. We ask.</li>
                <li className="flex items-start gap-2"><span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" />Access — Built for the world, not just Silicon Valley.</li>
              </ul>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mt-16 dashboard-card rounded-3xl p-12 text-center"
          >
            <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-4">Want to be part of this?</h2>
            <p className="text-text-secondary mb-6">We&apos;re building something meaningful. If that resonates, let&apos;s talk.</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-8 h-12 rounded-2xl card-gradient text-white font-bold text-sm shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Start for Free <ArrowRight className="w-4 h-4" />
                </motion.button>
              </Link>
              <Link href="/contact" className="text-primary font-semibold flex items-center justify-center gap-1 px-4 h-12">
                Contact us <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
