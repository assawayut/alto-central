import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Thermometer, Zap, Activity } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Site } from '@/types/site'

interface BuildingCardProps {
  site: Site
}

export function BuildingCard({ site }: BuildingCardProps) {
  const navigate = useNavigate()

  const statusVariant = {
    active: 'success',
    warning: 'warning',
    alarm: 'danger',
    offline: 'muted',
  } as const

  const statusLabel = {
    active: 'Active',
    warning: 'Warning',
    alarm: 'Alarm',
    offline: 'Offline',
  }

  const typeIcon = {
    hotel: '🏨',
    office: '🏢',
    mall: '🛒',
    hospital: '🏥',
    industrial: '🏭',
  }

  return (
    <Card
      className="p-4 cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => navigate(`/site/${site.id}`)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{typeIcon[site.type]}</span>
          <div>
            <h3 className="font-semibold text-foreground text-sm">{site.name}</h3>
            <p className="text-xs text-muted">{site.chillerCount} Chillers</p>
          </div>
        </div>
        <Badge variant={statusVariant[site.status]}>
          {statusLabel[site.status]}
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-[#F9FAFF] rounded-md p-2">
          <div className="flex items-center justify-center gap-1 text-muted mb-1">
            <Activity className="h-3 w-3" />
            <span className="text-[10px]">Efficiency</span>
          </div>
          <p className={`text-sm font-bold ${site.efficiency <= 0.7 ? 'text-[#14B8B4]' : site.efficiency <= 0.8 ? 'text-[#FEBE54]' : 'text-[#EF4337]'}`}>
            {site.efficiency.toFixed(2)}
          </p>
          <p className="text-[10px] text-muted">kW/RT</p>
        </div>

        <div className="bg-[#F9FAFF] rounded-md p-2">
          <div className="flex items-center justify-center gap-1 text-muted mb-1">
            <Zap className="h-3 w-3" />
            <span className="text-[10px]">Power</span>
          </div>
          <p className="text-sm font-bold text-foreground">{site.power}</p>
          <p className="text-[10px] text-muted">kW</p>
        </div>

        <div className="bg-[#F9FAFF] rounded-md p-2">
          <div className="flex items-center justify-center gap-1 text-muted mb-1">
            <Thermometer className="h-3 w-3" />
            <span className="text-[10px]">Load</span>
          </div>
          <p className="text-sm font-bold text-foreground">{site.coolingLoad}</p>
          <p className="text-[10px] text-muted">RT</p>
        </div>
      </div>
    </Card>
  )
}
