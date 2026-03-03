import React from 'react'
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error'
  title?: string
  dismissible?: boolean
  onDismiss?: () => void
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', title, children, dismissible, onDismiss, ...props }, ref) => {
    const variants = {
      info: {
        container: 'bg-primary/10 border-primary/20 text-primary',
        icon: Info
      },
      success: {
        container: 'bg-success/10 border-success/20 text-success',
        icon: CheckCircle
      },
      warning: {
        container: 'bg-warning/10 border-warning/20 text-warning',
        icon: AlertTriangle
      },
      error: {
        container: 'bg-error/10 border-error/20 text-error',
        icon: AlertCircle
      }
    }

    const { container, icon: Icon } = variants[variant]

    return (
      <div
        ref={ref}
        className={cn(
          'relative rounded-lg border p-4',
          container,
          className
        )}
        {...props}
      >
        <div className="flex gap-3">
          <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            {title && (
              <h5 className="mb-1 font-semibold">{title}</h5>
            )}
            <div className="text-sm opacity-90">{children}</div>
          </div>
          {dismissible && onDismiss && (
            <button
              onClick={onDismiss}
              className="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    )
  }
)

Alert.displayName = 'Alert'

export { Alert }
