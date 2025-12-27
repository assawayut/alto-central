import { useRef, useEffect, useState } from "react";
import { useRealtime } from '@/features/realtime';
import { cn } from "@/utils/cn"; // Update the import path to the correct location
import { entityService, OntologyEntity } from "@/features/ontology";


export type ChillerPlantVariant = 'air-cooled' | 'water-cooled';

type BoxType = 'main' | 'temp' | 'flow';
type PathType = 'chr' | 'chs' | 'cdr' | 'cds';
type PathDirection = 'horizontal-first' | 'vertical-first';

interface BoxConfig {
  type: BoxType;
  position: {
    left: string;
    top: string;
  };
  label: string | string[];
  bgColor?: string;
  textColor?: string;
  width?: number;
}

interface PathConfig {
  from: string;
  to: string;
  type: PathType;
  direction: PathDirection;
}

interface StyleConfig {
  width: number;
  padding: number;
  borderRadius: number;
  fontSize: number;
  lineHeight: number;
}

interface ColorConfig {
  bg: string;
  light: string;
}

interface DiagramConfig {
  styles: {
    main: StyleConfig;
    temp: StyleConfig;
    flow: StyleConfig;
  };
  colors: {
    chr: ColorConfig;
    chs: ColorConfig;
    cdr: ColorConfig;
    cds: ColorConfig;
  };
  animation: {
    duration: string;
    strokeDashArray: number;
    strokeWidth: {
      base: number;
      animated: number;
    };
  };
  boxes: {
    chillerPlant: BoxConfig;
    building: BoxConfig;
    flowCHW: BoxConfig;
    chs: BoxConfig;
    chr: BoxConfig;
    flowCDW?: BoxConfig;
    cds?: BoxConfig;
    cdr?: BoxConfig;
    coolingTower?: BoxConfig;
    weatherStation: BoxConfig;
  };
  paths: PathConfig[];
}

const colors = {
  chr: {
    bg: '#8BC6FF',
    light: '#C0E8FF',
  },
  chs: {
    bg: '#065BA9',
    light: '#55A6F2',
  },
  cdr: {
    bg: '#F88D40',
    light: '#FFD4C8',
  },
  cds: {
    bg: '#FEBE54',
    light: '#FFFAC4',
  },
};

// Create separate box configurations for each variant
const boxConfigByVariant = {
  'water-cooled': {
    weatherStation: {
      type: 'main' as const,
      position: { left: '20%', top: '90%' },
      label: ['Weather', 'Station'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
    chillerPlant: {
      type: 'main' as const,
      position: { left: '50%', top: '50%' },
      label: ['Chiller Plant'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
    building: {
      type: 'main' as const,
      position: { left: '85%', top: '50%' },
      label: ['Building'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
    flowCHW: {
      type: 'flow' as const,
      position: { left: '75%', top: '80%' },
      label: 'Flow',
      bgColor: '#59D1CE',
      textColor: 'text-[#272E3B]',
    },
    flowCDW: {
      type: 'flow' as const,
      position: { left: '37%', top: '80%' },
      label: 'Flow',
      bgColor: '#FF9E00',
      textColor: 'text-[#272E3B]',
    },
    chs: {
      type: 'temp' as const,
      position: { left: '62%', top: '80%' },
      label: 'CHS',
      bgColor: colors.chs.bg,
      textColor: 'text-white',
    },
    chr: {
      type: 'temp' as const,
      position: { left: '68%', top: '10%' },
      label: 'CHR',
      bgColor: colors.chr.bg,
      textColor: 'text-white',
    },
    cds: {
      type: 'temp' as const,
      position: { left: '25%', top: '80%' },
      label: 'CDS',
      bgColor: colors.cds.bg,
      textColor: 'text-white',
    },
    cdr: {
      type: 'temp' as const,
      position: { left: '25%', top: '10%' },
      label: 'CDR',
      bgColor: colors.cdr.bg,
      textColor: 'text-white',
    },
    coolingTower: {
      type: 'main' as const,
      position: { left: '15%', top: '50%' },
      label: ['Cooling', 'Tower'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
  },
  'air-cooled': {
    weatherStation: {
      type: 'main' as const,
      position: { left: '20%', top: '90%' },
      label: ['Weather', 'Station'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
    chillerPlant: {
      type: 'main' as const,
      position: { left: '20%', top: '50%' }, // Moved left since no condenser loop
      label: ['Chiller Plant'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
    building: {
      type: 'main' as const,
      position: { left: '85%', top: '50%' },
      label: ['Building'],
      bgColor: 'white',
      textColor: 'text-primary-dark-dark',
    },
    flowCHW: {
      type: 'flow' as const,
      position: { left: '75%', top: '80%' },
      label: 'Flow',
      bgColor: '#59D1CE',
      textColor: 'text-[#272E3B]',
    },
    chs: {
      type: 'temp' as const,
      position: { left: '55%', top: '80%' }, // Adjusted for better spacing
      label: 'CHS',
      bgColor: colors.chs.bg,
      textColor: 'text-white',
    },
    chr: {
      type: 'temp' as const,
      position: { left: '55%', top: '10%' }, // Adjusted for better spacing
      label: 'CHR',
      bgColor: colors.chr.bg,
      textColor: 'text-white',
    },
  },
};

// Update the diagram config to use variant-specific box positions
const getDiagramConfig = (variant: ChillerPlantVariant): DiagramConfig => ({
  styles: {
    main: {
      width: 100,
      padding: 8,
      borderRadius: 10,
      fontSize: 12,
      lineHeight: 18,
    },
    temp: {
      width: 54,
      padding: 2,
      borderRadius: 6,
      fontSize: 10,
      lineHeight: 15,
    },
    flow: {
      width: 54,
      padding: 2,
      borderRadius: 6,
      fontSize: 10,
      lineHeight: 15,
    }
  },
  colors,
  animation: {
    duration: '1s',
    strokeDashArray: 20,
    strokeWidth: {
      base: 15,
      animated: 10,
    },
  },
  boxes: boxConfigByVariant[variant],
  paths: [], // This will be populated dynamically based on variant
});

interface ChillerPlantDiagramProps {
  data: any;
}

const getPathsConfig = (variant: ChillerPlantVariant): PathConfig[] => {
  const chilledWaterPaths: PathConfig[] = [
    { from: 'building', to: 'chr', type: 'chr', direction: 'vertical-first' },
    { from: 'chr', to: 'chillerPlantRight', type: 'chr', direction: 'horizontal-first' },
    { from: 'chillerPlantRight', to: 'chs', type: 'chs', direction: 'vertical-first' },
    { from: 'chs', to: 'flowCHW', type: 'chs', direction: 'horizontal-first' },
    { from: 'flowCHW', to: 'building', type: 'chs', direction: 'horizontal-first' },
  ];

  const condenserWaterPaths: PathConfig[] = [
    { from: 'chillerPlantLeft', to: 'cdr', type: 'cdr', direction: 'vertical-first' },
    { from: 'cdr', to: 'coolingTower', type: 'cdr', direction: 'horizontal-first' },
    { from: 'coolingTower', to: 'cds', type: 'cds', direction: 'vertical-first' },
    { from: 'cds', to: 'chillerPlantLeft', type: 'cds', direction: 'horizontal-first' },
  ];

  return variant === 'water-cooled' 
    ? [...chilledWaterPaths, ...condenserWaterPaths]
    : chilledWaterPaths;
};

const ChillerPlantDiagram = () => {
  // Determine variant based on site
  const variant: ChillerPlantVariant = 'water-cooled';
  const containerRef = useRef<HTMLDivElement>(null);
  const chrBoxRef = useRef<HTMLDivElement>(null);
  const chillerPlantBoxref = useRef<HTMLDivElement>(null);
  const buildingBoxRef = useRef<HTMLDivElement>(null);
  const chsBoxRef = useRef<HTMLDivElement>(null);
  const flowBoxRef = useRef<HTMLDivElement>(null);
  const coolingTowerBoxRef = useRef<HTMLDivElement>(null);
  const cdwrBoxRef = useRef<HTMLDivElement>(null);
  const cdwsBoxRef = useRef<HTMLDivElement>(null);
  const flowCDWBoxRef = useRef<HTMLDivElement>(null);
  const [paths, setPaths] = useState<{[key: string]: string}>({});

  // Use the real-time context to get plant data
  const { realtimeData, getValue, getUnit } = useRealtime();
  const [chillers, setChillers] = useState<OntologyEntity[]>([]);
  
  // Fetch chillers using ontology API
  useEffect(() => {
    const fetchChillers = async () => {
      try {
        const waterEntities = await entityService.queryEntities({
          tag_filter: 'model:chiller',
          expand: ['tags', 'latest_data']
        });
        setChillers(waterEntities);
      } catch (error) {
        console.error('Error fetching chillers:', error);
      }
    };
    
    fetchChillers();
  }, []);
  
  // Get plant data from the real-time context
  const chr = getValue('chilled_water_loop', 'return_water_temperature');
  const chs = getValue('chilled_water_loop', 'supply_water_temperature');
  
  // Calculate average setpoint from active chillers
  const activeChillers = chillers.filter(chiller => getValue(chiller.entity_id, 'status_read') === 1);
  const chs_sp = activeChillers.length > 0 
    ? activeChillers.reduce((sum, chiller) => sum + (getValue(chiller.entity_id, 'setpoint_read') || 0), 0) / activeChillers.length
    : null;

  const flowCHW = getValue('chilled_water_loop', 'flow_rate');
  const flowCDW = getValue('condenser_water_loop', 'flow_rate');
  const cooling_rate = getValue('plant', 'cooling_rate');
  const heat_reject = getValue('plant', 'heat_reject');
  const cdwr = getValue('condenser_water_loop', 'return_water_temperature');
  const cdws = getValue('condenser_water_loop', 'supply_water_temperature');
  const diagramConfig = getDiagramConfig(variant);

  const renderWaterCooledComponents = () => {
    return (
      <>
        {/* CDR Box */}
        <div
          ref={cdwrBoxRef}
          className={cn(
            "absolute -translate-x-1/2 flex flex-col rounded-md bg-white overflow-hidden shadow-sm min-w-[54px]",
          )}
          style={{
            left: diagramConfig.boxes.cdr?.position.left,
            top: diagramConfig.boxes.cdr?.position.top,
          }}
        >
          <div
            className="w-full text-white font-semibold text-xs p-0.5 text-center"
            style={{ backgroundColor: diagramConfig.colors.cdr.bg }}
          >
            CDR
          </div>
          <div className="text-xs text-[#272E3B] font-semibold p-0.5 text-center">
            {cdwr === null || cdwr === undefined ? "-" : `${cdwr.toFixed(1)} ${getUnit('condenser_water_loop', 'return_water_temperature')}`}
          </div>
        </div>

        {/* Cooling Tower Box */}
        <div
          ref={coolingTowerBoxRef}
          className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col justify-center items-center w-[100px] bg-white rounded-lg p-2 border border-gray-200 dark:border-gray-700 shadow-sm"
          style={{
            left: diagramConfig.boxes.coolingTower?.position.left,
            top: diagramConfig.boxes.coolingTower?.position.top,
          }}
        >
          <p className="text-xs leading-tight font-semibold text-primary-dark text-center">Heat Reject</p>
          <div className="flex py-px px-1.5 items-center gap-1 rounded-md bg-[#EDEFF9] mt-1 justify-center w-full">
            <div className="flex items-center">
              <span className="text-[#272E3B] text-sm leading-tight font-semibold mr-0.5">
                {heat_reject === null || heat_reject === undefined ? "-" : heat_reject.toFixed(0)}
              </span>
              <span className="text-[#272E3B] text-xs leading-tight">
                Ton
              </span>
            </div>
          </div>
        </div>

        {/* CDS Box */}
        <div
          ref={cdwsBoxRef}
          className={cn(
            "absolute -translate-x-1/2 flex flex-col rounded-md bg-white overflow-hidden shadow-sm min-w-[54px]",
          )}
          style={{
            left: diagramConfig.boxes.cds?.position.left,
            top: diagramConfig.boxes.cds?.position.top,
          }}
        >
          <div
            className="w-full text-[#212529] font-semibold text-xs p-0.5 text-center"
            style={{ backgroundColor: diagramConfig.colors.cds.bg }}
          >
            CDS
          </div>
          <div className="text-xs text-[#272E3B] font-semibold p-0.5 text-center">
            {cdws === null || cdws === undefined ? "-" : `${cdws.toFixed(1)} ${getUnit('condenser_water_loop', 'supply_water_temperature')}`}
          </div>
        </div>

        {/* Flow CDW Box */}
        <div
          ref={flowCDWBoxRef}
          className={cn(
            "absolute -translate-x-1/2 flex flex-col rounded-md bg-white overflow-hidden shadow-sm min-w-[54px]",
          )}
          style={{
            left: diagramConfig.boxes.flowCDW?.position.left,
            top: diagramConfig.boxes.flowCDW?.position.top,
          }}
        >
          <div 
            className="w-full text-[#272E3B] font-semibold text-xs p-0.5 text-center"
            style={{ backgroundColor: '#FF9E00' }}
          >
            Flow
          </div>
          <div className="text-xs text-[#272E3B] font-semibold p-0.5 text-center">
            {flowCDW === null || flowCDW === undefined ? "-" : `${flowCDW.toFixed(0)} ${getUnit('condenser_water_loop', 'flow_rate')}`}
          </div>
        </div>
      </>
    );
  };

  useEffect(() => {
    const updatePaths = () => {
      const positions = getBoxPositions();
      if (!positions) return;

      const newPaths = getPathsConfig(variant).reduce((acc, pathConfig) => {
        const fromPos = positions[pathConfig.from as keyof typeof positions];
        const toPos = positions[pathConfig.to as keyof typeof positions];
        if (!fromPos || !toPos) return acc;
        
        const pathKey = `${pathConfig.from}To${pathConfig.to}`;
        acc[pathKey] = getPathBetweenPoints(fromPos, toPos, pathConfig.direction);
        return acc;
      }, {} as { [key: string]: string });

      setPaths(newPaths);
    };

    updatePaths();
    window.addEventListener('resize', updatePaths);
    const interval = setInterval(updatePaths, 1000);

    return () => {
      window.removeEventListener('resize', updatePaths);
      clearInterval(interval);
    };
  }, [variant]);

  // Refresh paths when realtimeData changes
  useEffect(() => {
    // Define a function to update paths when realtimeData changes
    const refreshPaths = () => {
      const positions = getBoxPositions();
      if (!positions) return;

      const newPaths = getPathsConfig(variant).reduce((acc, pathConfig) => {
        const fromPos = positions[pathConfig.from as keyof typeof positions];
        const toPos = positions[pathConfig.to as keyof typeof positions];
        if (!fromPos || !toPos) return acc;
        
        const pathKey = `${pathConfig.from}To${pathConfig.to}`;
        acc[pathKey] = getPathBetweenPoints(fromPos, toPos, pathConfig.direction);
        return acc;
      }, {} as { [key: string]: string });

      setPaths(newPaths);
    };

    if (containerRef.current) {
      refreshPaths();
    }
  }, [realtimeData, variant]);

  // Helper functions for position and path calculations
  const getRelativePosition = (element: HTMLElement | null) => {
    if (!element || !containerRef.current) return { x: 0, y: 0 };
    const containerRect = containerRef.current.getBoundingClientRect();
    const rect = element.getBoundingClientRect();
    return {
      x: rect.left - containerRect.left + rect.width / 2,
      y: rect.top - containerRect.top + rect.height / 2
    };
  };

  const getPathBetweenPoints = (from: { x: number, y: number }, to: { x: number, y: number }, direction: PathDirection) => {
    if (direction === 'horizontal-first') {
      return `M ${from.x} ${from.y} L ${to.x} ${from.y} L ${to.x} ${to.y}`;
    } else {
      return `M ${from.x} ${from.y} L ${from.x} ${to.y} L ${to.x} ${to.y}`;
    }
  };

  // Update the boxPositions calculation
  const getBoxPositions = () => {
    if (!containerRef.current || !chrBoxRef.current || !chillerPlantBoxref.current || 
        !buildingBoxRef.current || !chsBoxRef.current || !flowBoxRef.current) {
      return null;
    }

    const basePositions = {
      building: getRelativePosition(buildingBoxRef.current),
      chr: getRelativePosition(chrBoxRef.current),
      chillerPlant: getRelativePosition(chillerPlantBoxref.current),
      chs: getRelativePosition(chsBoxRef.current),
      flowCHW: getRelativePosition(flowBoxRef.current),
    };

    if (variant === 'water-cooled') {
      if (!coolingTowerBoxRef.current || !cdwrBoxRef.current || !cdwsBoxRef.current || !flowCDWBoxRef.current) {
        return null;
      }

      return {
        ...basePositions,
        chillerPlantLeft: {
          ...getRelativePosition(chillerPlantBoxref.current),
          x: getRelativePosition(chillerPlantBoxref.current).x - 20,
        },
        chillerPlantRight: {
          ...getRelativePosition(chillerPlantBoxref.current),
          x: getRelativePosition(chillerPlantBoxref.current).x + 20,
        },
        coolingTower: getRelativePosition(coolingTowerBoxRef.current),
        cdr: getRelativePosition(cdwrBoxRef.current),
        cds: getRelativePosition(cdwsBoxRef.current),
        flowCDW: getRelativePosition(flowCDWBoxRef.current),
      };
    }

    return {
      ...basePositions,
      chillerPlantRight: getRelativePosition(chillerPlantBoxref.current),
    };
  };

  return (
    <div className="w-full">
      <div ref={containerRef} className="relative w-full aspect-[2/1]">
        <style>
          {`
            @keyframes flow {
              0% {
                stroke-dashoffset: ${diagramConfig.animation.strokeDashArray * 2};
              }
              100% {
                stroke-dashoffset: 0;
              }
            }
            .flow-path-chr-dark {
              stroke: ${diagramConfig.colors.chr.bg};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCHW && flowCHW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
            }
            .flow-path-chr-light {
              stroke: ${diagramConfig.colors.chr.light};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCHW && flowCHW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
              stroke-dashoffset: ${diagramConfig.animation.strokeDashArray};
            }
            .flow-path-chs-dark {
              stroke: ${diagramConfig.colors.chs.bg};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCHW && flowCHW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
            }
            .flow-path-chs-light {
              stroke: ${diagramConfig.colors.chs.light};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCHW && flowCHW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
              stroke-dashoffset: ${diagramConfig.animation.strokeDashArray};
            }
            .flow-path-cdr-dark {
              stroke: ${diagramConfig.colors.cdr.bg};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCDW && flowCDW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
            }
            .flow-path-cdr-light {
              stroke: ${diagramConfig.colors.cdr.light};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCDW && flowCDW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
              stroke-dashoffset: ${diagramConfig.animation.strokeDashArray};
            }
            .flow-path-cds-dark {
              stroke: ${diagramConfig.colors.cds.bg};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCDW && flowCDW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
            }
            .flow-path-cds-light {
              stroke: ${diagramConfig.colors.cds.light};
              stroke-dasharray: ${diagramConfig.animation.strokeDashArray};
              animation: ${flowCDW && flowCDW >= 1 ? `flow ${diagramConfig.animation.duration} linear infinite` : 'none'};
              stroke-dashoffset: ${diagramConfig.animation.strokeDashArray};
            }
          `}
        </style>
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
          {Object.entries(paths).map(([key, path], index) => {
            // Find the corresponding path config
            const pathConfig = getPathsConfig(variant).find(p => `${p.from}To${p.to}` === key);
            if (!pathConfig) return null;

            const pathType = pathConfig.type;
            const darkClass = `flow-path-${pathType}-dark`;
            const lightClass = `flow-path-${pathType}-light`;
            const baseColor = diagramConfig.colors[pathType].bg;

            return (
              <g key={index}>
                <path
                  d={path}
                  fill="none"
                  stroke={baseColor}
                  strokeWidth={diagramConfig.animation.strokeWidth.base}
                  strokeLinejoin="round"
                />
                <path
                  d={path}
                  fill="none"
                  strokeWidth={diagramConfig.animation.strokeWidth.animated}
                  strokeLinejoin="round"
                  className={darkClass}
                />
                <path
                  d={path}
                  fill="none"
                  strokeWidth={diagramConfig.animation.strokeWidth.animated}
                  strokeLinejoin="round"
                  className={lightClass}
                />
              </g>
            );
          })}
        </svg>

        {/* CHR Box */}
        <div
          ref={chrBoxRef}
          className={cn(
            "absolute -translate-x-1/2 flex flex-col rounded-md bg-white overflow-hidden shadow-sm min-w-[54px]",
          )}
          style={{
            left: diagramConfig.boxes.chr.position.left,
            top: diagramConfig.boxes.chr.position.top,
          }}
        >
          <div
            className="w-full text-white font-semibold text-xs p-0.5 text-center"
            style={{ backgroundColor: diagramConfig.colors.chr.bg }}
          >
            {diagramConfig.boxes.chr.label}
          </div>
          <div className="text-xs text-[#272E3B] font-semibold p-0.5 text-center">
            {chr === null || chr === undefined ? "-" : `${chr.toFixed(1)} ${getUnit('chilled_water_loop', 'return_water_temperature')}`}
          </div>
        </div>

        {/* CHS Box */}
        <div
          ref={chsBoxRef}
          className={cn(
            "absolute -translate-x-1/2 flex flex-col rounded-md bg-white overflow-hidden shadow-sm min-w-[54px]",
          )}
          style={{
            left: diagramConfig.boxes.chs.position.left,
            top: diagramConfig.boxes.chs.position.top,
          }}
        >
          <div
            className="w-full text-white font-semibold text-xs p-0.5 text-center"
            style={{ backgroundColor: diagramConfig.colors.chs.bg }}
          >
            {diagramConfig.boxes.chs.label}
          </div>
          <div className="text-xs text-[#272E3B] font-semibold p-0.5 text-center">
            {chs === null || chs === undefined ? "-" : `${chs.toFixed(1)} ${getUnit('chilled_water_loop', 'supply_water_temperature')}`}
          </div>
        </div>

        {/* Flow CHW Box */}
        <div
          ref={flowBoxRef}
          className={cn(
            "absolute -translate-x-1/2 flex flex-col rounded-md bg-white overflow-hidden shadow-sm min-w-[54px]",
          )}
          style={{
            left: diagramConfig.boxes.flowCHW.position.left,
            top: diagramConfig.boxes.flowCHW.position.top,
          }}
        >
          <div 
            className="w-full text-[#272E3B] font-semibold text-xs p-0.5 text-center"
            style={{ backgroundColor: diagramConfig.boxes.flowCHW.bgColor }}
          >
            {diagramConfig.boxes.flowCHW.label}
          </div>
          <div className="text-xs text-[#272E3B] font-semibold p-0.5 text-center">
            {flowCHW === null || flowCHW === undefined ? "-" : `${flowCHW.toFixed(0)} ${getUnit('chilled_water_loop', 'flow_rate')}`}
          </div>
        </div>

        {/* Chiller Plant Box */}
        <div
          ref={chillerPlantBoxref}
          className={cn(
            "absolute -translate-x-1/2 -translate-y-1/2 flex flex-col justify-center items-center w-[100px] bg-white rounded-lg p-2 border border-gray-200 dark:border-gray-700 shadow-sm",
          )}
          style={{
            left: diagramConfig.boxes.chillerPlant.position.left,
            top: diagramConfig.boxes.chillerPlant.position.top,
          }}
        >
          {Array.isArray(diagramConfig.boxes.chillerPlant.label) ? 
            diagramConfig.boxes.chillerPlant.label.map((line, index) => (
              <p key={index} className="text-xs leading-tight font-semibold text-primary-dark">
                {line}
              </p>
            )) : 
            <p className="text-xs leading-tight font-semibold text-primary-dark">
              {diagramConfig.boxes.chillerPlant.label}
            </p>
          }
          <div className="flex py-px px-1.5 items-center gap-1 rounded-md bg-[#EDEFF9] mt-1 justify-center w-full">
            <p className="text-neutral-500 text-xs leading-tight">SP</p>
            <span className="text-[#272E3B] text-sm leading-tight font-semibold">
              {chs_sp === null || chs_sp === undefined ? "-" : chs_sp.toFixed(1)}
            </span>
            <p className="text-[#272E3B] text-xs leading-tight">{getUnit('', 'setpoint_read')}</p>
          </div>
        </div>

        {/* Building Box */}
        <div
          ref={buildingBoxRef}
          className={cn(
            "absolute -translate-x-1/2 -translate-y-1/2 flex flex-col justify-center w-[100px] bg-white rounded-lg p-2 border border-gray-200 dark:border-gray-700 shadow-sm",
          )}
          style={{
            left: diagramConfig.boxes.building.position.left,
            top: diagramConfig.boxes.building.position.top,
          }}
        >
          <p className="text-xs leading-tight font-semibold text-primary-dark text-center">
            {diagramConfig.boxes.building.label}
          </p>
          <div className="flex py-px px-1.5 items-center gap-1 rounded-md bg-[#EDEFF9] mt-1 justify-center w-full">
            <div className="flex items-center">
              <span className="text-[#272E3B] text-sm leading-tight font-semibold mr-0.5">
                {cooling_rate === null || cooling_rate === undefined ? "-" : cooling_rate.toFixed(0)}
              </span>
              <span className="text-[#272E3B] text-xs leading-tight">
                Ton
              </span>
            </div>
          </div>
        </div>

        {/* Water-cooled specific components */}
        {variant === 'water-cooled' && renderWaterCooledComponents()}
      </div>
    </div>
  );
};

export default ChillerPlantDiagram;