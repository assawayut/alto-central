import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ArrowLeft, Settings, Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface HeaderProps {
  title: string
  subtitle?: string
  showBack?: boolean
  backTo?: string
}

export function Header({ title, subtitle, showBack, backTo = '/' }: HeaderProps) {
  const location = useLocation()
  const isMapPage = location.pathname === '/'

  return (
    <header className="h-16 bg-white border-b border-border flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-4">
        {showBack && (
          <Link to={backTo}>
            <Button variant="ghost" size="icon" className="text-muted hover:text-foreground">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
        )}
        <div>
          <h1 className="text-lg font-semibold text-foreground">{title}</h1>
          {subtitle && (
            <p className="text-sm text-muted">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {!isMapPage && (
          <div className="text-sm text-muted mr-4">
            <span className="text-foreground font-medium">ALTO</span> HVAC Central
          </div>
        )}
        <Button variant="ghost" size="icon" className="text-muted hover:text-foreground">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" className="text-muted hover:text-foreground">
          <Settings className="h-5 w-5" />
        </Button>
      </div>
    </header>
  )
}
