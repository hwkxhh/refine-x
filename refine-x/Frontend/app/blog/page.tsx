'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Clock, User } from 'lucide-react'
import PageLayout from '@/components/layout/page-layout'

const categories = ['All Posts', 'Data Cleaning', 'Analytics & Insights', 'Use Cases', 'Product Updates', 'Tutorials', 'Data Culture']

const featuredPost = {
  category: 'DATA QUALITY',
  title: 'The hidden cost of a typo in a spreadsheet',
  excerpt: 'A single formatting inconsistency in a date column can silently break six months of trend analysis. We traced one typo through a real dataset to show exactly how far the damage spreads — and how to find it before it finds you.',
  author: 'RefineX Team',
  date: 'February 18, 2026',
  readTime: '7 min read',
}

const posts = [
  {
    category: 'Data Cleaning',
    title: 'Why "prefer not to say" is not missing data — and why it matters',
    excerpt: 'Most data tools treat a blank and a refusal the same way. They\'re not. Here\'s why the difference matters for your analysis and how RefineX handles it.',
    readTime: '5 min read',
  },
  {
    category: 'Use Cases',
    title: 'How a school in Kathmandu found its enrollment problem in 90 seconds',
    excerpt: 'Three years of admission records. One upload. One chart. The pattern was obvious — once the data was clean enough to show it.',
    readTime: '6 min read',
  },
  {
    category: 'Analytics & Insights',
    title: 'The 80-20 rule for your data: Pareto analysis without a data analyst',
    excerpt: 'In most datasets, 20% of your rows, products, or people account for 80% of the impact. Here\'s how to find them — and what to do when you do.',
    readTime: '8 min read',
  },
  {
    category: 'Tutorials',
    title: 'How to upload a payment sheet to RefineX and verify every formula',
    excerpt: 'A step-by-step walkthrough of uploading a real rider payment file, watching RefineX detect the payment formulas, and verifying every row.',
    readTime: '10 min read',
  },
  {
    category: 'Data Culture',
    title: 'The real reason your team\'s data is messy (it\'s not the software)',
    excerpt: 'Data quality is a people problem before it\'s a tools problem. We\'ve seen it across schools, hospitals, and delivery companies. Here\'s what we\'ve learned.',
    readTime: '6 min read',
  },
  {
    category: 'Product Updates',
    title: 'Introducing Formula Intelligence: RefineX now verifies your math',
    excerpt: 'Starting today, RefineX automatically detects calculated columns in your data — and checks whether the formula holds for every single row.',
    readTime: '4 min read',
  },
  {
    category: 'Data Cleaning',
    title: '"Eleven" is a number. Your spreadsheet disagrees. Here\'s the fix.',
    excerpt: 'Written numbers in numeric columns — "eleven," "twelve," "thirten" — are more common than you\'d think. Here\'s how RefineX handles them and why most tools don\'t.',
    readTime: '4 min read',
  },
  {
    category: 'Analytics & Insights',
    title: 'Year-over-year vs month-over-month: which comparison actually tells you something?',
    excerpt: 'Both matter. They answer different questions. Here\'s when to use each — and what pitfalls to avoid with both.',
    readTime: '7 min read',
  },
  {
    category: 'Use Cases',
    title: 'NGO program data from the field is always messy. Here\'s how to clean it.',
    excerpt: 'Field data collected across 12 districts by 6 different people in 3 different formats. This is the reality of NGO data — and how RefineX handles it.',
    readTime: '8 min read',
  },
  {
    category: 'Tutorials',
    title: 'Data Quality Score explained: what each dimension means for your organization',
    excerpt: 'A deep dive into how RefineX calculates Completeness, Validity, Uniqueness, Consistency, and Accuracy — and why each one matters differently depending on your context.',
    readTime: '9 min read',
  },
  {
    category: 'Data Culture',
    title: 'Why the person who enters data is never the person who analyzes it (and why that\'s a problem)',
    excerpt: 'Data collection and data analysis happen in silos. The inconsistencies between them are not bugs — they\'re features of how organizations actually work. Here\'s what to do about it.',
    readTime: '6 min read',
  },
]

export default function BlogPage() {
  const [activeCategory, setActiveCategory] = useState('All Posts')
  const [visibleCount, setVisibleCount] = useState(9)

  const filteredPosts = useMemo(
    () => activeCategory === 'All Posts' ? posts : posts.filter((post) => post.category === activeCategory),
    [activeCategory]
  )

  const visiblePosts = filteredPosts.slice(0, visibleCount)

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
            <p className="text-xs font-semibold text-primary tracking-widest uppercase mb-4">THE REFINEX JOURNAL</p>
            <h1 className="text-4xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-foreground mb-6">
              Writing about data,<br />
              decisions, and the messy<br />
              <span className="text-primary">gap between them.</span>
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed max-w-2xl">
              Practical writing about data quality, analytics, and what it actually takes to make decisions from real-world organizational data — without a data science team.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Featured Post */}
      <section className="pb-12">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.article
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="dashboard-card dashboard-card-hover rounded-2xl p-8 lg:p-10 cursor-pointer"
          >
            <span className="text-xs font-bold text-primary tracking-wide">{featuredPost.category}</span>
            <h2 className="text-2xl lg:text-3xl font-bold text-foreground mt-2 mb-3">{featuredPost.title}</h2>
            <p className="text-text-secondary leading-relaxed max-w-3xl mb-5">{featuredPost.excerpt}</p>
            <div className="flex items-center gap-4 text-sm text-text-muted">
              <span className="flex items-center gap-1"><User className="w-3.5 h-3.5" />{featuredPost.author}</span>
              <span>{featuredPost.date}</span>
              <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{featuredPost.readTime}</span>
            </div>
            <Link href="#" className="text-primary font-semibold text-sm mt-4 inline-flex items-center gap-1 hover:underline">
              Read Article <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.article>
        </div>
      </section>

      {/* Category Tabs */}
      <section className="pb-6">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => {
                  setActiveCategory(category)
                  setVisibleCount(9)
                }}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                  activeCategory === category
                    ? 'bg-primary text-white shadow-md'
                    : 'bg-card text-text-secondary border border-border hover:text-foreground hover:border-primary/30'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Post Grid */}
      <section className="py-6 pb-20">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          {visiblePosts.length > 0 ? (
            <>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {visiblePosts.map((post, index) => (
                  <motion.article
                    key={post.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.05 }}
                    className="dashboard-card dashboard-card-hover rounded-2xl p-6 cursor-pointer flex flex-col"
                  >
                    <span className="text-xs font-bold text-primary tracking-wide uppercase">{post.category}</span>
                    <h3 className="text-lg font-bold text-foreground mt-2 mb-2 flex-1">{post.title}</h3>
                    <p className="text-sm text-text-secondary leading-relaxed mb-4">{post.excerpt}</p>
                    <div className="flex items-center justify-between text-xs text-text-muted mt-auto pt-4 border-t border-border/40">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{post.readTime}</span>
                      <span className="text-primary font-semibold flex items-center gap-1">Read <ArrowRight className="w-3 h-3" /></span>
                    </div>
                  </motion.article>
                ))}
              </div>

              {/* Load More / Pagination */}
              {visibleCount < filteredPosts.length && (
                <div className="mt-10 text-center">
                  <p className="text-sm text-text-muted mb-4">Showing {visiblePosts.length} of {filteredPosts.length} posts</p>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setVisibleCount(prev => prev + 6)}
                    className="px-8 h-12 rounded-2xl border border-border text-foreground font-semibold text-sm hover:border-primary/40 hover:text-primary transition-all"
                  >
                    Load More Posts
                  </motion.button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-20">
              <h3 className="text-xl font-bold text-foreground mb-2">No posts in this category yet</h3>
              <p className="text-text-secondary mb-6">We&apos;re adding new content regularly. Subscribe to be notified when new posts are published.</p>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-8 h-12 rounded-2xl card-gradient text-white font-bold text-sm"
              >
                Subscribe to updates
              </motion.button>
            </div>
          )}
        </div>
      </section>

      {/* Newsletter Strip */}
      <section className="py-16 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="mx-auto px-6 lg:px-12 max-w-[700px] text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-3">Data insights in your inbox</h2>
            <p className="text-text-secondary mb-6">
              One email a month. New articles, product updates, and practical data tips. No spam, ever.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Your work email"
                className="flex-1 h-12 px-4 rounded-xl border border-border bg-card text-foreground placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
              />
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="h-12 px-6 rounded-xl card-gradient text-white font-bold text-sm"
              >
                Subscribe
              </motion.button>
            </div>
            <p className="text-xs text-text-muted mt-3">You can unsubscribe anytime. We take your inbox seriously.</p>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
