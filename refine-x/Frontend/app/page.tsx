'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Check, ChevronDown, Play, Upload } from 'lucide-react'
import Footer from '@/components/layout/footer'

export default function Home() {
  const [mounted, setMounted] = useState(false)
  const [activeSlice, setActiveSlice] = useState(0)
  const [currentSlide, setCurrentSlide] = useState(0)
  const [showFeaturesDropdown, setShowFeaturesDropdown] = useState(false)

  useEffect(() => {
    setMounted(true)
    const sliceInterval = setInterval(() => {
      setActiveSlice((prev) => (prev + 1) % 4)
    }, 2000)
    
    const slideInterval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % 4)
    }, 5000)
    
    return () => {
      clearInterval(sliceInterval)
      clearInterval(slideInterval)
    }
  }, [])

  // Pie chart data
  const pieData = [
    { label: 'Sales', value: 35, color: '#5B4FE7', icon: 'icons8-bar-chart-50.png' },
    { label: 'Marketing', value: 25, color: '#7367F0', icon: 'icons8-increase-50.png' },
    { label: 'Operations', value: 20, color: '#9785FF', icon: 'icons8-workflow-50.png' },
    { label: 'Support', value: 20, color: '#B8AAFF', icon: 'icons8-online-support-50.png' }
  ]

  // Hospital data
  const hospitalData = [
    { label: 'Doctors', value: 145, icon: 'icons8-manager-50.png', color: '#5B4FE7', change: '+12%' },
    { label: 'Patients', value: 2847, icon: 'icons8-people-50.png', color: '#7367F0', change: '+8%' },
    { label: 'Surgeries', value: 89, icon: 'icons8-approval-50.png', color: '#9785FF', change: '+15%' },
    { label: 'Staff', value: 423, icon: 'icons8-organization-50.png', color: '#B8AAFF', change: '+5%' }
  ]

  // Monthly trend data
  const monthlyData = [
    { month: 'Jan', value: 45 },
    { month: 'Feb', value: 62 },
    { month: 'Mar', value: 58 },
    { month: 'Apr', value: 78 },
    { month: 'May', value: 72 },
    { month: 'Jun', value: 88 },
    { month: 'Jul', value: 95 },
    { month: 'Aug', value: 85 }
  ]

  // Calculate pie chart paths
  const createPieSlice = (startAngle: number, endAngle: number, radius: number = 100) => {
    const start = polarToCartesian(120, 120, radius, endAngle)
    const end = polarToCartesian(120, 120, radius, startAngle)
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
    return `M 120 120 L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`
  }

  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians)
    }
  }

  let currentAngle = 0
  const slices = pieData.map((data, index) => {
    const slice = {
      ...data,
      startAngle: currentAngle,
      endAngle: currentAngle + (data.value / 100) * 360
    }
    currentAngle = slice.endAngle
    return slice
  })

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <motion.nav 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-sm border-b border-border"
      >
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <div className="flex justify-between items-center h-20">
            {/* Left Side */}
            <div className="flex items-center gap-10">
              {/* Brand */}
              <Link href="/" className="flex items-center gap-3 group">
                <motion.div 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="relative w-10 h-10 flex items-center justify-center"
                >
                  <Image 
                    src="/images/refinex.svg" 
                    alt="Refine Logo"
                    width={40}
                    height={40}
                    className="object-contain"
                  />
                </motion.div>
                <div className="leading-tight">
                  <span className="text-xl font-bold text-primary block">RefineX</span>
                  <span className="text-[10px] text-text-muted font-semibold block">Data Intelligence</span>
                </div>
              </Link>
              
              {/* Navigation Links */}
              <div className="hidden lg:flex items-center gap-8">
                {/* Features Dropdown */}
                <div 
                  className="relative"
                  onMouseEnter={() => setShowFeaturesDropdown(true)}
                  onMouseLeave={() => setShowFeaturesDropdown(false)}
                >
                  <button className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 hover:text-primary transition-colors py-2">
                    Features
                    <ChevronDown className={`w-4 h-4 transition-transform ${showFeaturesDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  
                  <AnimatePresence>
                    {showFeaturesDropdown && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        transition={{ duration: 0.2 }}
                        className="absolute top-full left-0 mt-2 w-[720px] bg-white rounded-2xl shadow-xl border border-border overflow-hidden"
                      >
                        <div className="p-6">
                          <div className="grid grid-cols-2 gap-4">
                            {/* Clean CSV */}
                            <Link href="#clean-csv" className="group p-5 rounded-xl hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 transition-all border-2 border-transparent hover:border-primary/20">
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center group-hover:scale-110 transition-transform">
                                  <Image src="/icons8/icons8-approval-50.png" alt="" width={32} height={32} />
                                </div>
                                <div className="flex-1">
                                  <h3 className="text-base font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">Clean CSV</h3>
                                  <p className="text-sm text-gray-600 leading-relaxed">Remove duplicates, handle missing values, and fix data quality issues automatically</p>
                                </div>
                              </div>
                            </Link>

                            {/* Charts */}
                            <Link href="#charts" className="group p-5 rounded-xl hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 transition-all border-2 border-transparent hover:border-primary/20">
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center group-hover:scale-110 transition-transform">
                                  <Image src="/icons8/icons8-pie-chart-50.png" alt="" width={32} height={32} />
                                </div>
                                <div className="flex-1">
                                  <h3 className="text-base font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">Charts</h3>
                                  <p className="text-sm text-gray-600 leading-relaxed">Create stunning visualizations with pie charts, bar graphs, and line plots instantly</p>
                                </div>
                              </div>
                            </Link>

                            {/* Data Cleaning */}
                            <Link href="#data-cleaning" className="group p-5 rounded-xl hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 transition-all border-2 border-transparent hover:border-primary/20">
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center group-hover:scale-110 transition-transform">
                                  <Image src="/icons8/icons8-process-50.png" alt="" width={32} height={32} />
                                </div>
                                <div className="flex-1">
                                  <h3 className="text-base font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">Data Cleaning</h3>
                                  <p className="text-sm text-gray-600 leading-relaxed">Transform, validate, and standardize your data with powerful cleaning tools</p>
                                </div>
                              </div>
                            </Link>

                            {/* Analysis */}
                            <Link href="#analysis" className="group p-5 rounded-xl hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 transition-all border-2 border-transparent hover:border-primary/20">
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-100 to-violet-200 flex items-center justify-center group-hover:scale-110 transition-transform">
                                  <Image src="/icons8/icons8-statistics-50.png" alt="" width={32} height={32} />
                                </div>
                                <div className="flex-1">
                                  <h3 className="text-base font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">Analysis</h3>
                                  <p className="text-sm text-gray-600 leading-relaxed">Get comprehensive statistical insights, trends, and patterns from your data</p>
                                </div>
                              </div>
                            </Link>

                            {/* Charts Analysis */}
                            <Link href="#charts-analysis" className="group p-5 rounded-xl hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 transition-all border-2 border-transparent hover:border-primary/20">
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-100 to-pink-200 flex items-center justify-center group-hover:scale-110 transition-transform">
                                  <Image src="/icons8/icons8-line-chart-50.png" alt="" width={32} height={32} />
                                </div>
                                <div className="flex-1">
                                  <h3 className="text-base font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">Charts Analysis</h3>
                                  <p className="text-sm text-gray-600 leading-relaxed">Advanced analytics with interactive charts and real-time data exploration</p>
                                </div>
                              </div>
                            </Link>

                            {/* AI Insights - Bonus */}
                            <Link href="#ai-insights" className="group p-5 rounded-xl hover:bg-gradient-to-br hover:from-purple-50 hover:to-blue-50 transition-all border-2 border-transparent hover:border-primary/20">
                              <div className="flex items-start gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-pink-100 to-purple-200 flex items-center justify-center group-hover:scale-110 transition-transform">
                                  <Image src="/icons8/icons8-chatbot-50.png" alt="" width={32} height={32} />
                                </div>
                                <div className="flex-1">
                                  <h3 className="text-base font-bold text-gray-900 mb-1 group-hover:text-primary transition-colors">AI Insights</h3>
                                  <p className="text-sm text-gray-600 leading-relaxed">AI-powered recommendations and automated insights generation</p>
                                </div>
                              </div>
                            </Link>
                          </div>

                          {/* Bottom CTA */}
                          <div className="mt-6 pt-6 border-t border-border">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-semibold text-gray-900">Ready to get started?</p>
                                <p className="text-xs text-gray-500">Try all features with a free account</p>
                              </div>
                              <Link href="/auth/signup">
                                <button className="px-6 py-2.5 rounded-xl card-gradient text-white text-sm font-semibold hover:shadow-lg transition-all flex items-center gap-2">
                                  Start Free Trial
                                  <ArrowRight className="w-4 h-4" />
                                </button>
                              </Link>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <Link href="/how-it-works" className="text-sm font-semibold text-gray-700 hover:text-primary transition-colors">
                  How It Works
                </Link>
                <Link href="/use-cases" className="text-sm font-semibold text-gray-700 hover:text-primary transition-colors">
                  Use Cases
                </Link>
                <Link href="/pricing" className="text-sm font-semibold text-gray-700 hover:text-primary transition-colors">
                  Pricing
                </Link>
                <Link href="/blog" className="text-sm font-semibold text-gray-700 hover:text-primary transition-colors">
                  Blog
                </Link>
              </div>
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-3">
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
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-40 lg:pb-28">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px] relative">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7 }}
              className="space-y-8"
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full dashboard-card">
                  <Image 
                    src="/icons8/icons8-chatbot-50.png"
                    alt="AI"
                    width={20}
                    height={20}
                  />
                  <span className="text-sm font-bold text-primary">
                    The Data Analyst in Your Browser
                  </span>
                </div>
              </motion.div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.1] tracking-tight text-foreground">
                Your data has answers.
                <br />
                RefineX finds them.
              </h1>

              <p className="text-xl text-text-secondary leading-relaxed max-w-xl">
                Upload any CSV or spreadsheet. RefineX cleans it, understands it, and tells you what it actually means — in plain language. No code. No data science degree. No waiting.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/dashboard/upload">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-8 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
                  >
                    Analyze Your First File Free
                    <motion.div
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <ArrowRight className="w-5 h-5" />
                    </motion.div>
                  </motion.button>
                </Link>
                <Link href="/dashboard/upload">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="px-8 h-14 rounded-2xl dashboard-card font-bold text-lg flex items-center justify-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    Watch 2-min Demo
                  </motion.button>
                </Link>
              </div>

              <div className="flex flex-wrap items-center gap-6 pt-4">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center">
                    <Check className="w-3 h-3 text-primary" strokeWidth={3} />
                  </div>
                  <span className="text-sm font-medium text-text-secondary">No credit card required · Works with CSV, XLSX, XLS · Results in under 60 seconds</span>
                </div>
              </div>
            </motion.div>

            {/* Right Content - Slider with Multiple Charts */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="relative"
            >
              <div className="relative dashboard-card dashboard-card-hover rounded-3xl overflow-hidden min-h-[600px]">
                <AnimatePresence mode="wait">
                  {/* Slide 1: Revenue Pie Chart */}
                  {currentSlide === 0 && (
                    <motion.div
                      key="slide1"
                      initial={{ opacity: 0, x: 100 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.5 }}
                      className="absolute inset-0 p-8 space-y-6"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-1">
                            Revenue Overview
                          </p>
                          <p className="text-4xl font-bold text-foreground">$847,234</p>
                        </div>
                        <motion.div 
                          animate={{ scale: [1, 1.05, 1] }}
                          transition={{ duration: 3, repeat: Infinity }}
                          className="px-4 py-2.5 rounded-xl bg-success/10"
                        >
                          <div className="flex items-center gap-1.5">
                            <Image 
                              src="/icons8/icons8-increase-50.png"
                              alt="Increase"
                              width={18}
                              height={18}
                            />
                            <span className="text-lg font-bold text-success">+24.5%</span>
                          </div>
                        </motion.div>
                      </div>

                      <div className="relative flex items-center justify-center py-4">
                        <svg width="320" height="320" viewBox="0 0 240 240" className="transform -rotate-90">
                          {slices.map((slice, index) => (
                            <motion.path
                              key={index}
                              d={createPieSlice(slice.startAngle, slice.endAngle)}
                              fill={slice.color}
                              animate={{ 
                                scale: activeSlice === index ? 1.08 : 1,
                              }}
                              transition={{ duration: 0.3 }}
                              style={{ 
                                transformOrigin: '120px 120px',
                                filter: activeSlice === index ? 'drop-shadow(0 4px 12px rgba(91, 79, 231, 0.4))' : 'none'
                              }}
                            />
                          ))}
                          <circle cx="120" cy="120" r="50" fill="white" />
                        </svg>
                        
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-center">
                            <p className="text-sm font-semibold text-text-muted mb-1">Total</p>
                            <p className="text-3xl font-bold text-foreground">100%</p>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        {pieData.map((item, index) => (
                          <div
                            key={index}
                            onMouseEnter={() => setActiveSlice(index)}
                            className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                              activeSlice === index ? 'dashboard-card' : 'bg-muted/30'
                            }`}
                          >
                            <div 
                              className="w-10 h-10 rounded-xl flex items-center justify-center"
                              style={{ backgroundColor: `${item.color}20` }}
                            >
                              <Image 
                                src={`/icons8/${item.icon}`}
                                alt={item.label}
                                width={20}
                                height={20}
                              />
                            </div>
                            <div className="flex-1">
                              <p className="text-xs font-semibold text-text-muted">{item.label}</p>
                              <p className="text-lg font-bold text-foreground">{item.value}%</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {/* Slide 2: Hospital Stats */}
                  {currentSlide === 1 && (
                    <motion.div
                      key="slide2"
                      initial={{ opacity: 0, x: 100 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.5 }}
                      className="absolute inset-0 p-8 space-y-6"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-1">
                            Hospital Dashboard
                          </p>
                          <p className="text-4xl font-bold text-foreground">3,504</p>
                          <p className="text-sm text-text-secondary">Total Capacity</p>
                        </div>
                        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                          <Image 
                            src="/icons8/icons8-business-50.png"
                            alt="Hospital"
                            width={32}
                            height={32}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        {hospitalData.map((item, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="p-5 rounded-2xl dashboard-card"
                          >
                            <div className="flex items-center gap-3 mb-4">
                              <div 
                                className="w-12 h-12 rounded-xl flex items-center justify-center"
                                style={{ backgroundColor: `${item.color}15` }}
                              >
                                <Image 
                                  src={`/icons8/${item.icon}`}
                                  alt={item.label}
                                  width={24}
                                  height={24}
                                />
                              </div>
                            </div>
                            <p className="text-xs font-semibold text-text-muted uppercase mb-1">{item.label}</p>
                            <p className="text-3xl font-bold text-foreground mb-2">{item.value}</p>
                            <div className="flex items-center gap-1">
                              <Image 
                                src="/icons8/icons8-positive-dynamic-50.png"
                                alt="Trend"
                                width={14}
                                height={14}
                              />
                              <span className="text-sm font-bold text-success">{item.change}</span>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {/* Slide 3: Monthly Trend Bar Chart */}
                  {currentSlide === 2 && (
                    <motion.div
                      key="slide3"
                      initial={{ opacity: 0, x: 100 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.5 }}
                      className="absolute inset-0 p-8 space-y-6"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-1">
                            Monthly Growth
                          </p>
                          <p className="text-4xl font-bold text-foreground">+127%</p>
                        </div>
                        <div className="px-4 py-2.5 rounded-xl primary-gradient">
                          <span className="text-white font-bold text-sm">YTD</span>
                        </div>
                      </div>

                      <div className="relative rounded-2xl bg-muted/20 p-6 flex-1 min-h-[320px]">
                        <div className="flex items-end justify-between gap-3 pb-8" style={{ height: '240px' }}>
                          {monthlyData.map((data, i) => (
                            <div key={i} className="flex-1 flex flex-col justify-end items-center gap-2">
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: `${(data.value / 100) * 240}px` }}
                                transition={{ duration: 0.8, delay: i * 0.1 }}
                                className="w-full rounded-t-xl relative group cursor-pointer"
                                style={{ 
                                  background: `linear-gradient(180deg, ${i % 2 === 0 ? '#5B4FE7' : '#7367F0'} 0%, ${i % 2 === 0 ? '#7367F0' : '#9785FF'} 100%)`,
                                  boxShadow: '0 4px 12px rgba(91, 79, 231, 0.3)'
                                }}
                              >
                                <motion.div 
                                  initial={{ opacity: 0, y: 10 }}
                                  whileHover={{ opacity: 1, y: -8 }}
                                  className="absolute -top-12 left-1/2 -translate-x-1/2 bg-foreground text-white text-xs font-bold px-3 py-2 rounded-lg whitespace-nowrap shadow-lg"
                                >
                                  {data.value}%
                                </motion.div>
                              </motion.div>
                              <span className="text-xs font-bold text-text-muted absolute -bottom-6">{data.month}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Slide 4: Activity Stats */}
                  {currentSlide === 3 && (
                    <motion.div
                      key="slide4"
                      initial={{ opacity: 0, x: 100 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.5 }}
                      className="absolute inset-0 p-8 space-y-6"
                    >
                      <div>
                        <p className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-1">
                          Weekly Activity
                        </p>
                        <p className="text-4xl font-bold text-foreground">47,523</p>
                        <p className="text-sm text-text-secondary">Total Actions</p>
                      </div>

                      <div className="space-y-4">
                        {[
                          { label: 'Data Uploads', value: 89, icon: 'icons8-documents-50.png', color: '#5B4FE7' },
                          { label: 'AI Analysis', value: 72, icon: 'icons8-chatbot-50.png', color: '#7367F0' },
                          { label: 'Reports Generated', value: 95, icon: 'icons8-statistics-50.png', color: '#9785FF' },
                          { label: 'Team Collaboration', value: 64, icon: 'icons8-collaboration-50.png', color: '#B8AAFF' }
                        ].map((item, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="space-y-2"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div 
                                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                                  style={{ backgroundColor: `${item.color}15` }}
                                >
                                  <Image 
                                    src={`/icons8/${item.icon}`}
                                    alt={item.label}
                                    width={20}
                                    height={20}
                                  />
                                </div>
                                <span className="text-sm font-semibold text-foreground">{item.label}</span>
                              </div>
                              <span className="text-sm font-bold text-foreground">{item.value}%</span>
                            </div>
                            <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${item.value}%` }}
                                transition={{ duration: 1, delay: 0.3 + index * 0.1 }}
                                className="h-full rounded-full"
                                style={{ backgroundColor: item.color }}
                              />
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Slider Navigation Dots */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 z-10">
                  {[0, 1, 2, 3].map((index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentSlide(index)}
                      className={`h-2 rounded-full transition-all ${
                        currentSlide === index ? 'w-8 bg-primary' : 'w-2 bg-text-muted/30'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Floating Stats Cards */}
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 1.2 }}
                className="absolute -left-24 top-20 hidden xl:block z-20"
              >
                <motion.div 
                  animate={{ y: [0, -12, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className="dashboard-card rounded-2xl p-5 shadow-xl backdrop-blur-lg"
                  style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                      <Image 
                        src="/icons8/icons8-people-50.png"
                        alt="Users"
                        width={24}
                        height={24}
                      />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-text-muted uppercase">Users</p>
                      <p className="text-2xl font-bold text-foreground">12.5K</p>
                    </div>
                  </div>
                </motion.div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 1.4 }}
                className="absolute -right-24 bottom-20 hidden xl:block z-20"
              >
                <motion.div 
                  animate={{ y: [0, 12, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="dashboard-card rounded-2xl p-5 shadow-xl backdrop-blur-lg"
                  style={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center">
                      <Image 
                        src="/icons8/icons8-positive-dynamic-50.png"
                        alt="Growth"
                        width={24}
                        height={24}
                      />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-text-muted uppercase">Growth</p>
                      <p className="text-2xl font-bold text-success">+94%</p>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 lg:py-28 relative">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          {/* Animated Workflow Illustration */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.8 }}
            className="mb-24 relative"
          >
            <div className="relative mx-auto max-w-5xl" style={{ height: '400px' }}>
              {/* Left Side - Input Files */}
              <div className="absolute left-0 top-1/2 -translate-y-1/2 space-y-4 z-10">
                {[
                  { label: 'sales.csv', delay: 0 },
                  { label: 'users.csv', delay: 0.15 },
                  { label: 'products.csv', delay: 0.3 },
                  { label: 'orders.csv', delay: 0.45 }
                ].map((file, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -50 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: file.delay }}
                    className="dashboard-card px-4 py-3 rounded-xl backdrop-blur-lg shadow-lg"
                    style={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', width: '140px' }}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                        </svg>
                      </div>
                      <span className="text-xs font-bold text-foreground">{file.label}</span>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Animated Connection Lines to Center */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
                {[0, 1, 2, 3].map((index) => (
                  <motion.path
                    key={index}
                    d={`M 150 ${115 + index * 70} Q 280 ${150 + index * 40} 360 200`}
                    stroke="rgba(99, 102, 241, 0.15)"
                    strokeWidth="1.5"
                    fill="none"
                    strokeDasharray="4,4"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.2, delay: 0.4 + index * 0.1 }}
                  />
                ))}
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity="0.8" />
                  </linearGradient>
                </defs>
              </svg>

              {/* Center - Processing Platform */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 1 }}
                className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
                style={{ zIndex: 5 }}
              >
                <div className="relative">
                  {/* Main Platform Card */}
                  <div 
                    className="dashboard-card p-8 rounded-3xl backdrop-blur-lg shadow-2xl relative overflow-hidden"
                    style={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      width: '450px',
                      height: '270px',
                    
                    }}
                  >
                    {/* Animated Grid Inside */}
                    <div className="grid grid-cols-4 gap-2 mb-4">
                      {Array.from({ length: 16 }).map((_, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0.3 }}
                          animate={{ 
                            opacity: [0.3, 1, 0.3],
                            scale: [1, 1.1, 1]
                          }}
                          transition={{ 
                            duration: 2,
                            delay: i * 0.1,
                            repeat: Infinity,
                            repeatDelay: 1
                          }}
                          className="h-6 rounded-md"
                          style={{ 
                            background: i % 2 === 0 
                              ? 'linear-gradient(135deg, #6366f1, #818cf8)' 
                              : 'linear-gradient(135deg, #818cf8, #a5b4fc)'
                          }}
                        />
                      ))}
                    </div>

                    {/* Platform Label */}
                    <div className="text-center mt-4">
                      <p className="text-xl font-bold text-primary mb-1">Refinex</p>
                      <p className="text-xs text-text-muted font-semibold">AI Processing</p>
                    </div>

                    {/* Processing Icons */}
                    <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-5">
                      {['✓', '⚡', '🔍', '📊'].map((icon, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ 
                            duration: 0.5, 
                            delay: 1.5 + i * 0.2,
                          }}
                          className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-xs"
                        >
                          {icon}
                        </motion.div>
                      ))}
                    </div>

                    {/* Pulse Animation */}
                    <div
                      className="absolute inset-0 rounded-3xl border-2 border-primary pointer-events-none"
                      style={{ opacity: 0.3 }}
                    />
                  </div>
                </div>
              </motion.div>

              {/* Animated Connection Lines to Right */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
                {[0, 1, 2].map((index) => (
                  <motion.path
                    key={`right-${index}`}
                    d={`M 692 200 Q 835 ${[156, 212, 268][index]} 952 ${[145, 225, 304][index]}`}
                    stroke="rgba(99, 102, 241, 0.22)"
                    strokeWidth="1.5"
                    fill="none"
                    strokeDasharray="4,4"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 1.2, delay: 1.2 + index * 0.1 }}
                  />
                ))}
                <defs>
                  <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#a5b4fc" stopOpacity="0.4" />
                  </linearGradient>
                </defs>
              </svg>

              {/* ── RIGHT SIDE – Output Results (same style as left) ── */}
<div className="absolute right-0 top-1/2 -translate-y-1/2 space-y-4 z-20">
  {[
    { label: 'Insights', icon: '💡', badge: 'Ready', delay: 2   },
    { label: 'Charts',   icon: '📊', badge: 'Ready', delay: 2.2 },
    { label: 'Reports',  icon: '📄', badge: 'Ready', delay: 2.4 },
  ].map((output, index) => (
    <motion.div
      key={index}
      initial={{ opacity: 0, x: 50 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay: output.delay }}
      whileHover={{ scale: 1.04, x: -4 }}
      className="dashboard-card px-4 py-3 rounded-xl backdrop-blur-lg shadow-lg cursor-pointer"
      style={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', width: '140px' }}
    >
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-base">
          {output.icon}
        </div>
        <div>
          <span className="text-xs font-bold text-foreground block">{output.label}</span>
          <span className="text-xs text-primary font-semibold">{output.badge}</span>
        </div>
      </div>
    </motion.div>
  ))}
</div>

              {/* Floating Particles */}
              {Array.from({ length: 8 }).map((_, i) => (
                <motion.div
                  key={`particle-${i}`}
                  className="absolute w-2 h-2 rounded-full bg-primary/30"
                  style={{
                    left: `${20 + i * 12}%`,
                    top: `${30 + (i % 3) * 20}%`,
                  }}
                  animate={{
                    y: [0, -20, 0],
                  }}
                  transition={{
                    duration: 3,
                    delay: i * 0.3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold mb-4 text-foreground">
              Simple process, <span className="text-primary">powerful results</span>
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              From raw CSV to actionable insights in three easy steps
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                icon: 'icons8-documents-50.png',
                title: 'Upload CSV',
                description: 'Drag & drop or browse. Support for files up to 1GB on Pro plans.',
              },
              {
                step: '02',
                icon: 'icons8-process-50.png',
                title: 'AI Analysis',
                description: 'Machine learning cleans data, detects patterns, and finds insights automatically.',
              },
              {
                step: '03',
                icon: 'icons8-statistics-50.png',
                title: 'View Results',
                description: 'Interactive dashboards, charts, and recommendations ready to share.',
              }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
              >
                <motion.div
                  whileHover={{ y: -8 }}
                  className="relative h-full dashboard-card dashboard-card-hover rounded-3xl p-8"
                >
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-16 h-16 rounded-2xl primary-gradient flex items-center justify-center">
                      <Image 
                        src={`/icons8/${item.icon}`}
                        alt={item.title}
                        width={32}
                        height={32}
                        className="brightness-0 invert"
                      />
                    </div>
                    <span className="text-6xl font-bold text-foreground/5">{item.step}</span>
                  </div>

                  <h3 className="text-2xl font-bold mb-3 text-foreground">
                    {item.title}
                  </h3>
                  <p className="text-text-secondary leading-relaxed">
                    {item.description}
                  </p>
                </motion.div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 lg:py-28 relative">
        <div className="mx-auto px-6 lg:px-12 max-w-[1400px]">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold mb-4 text-foreground">
              Everything your data team<br />needs in <span className="text-primary">one platform</span>
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              Clean, analyze, visualize, and collaborate — all with complete transparency
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: 'icons8-inspection-50.png',
                title: 'Data Cleaning',
                description: '200+ formulas across 47 column types. Every fix logged, every change reversible.',
                color: '#5B4FE7'
              },
              {
                icon: 'icons8-chatbot-50.png',
                title: 'AI Insights',
                description: 'Plain-language observations specific to your data. Not generic dashboards — real findings.',
                color: '#7367F0'
              },
              {
                icon: 'icons8-area-chart-50.png',
                title: '14 Chart Types',
                description: 'Bar, line, pie, scatter, heatmap, treemap, and more. Customize, export, or embed.',
                color: '#9785FF'
              },
              {
                icon: 'icons8-process-50.png',
                title: 'Formula Verification',
                description: 'Detects calculated columns and checks every row. Catches formula errors before they matter.',
                color: '#5B4FE7'
              },
              {
                icon: 'icons8-increase-50.png',
                title: 'Multi-File Analysis',
                description: 'Upload files across periods. RefineX aligns, compares, and surfaces trends automatically.',
                color: '#7367F0'
              },
              {
                icon: 'icons8-guarantee-50.png',
                title: 'Secure & Private',
                description: 'Encrypted at rest, PII auto-tagged, zero AI training on your data. Delete anytime.',
                color: '#9785FF'
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <motion.div
                  whileHover={{ y: -8 }}
                  className="h-full dashboard-card dashboard-card-hover rounded-3xl p-6"
                >
                  <div 
                    className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
                    style={{ backgroundColor: `${feature.color}15` }}
                  >
                    <Image 
                      src={`/icons8/${feature.icon}`}
                      alt={feature.title}
                      width={28}
                      height={28}
                    />
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-text-secondary leading-relaxed text-sm">
                    {feature.description}
                  </p>
                </motion.div>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-center mt-10"
          >
            <Link href="/features" className="text-primary font-semibold text-sm hover:underline inline-flex items-center gap-1">
              See all 9 features in detail <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 lg:py-28">
        <div className="mx-auto px-6 lg:px-12 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="dashboard-card rounded-3xl p-12 lg:p-16 text-center"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-foreground mb-6">
              Your data is waiting
              <br />
              to tell you something.
            </h2>
            <p className="text-xl text-text-secondary mb-10 max-w-2xl mx-auto">
              Start with your first file. Free. No credit card. No setup.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/signup">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-10 h-14 rounded-2xl card-gradient text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  Analyze Your First File Free
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="/pricing" className="text-primary font-semibold flex items-center justify-center gap-1 px-4 h-14">
                Compare plans <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  )
}
