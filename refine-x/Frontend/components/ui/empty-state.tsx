import React from 'react'
import { FileQuestion, SearchX, Database, Inbox } from 'lucide-react'
import { Button } from './button'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: 'file' | 'search' | 'database' | 'inbox'
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

const icons = {
  file: FileQuestion,
  search: SearchX,
  database: Database,
  inbox: Inbox
}

export function EmptyState({ 
  icon = 'inbox', 
  title, 
  description, 
  action,
  className 
}: EmptyStateProps) {
  const Icon = icons[icon]

  return (
    <div className={cn('flex flex-col items-center justify-center p-12 text-center', className)}>
      <div className="rounded-full bg-muted p-6 mb-4">
        <Icon className="h-12 w-12 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-muted-foreground mb-6 max-w-md">{description}</p>
      )}
      {action && (
        <Button onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  )
}
