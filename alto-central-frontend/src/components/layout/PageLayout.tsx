import React from 'react'
import { Header } from './Header'

interface PageLayoutProps {
  children: React.ReactNode
  title: string
  subtitle?: string
  showBack?: boolean
  backTo?: string
}

export function PageLayout({
  children,
  title,
  subtitle,
  showBack,
  backTo,
}: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Header
        title={title}
        subtitle={subtitle}
        showBack={showBack}
        backTo={backTo}
      />
      <main className="p-4 md:p-6">
        {children}
      </main>
    </div>
  )
}
