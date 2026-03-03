'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, ChevronDown, Menu, X } from 'lucide-react'

const navLinks = [
  { label: 'How It Works', href: '/how-it-works' },
  { label: 'Features', href: '/features' },
  { label: 'Use Cases', href: '/use-cases', hasDropdown: true },
  { label: 'Pricing', href: '/pricing' },
  { label: 'Blog', href: '/blog' },
]

const useCaseDropdownItems = [
  { label: 'For Schools & Universities', href: '/use-cases#schools' },
  { label: 'For Hospitals & Clinics', href: '/use-cases#hospitals' },
  { label: 'For NGOs & Non-profits', href: '/use-cases#ngos' },
  { label: 'For Retail & Supermarkets', href: '/use-cases#retail' },
  { label: 'For Logistics & Delivery', href: '/use-cases#logistics' },
  { label: 'For Businesses & Corporates', href: '/use-cases#corporates' },
  { label: 'View All Use Cases →', href: '/use-cases' },
]

export default function Header() {
  const pathname = usePathname()
  const [scrolled, setScrolled] = useState(false)
  const [showUseCasesDropdown, setShowUseCasesDropdown] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [pathname])

  const isActive = (href: string) => {
    if (href === '/use-cases') return pathname.startsWith('/use-cases')
    if (href === '/blog') return pathname.startsWith('/blog')
    return pathname === href
  }

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/90 backdrop-blur-md shadow-[0_2px_12px_rgba(0,0,0,0.06)]'
          : 'bg-white/80 backdrop-blur-sm'
      } border-b border-border`}
    >
      <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
        <div className="flex justify-between items-center h-20">
          {/* Left — Logo */}
          <div className="flex items-center gap-10">
            <Link href="/" className="flex items-center gap-3 group">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="relative w-10 h-10 flex items-center justify-center"
              >
                <Image
                  src="/images/refinex.svg"
                  alt="RefineX Logo"
                  width={40}
                  height={40}
                  className="object-contain"
                />
              </motion.div>
              <div className="leading-tight">
                <span className="text-xl font-bold text-primary block">RefineX</span>
                <span className="text-[10px] text-text-muted font-semibold block hidden md:block">Data Intelligence</span>
              </div>
            </Link>

            {/* Center — Navigation Links */}
            <div className="hidden lg:flex items-center gap-8">
              {navLinks.map((link) =>
                link.hasDropdown ? (
                  <div
                    key={link.label}
                    className="relative"
                    onMouseEnter={() => setShowUseCasesDropdown(true)}
                    onMouseLeave={() => setShowUseCasesDropdown(false)}
                  >
                    <Link
                      href={link.href}
                      className={`flex items-center gap-1.5 text-sm font-semibold transition-colors py-2 ${
                        isActive(link.href)
                          ? 'text-primary border-b-2 border-primary'
                          : 'text-gray-700 hover:text-primary'
                      }`}
                    >
                      {link.label}
                      <ChevronDown
                        className={`w-4 h-4 transition-transform ${showUseCasesDropdown ? 'rotate-180' : ''}`}
                      />
                    </Link>

                    <AnimatePresence>
                      {showUseCasesDropdown && (
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 10 }}
                          transition={{ duration: 0.2 }}
                          className="absolute top-full left-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-border overflow-hidden"
                        >
                          <div className="py-2">
                            {useCaseDropdownItems.map((item) => (
                              <Link
                                key={item.label}
                                href={item.href}
                                className="block px-4 py-2.5 text-sm text-gray-700 hover:bg-primary/5 hover:text-primary transition-colors"
                              >
                                {item.label}
                              </Link>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ) : (
                  <Link
                    key={link.label}
                    href={link.href}
                    className={`text-sm font-semibold transition-colors py-2 ${
                      isActive(link.href)
                        ? 'text-primary border-b-2 border-primary'
                        : 'text-gray-700 hover:text-primary'
                    }`}
                  >
                    {link.label}
                  </Link>
                )
              )}
            </div>
          </div>

          {/* Right — CTA block */}
          <div className="hidden lg:flex items-center gap-3">
            <Link href="/auth/login">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-6 h-11 rounded-xl font-semibold text-gray-700 hover:text-primary hover:bg-[#F5F6FA] transition-all"
              >
                Sign In
              </motion.button>
            </Link>
            <Link href="/auth/signup">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-6 h-11 rounded-xl card-gradient text-white font-semibold shadow-sm hover:shadow-md transition-all flex items-center gap-2"
              >
                Start for Free
                <ArrowRight className="w-4 h-4" />
              </motion.button>
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            className="lg:hidden p-2 rounded-xl hover:bg-muted/30 transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="lg:hidden bg-white border-t border-border overflow-hidden"
          >
            <div className="px-6 py-6 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  className={`block px-4 py-3 rounded-xl text-base font-semibold transition-colors ${
                    isActive(link.href)
                      ? 'text-primary bg-primary/5'
                      : 'text-gray-700 hover:text-primary hover:bg-primary/5'
                  }`}
                >
                  {link.label}
                </Link>
              ))}

              <div className="border-t border-border my-4" />

              <Link href="/auth/login" className="block">
                <button className="w-full px-4 py-3 rounded-xl font-semibold text-gray-700 hover:text-primary hover:bg-[#F5F6FA] transition-all text-left">
                  Sign In
                </button>
              </Link>
              <Link href="/auth/signup" className="block">
                <button className="w-full px-6 h-12 rounded-xl card-gradient text-white font-semibold shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-2">
                  Start for Free
                  <ArrowRight className="w-4 h-4" />
                </button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  )
}
