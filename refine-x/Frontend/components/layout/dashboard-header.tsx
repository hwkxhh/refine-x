'use client'

import { useState } from 'react'
import { Bell, ChevronDown, Search, Menu, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { useAuth } from '@/lib/auth/use-auth'

export function DashboardHeader() {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const { user, logout } = useAuth()

  const userName = user?.name || 'User'
  const userEmail = user?.email || ''
  const initials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <header className="h-20 border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-40">
      <div className="h-full px-4 sm:px-6 flex items-center justify-between gap-4">
        {/* Left: Mobile Menu + Search */}
        <div className="flex items-center gap-4 flex-1">
          <button className="md:hidden p-2 -ml-2 text-gray-600 hover:text-foreground">
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="hidden sm:flex items-center gap-2 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search datasets, insights, or analyses..."
                className="w-full h-11 pl-12 pr-4 rounded-xl bg-[#F5F6FA] border border-[#E6E7F0] text-sm text-gray-700 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/30 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Center: Workspace Dropdown (hidden on mobile) */}
        <div className="hidden lg:flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#F5F6FA] border border-[#E6E7F0] hover:bg-gray-50 transition-all">
            <span className="text-sm font-semibold text-gray-700">Rider Payments</span>
            <ChevronDown className="w-4 h-4 text-gray-500" />
          </button>
          <button className="text-xs text-primary font-semibold hover:underline">+ New Workspace</button>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          <Link href="/dashboard/upload">
            <Button size="sm" className="hidden sm:flex h-11 px-5 rounded-xl card-gradient text-white font-semibold shadow-sm hover:shadow-md">
              <Upload className="w-4 h-4 mr-2" />
              + New Analysis
            </Button>
          </Link>

          <button className="relative p-2.5 w-11 h-11 rounded-xl bg-[#F5F6FA] border border-[#E6E7F0] hover:bg-gray-50 transition-all flex items-center justify-center">
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 h-11 pl-3 pr-4 rounded-xl bg-[#F5F6FA] border border-[#E6E7F0] hover:bg-gray-50 transition-all"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-sm font-medium">
                {initials}
              </div>
              <ChevronDown className="w-4 h-4 text-gray-500 hidden sm:block" />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-card border border-border rounded-lg shadow-lg py-2">
                <div className="px-4 py-2 border-b border-border">
                  <p className="text-sm font-medium text-foreground">{userName}</p>
                  <p className="text-xs text-text-muted">{userEmail}</p>
                </div>
                <Link href="/dashboard/settings" className="block px-4 py-2 text-sm text-text-secondary hover:bg-muted">
                  Profile
                </Link>
                <Link href="/dashboard/settings" className="block px-4 py-2 text-sm text-text-secondary hover:bg-muted">
                  Settings
                </Link>
                <Link href="/dashboard/billing" className="block px-4 py-2 text-sm text-text-secondary hover:bg-muted">
                  Billing
                </Link>
                <Link href="/dashboard/help" className="block px-4 py-2 text-sm text-text-secondary hover:bg-muted">
                  Help & Support
                </Link>
                <hr className="my-2 border-border" />
                <button
                  onClick={() => { setShowUserMenu(false); logout(); }}
                  className="block w-full text-left px-4 py-2 text-sm text-text-secondary hover:bg-muted"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
