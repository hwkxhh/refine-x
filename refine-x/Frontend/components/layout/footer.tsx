'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { ArrowRight, ChevronDown } from 'lucide-react'

export default function Footer() {
  const [expandedColumn, setExpandedColumn] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const toggleColumn = (col: string) => {
    setExpandedColumn(expandedColumn === col ? null : col)
  }

  return (
    <footer className="relative bg-gradient-to-b from-background to-[#e8ecff] border-t border-border">
      {/* Newsletter Strip */}
      <div className="border-b border-border">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px] py-12">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <h3 className="text-xl font-bold text-foreground mb-1">Stay sharp on data.</h3>
              <p className="text-sm text-text-secondary">
                Insights, product updates, and data tips — once a month. No spam.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
              <input
                type="email"
                placeholder="Your work email"
                className="h-12 px-4 rounded-xl bg-card border border-border text-foreground placeholder:text-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 w-full sm:w-72"
              />
              <button className="h-12 px-6 rounded-xl card-gradient text-white font-semibold text-sm hover:opacity-90 transition-colors whitespace-nowrap">
                Subscribe
              </button>
            </div>
          </div>
          <p className="text-xs text-text-muted mt-3">No spam. Unsubscribe in one click.</p>
        </div>
      </div>

      {/* Main Footer Grid */}
      <div className="mx-auto px-6 lg:px-12 max-w-[1400px] py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
          {/* Column 1 — Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 flex items-center justify-center">
                <Image
                  src="/images/refinex.svg"
                  alt="RefineX Logo"
                  width={40}
                  height={40}
                  className="object-contain"
                />
              </div>
              <span className="text-lg font-bold text-foreground">RefineX</span>
            </Link>
            <p className="text-sm text-text-secondary leading-relaxed mb-6">
              Intelligent data cleaning and analytics for every organization.
            </p>
            <div className="flex items-center gap-4">
              <Link href="https://linkedin.com/company/refinex" aria-label="LinkedIn" className="text-text-muted hover:text-primary transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
              </Link>
              <Link href="https://twitter.com/refinex" aria-label="Twitter/X" className="text-text-muted hover:text-primary transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              </Link>
              <Link href="https://github.com/refinex" aria-label="GitHub" className="text-text-muted hover:text-primary transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              </Link>
              <Link href="https://youtube.com/@refinex" aria-label="YouTube" className="text-text-muted hover:text-primary transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
              </Link>
            </div>
          </div>

          {/* Column 2 — Product */}
          <div>
            <button
              onClick={() => toggleColumn('product')}
              className="md:cursor-default flex items-center justify-between w-full md:mb-4"
            >
              <h4 className="font-bold text-foreground text-sm uppercase tracking-wider">Product</h4>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${expandedColumn === 'product' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2.5 text-sm text-text-secondary mt-4 md:mt-0 ${expandedColumn === 'product' || mounted ? 'block' : 'hidden md:block'}`}>
              <li><Link href="/how-it-works" className="hover:text-primary transition-colors">How It Works</Link></li>
              <li><Link href="/features" className="hover:text-primary transition-colors">Features</Link></li>
              <li><Link href="/pricing" className="hover:text-primary transition-colors">Pricing</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Changelog</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors flex items-center gap-2">Roadmap <span className="text-xs text-text-muted">· Coming Soon</span></Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Status Page</Link></li>
            </ul>
          </div>

          {/* Column 3 — Use Cases */}
          <div>
            <button
              onClick={() => toggleColumn('usecases')}
              className="md:cursor-default flex items-center justify-between w-full md:mb-4"
            >
              <h4 className="font-bold text-foreground text-sm uppercase tracking-wider">Use Cases</h4>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${expandedColumn === 'usecases' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2.5 text-sm text-text-secondary mt-4 md:mt-0 ${expandedColumn === 'usecases' ? 'block' : 'hidden md:block'}`}>
              <li><Link href="/use-cases#schools" className="hover:text-primary transition-colors">For Schools</Link></li>
              <li><Link href="/use-cases#hospitals" className="hover:text-primary transition-colors">For Hospitals</Link></li>
              <li><Link href="/use-cases#ngos" className="hover:text-primary transition-colors">For NGOs</Link></li>
              <li><Link href="/use-cases#retail" className="hover:text-primary transition-colors">For Retail</Link></li>
              <li><Link href="/use-cases#logistics" className="hover:text-primary transition-colors">For Logistics</Link></li>
              <li><Link href="/use-cases" className="hover:text-primary transition-colors">View All Use Cases</Link></li>
            </ul>
          </div>

          {/* Column 4 — Resources */}
          <div>
            <button
              onClick={() => toggleColumn('resources')}
              className="md:cursor-default flex items-center justify-between w-full md:mb-4"
            >
              <h4 className="font-bold text-foreground text-sm uppercase tracking-wider">Resources</h4>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${expandedColumn === 'resources' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2.5 text-sm text-text-secondary mt-4 md:mt-0 ${expandedColumn === 'resources' ? 'block' : 'hidden md:block'}`}>
              <li><Link href="#" className="hover:text-primary transition-colors">Documentation</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Formula Rulebook</Link></li>
              <li><Link href="/blog" className="hover:text-primary transition-colors">Blog</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors flex items-center gap-2">Webinars <span className="text-xs text-text-muted">· Coming Soon</span></Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">API Reference</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors flex items-center gap-2">Community <span className="text-xs text-text-muted">· Coming Soon</span></Link></li>
            </ul>
          </div>

          {/* Column 5 — Company */}
          <div>
            <button
              onClick={() => toggleColumn('company')}
              className="md:cursor-default flex items-center justify-between w-full md:mb-4"
            >
              <h4 className="font-bold text-foreground text-sm uppercase tracking-wider">Company</h4>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${expandedColumn === 'company' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2.5 text-sm text-text-secondary mt-4 md:mt-0 ${expandedColumn === 'company' ? 'block' : 'hidden md:block'}`}>
              <li><Link href="/about" className="hover:text-primary transition-colors">About</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors flex items-center gap-2">Careers <span className="text-xs text-primary font-semibold">· We&apos;re Hiring</span></Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Press Kit</Link></li>
              <li><Link href="/contact" className="hover:text-primary transition-colors">Contact</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Privacy Policy</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Terms of Service</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Cookie Policy</Link></li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  )
}
