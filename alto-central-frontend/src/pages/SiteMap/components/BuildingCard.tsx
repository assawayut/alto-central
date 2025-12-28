import { useNavigate } from 'react-router-dom'
import { Thermometer, Zap, Activity } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { SiteConfig } from '@/config/sites'

interface BuildingCardProps {
  site: SiteConfig
  // Mock data for display - in real app this would come from API
  stats?: {
    status: 'active' | 'warning' | 'alarm' | 'offline'
    efficiency: number
    power: number
    coolingLoad: number
  }
}

// Mock stats generator - in real app this would be fetched from API
const getMockStats = (siteId: string) => {
  // Generate consistent mock data based on site_id
  const hash = siteId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return {
    status: 'active' as const,
    efficiency: 0.6 + (hash % 30) / 100,
    power: 70 + (hash % 50),
    coolingLoad: 80 + (hash % 40),
  };
};

export function BuildingCard({ site, stats }: BuildingCardProps) {
  const navigate = useNavigate()

  // Use provided stats or generate mock ones
  const displayStats = stats || getMockStats(site.site_id);

  const statusVariant = {
    active: 'success',
    warning: 'secondary',
    alarm: 'destructive',
    offline: 'outline',
  } as const

  const statusLabel = {
    active: 'Active',
    warning: 'Warning',
    alarm: 'Alarm',
    offline: 'Offline',
  }

  return (
    <Card
      className="p-4 cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => navigate(`/site/${site.site_id}`)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-lg bg-[#E5F2FF] flex items-center justify-center">
            <span className="text-sm font-bold text-primary">{site.site_code}</span>
          </div>
          <div>
            <h3 className="font-semibold text-foreground text-sm">{site.site_name}</h3>
            <p className="text-xs text-muted">{site.site_id}</p>
          </div>
        </div>
        <Badge variant={statusVariant[displayStats.status]}>
          {statusLabel[displayStats.status]}
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-[#F9FAFF] rounded-md p-2">
          <div className="flex items-center justify-center gap-1 text-muted mb-1">
            <Activity className="h-3 w-3" />
            <span className="text-[10px]">Efficiency</span>
          </div>
          <p className={`text-sm font-bold ${displayStats.efficiency <= 0.7 ? 'text-[#14B8B4]' : displayStats.efficiency <= 0.8 ? 'text-[#FEBE54]' : 'text-[#EF4337]'}`}>
            {displayStats.efficiency.toFixed(2)}
          </p>
          <p className="text-[10px] text-muted">kW/RT</p>
        </div>

        <div className="bg-[#F9FAFF] rounded-md p-2">
          <div className="flex items-center justify-center gap-1 text-muted mb-1">
            <Zap className="h-3 w-3" />
            <span className="text-[10px]">Power</span>
          </div>
          <p className="text-sm font-bold text-foreground">{displayStats.power}</p>
          <p className="text-[10px] text-muted">kW</p>
        </div>

        <div className="bg-[#F9FAFF] rounded-md p-2">
          <div className="flex items-center justify-center gap-1 text-muted mb-1">
            <Thermometer className="h-3 w-3" />
            <span className="text-[10px]">Load</span>
          </div>
          <p className="text-sm font-bold text-foreground">{displayStats.coolingLoad}</p>
          <p className="text-[10px] text-muted">RT</p>
        </div>
      </div>
    </Card>
  )
}
