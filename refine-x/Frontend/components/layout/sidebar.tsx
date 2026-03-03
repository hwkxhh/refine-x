'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard,
  FolderOpen,
  Lightbulb,
  BarChart3,
  History,
  Users,
  Database,
  Settings, 
  HelpCircle,
  BookOpen,
  Sparkles,
  LucideIcon
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  name: string
  href: string
  icon: LucideIcon
}

const navItems: NavItem[] = [
  { name: 'Home', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Analyses', href: '/dashboard/analyses', icon: FolderOpen },
  { name: 'Datasets', href: '/dashboard/datasets', icon: Database },
  { name: 'Insights', href: '/dashboard/insights', icon: Lightbulb },
  { name: 'Visualizations', href: '/dashboard/visualizations', icon: BarChart3 },
  { name: 'History', href: '/dashboard/history', icon: History },
  { name: 'Team', href: '/dashboard/team', icon: Users },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex w-64 flex-col border-r border-border bg-white/80 backdrop-blur-sm">
      {/* Logo */}
      <div className="h-20 flex items-center gap-3 px-6 border-b border-border">
        <div className="w-10 h-10 flex items-center justify-center">
          <Image 
            src="/images/refinex.svg" 
            alt="Refine Logo"
            width={40}
            height={40}
            className="object-contain"
          />
        </div>
        <div className="leading-tight">
          <p className="text-xl font-bold text-primary">RefineX</p>
          <p className="text-[10px] text-text-muted font-medium">Data Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200',
                isActive
                  ? 'card-gradient text-white shadow-md'
                  : 'text-text-secondary hover:bg-muted/30 hover:text-foreground'
              )}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Footer Links */}
      <div className="px-4 py-6 border-t border-border">
        <Link
          href="/dashboard/billing"
          className="mb-2 flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-text-secondary hover:bg-muted/30 hover:text-foreground transition-all duration-200"
        >
          <Sparkles className="w-5 h-5" />
          <span>Upgrade to Pro</span>
        </Link>
        <Link
          href="/dashboard/help"
          className="mb-2 flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-text-secondary hover:bg-muted/30 hover:text-foreground transition-all duration-200"
        >
          <BookOpen className="w-5 h-5" />
          <span>Documentation</span>
        </Link>
        <Link
          href="/dashboard/help"
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-text-secondary hover:bg-muted/30 hover:text-foreground transition-all duration-200"
        >
          <HelpCircle className="w-5 h-5" />
          <span>Help & Support</span>
        </Link>
      </div>
    </aside>
  )
}
