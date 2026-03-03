'use client'

import { motion } from 'framer-motion'
import { Mail, BookOpen, MessageCircle } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

export default function ContactPage() {
  return (
    <PageLayout>
      <section className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1000px]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="mb-12"
          >
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">CONTACT</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-4">
              We read <span className="text-primary">every message.</span>
            </h1>
            <p className="text-lg text-text-secondary">We typically respond within 24 hours on business days.</p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Contact Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="lg:col-span-2 dashboard-card rounded-2xl p-8"
            >
              <h2 className="text-lg font-bold text-foreground mb-6">Send us a message</h2>
              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <input className="h-12 w-full rounded-xl border border-border bg-card px-4 text-sm text-foreground placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/40" placeholder="Your name" />
                  <input className="h-12 w-full rounded-xl border border-border bg-card px-4 text-sm text-foreground placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/40" placeholder="Email address" type="email" />
                </div>
                <select defaultValue="General inquiry" className="h-12 w-full rounded-xl border border-border bg-card px-4 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40">
                  <option>General inquiry</option>
                  <option>Bug report</option>
                  <option>Feature request</option>
                  <option>Billing question</option>
                  <option>Enterprise / Organization plan</option>
                  <option>NGO / Education discount</option>
                  <option>Partnership</option>
                </select>
                <textarea className="w-full rounded-xl border border-border bg-card px-4 py-3 text-sm text-foreground placeholder:text-text-muted min-h-40 focus:outline-none focus:ring-2 focus:ring-primary/40" placeholder="Your message" />
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="h-12 px-8 rounded-2xl card-gradient text-white font-bold text-sm shadow-lg hover:shadow-xl transition-all"
                >
                  Send Message
                </motion.button>
              </div>
            </motion.div>

            {/* Sidebar */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="space-y-4"
            >
              <div className="dashboard-card rounded-2xl p-6">
                <Mail className="w-6 h-6 text-primary mb-3" />
                <h3 className="font-bold text-foreground mb-1">Email</h3>
                <p className="text-sm text-text-secondary">hello@refinex.io</p>
              </div>
              <div className="dashboard-card rounded-2xl p-6">
                <BookOpen className="w-6 h-6 text-primary mb-3" />
                <h3 className="font-bold text-foreground mb-1">Documentation</h3>
                <p className="text-sm text-text-secondary">Browse guides, tutorials, and troubleshooting resources.</p>
              </div>
              <div className="dashboard-card rounded-2xl p-6">
                <MessageCircle className="w-6 h-6 text-primary mb-3" />
                <h3 className="font-bold text-foreground mb-1">Live Chat</h3>
                <p className="text-sm text-text-secondary">Available for Professional and Organization plan users.</p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>
    </PageLayout>
  )
}
