import { useState, useRef, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import * as echarts from 'echarts';
import { FiX } from 'react-icons/fi';

interface DataPoint {
  timestamp: string;
  cooling_load: number;
  power: number;
  efficiency: number;
  num_chillers: number;
  chiller_combination: string;
  chs_temp: number;
  cds_temp: number;
  outdoor_temp: number;
}

interface DataAnalyticsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Color palette for primary categories
const COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1',
];

// Symbol shapes for secondary categories
const SYMBOLS = ['circle', 'rect', 'triangle', 'diamond', 'pin', 'arrow'];

// Label field options
type LabelField = 'none' | 'num_chillers' | 'chiller_combination' | 'chs_temp' | 'cds_temp' | 'outdoor_temp';

const LABEL_OPTIONS: { value: LabelField; label: string; isContinuous: boolean }[] = [
  { value: 'none', label: 'None', isContinuous: false },
  { value: 'num_chillers', label: 'Number of Chillers', isContinuous: false },
  { value: 'chiller_combination', label: 'Chiller Combination', isContinuous: false },
  { value: 'chs_temp', label: 'CHS Temp (°F)', isContinuous: true },
  { value: 'cds_temp', label: 'CDS Temp (°F)', isContinuous: true },
  { value: 'outdoor_temp', label: 'Outdoor Temp (°F)', isContinuous: true },
];

// Default bin sizes
const DEFAULT_BIN_SIZES: Record<string, number> = {
  chs_temp: 2,
  cds_temp: 3,
  outdoor_temp: 5,
};

// Function to bin a value into a range string
function binValue(value: number, step: number): string {
  const binStart = Math.floor(value / step) * step;
  const binEnd = binStart + step;
  return `${binStart}-${binEnd}`;
}

// Get category value from data point
function getCategoryValue(d: DataPoint, field: LabelField, binSize?: number): string {
  if (field === 'none') return 'all';
  if (field === 'num_chillers') return String(d.num_chillers);
  if (field === 'chiller_combination') return d.chiller_combination;

  // Continuous fields need binning
  const value = d[field as keyof DataPoint] as number;
  const step = binSize || DEFAULT_BIN_SIZES[field] || 1;
  return binValue(value, step);
}

// Mock data generator
function generateMockData(): DataPoint[] {
  const data: DataPoint[] = [];
  const combinations = {
    1: ['CH-1', 'CH-2', 'CH-3'],
    2: ['CH-1+CH-2', 'CH-1+CH-3', 'CH-2+CH-3'],
    3: ['CH-1+CH-2+CH-3'],
  };

  for (let i = 0; i < 500; i++) {
    const numChillers = Math.random() < 0.3 ? 1 : Math.random() < 0.7 ? 2 : 3;
    const combos = combinations[numChillers as 1 | 2 | 3];
    const combo = combos[Math.floor(Math.random() * combos.length)];
    const baseLoad = numChillers * 60 + Math.random() * 40;
    const coolingLoad = baseLoad + (Math.random() - 0.5) * 30;
    const chsTemp = 44 + Math.random() * 4;
    const outdoorTemp = 75 + Math.random() * 20;
    const cdsTemp = 80 + (outdoorTemp - 75) * 0.4 + Math.random() * 3;

    let baseEfficiency = 0.75;
    if (combo === 'CH-1' || combo === 'CH-1+CH-2') baseEfficiency = 0.72;
    if (combo === 'CH-2' || combo === 'CH-2+CH-3') baseEfficiency = 0.78;
    if (combo === 'CH-3' || combo === 'CH-1+CH-3') baseEfficiency = 0.75;

    const loadFactor = Math.min(coolingLoad / 150, 1);
    const chsFactor = (chsTemp - 44) * 0.01;
    const outdoorFactor = (outdoorTemp - 75) * 0.002;
    const efficiency = baseEfficiency - 0.1 * (1 - loadFactor) + chsFactor + outdoorFactor + (Math.random() - 0.5) * 0.06;
    const power = coolingLoad * efficiency;

    data.push({
      timestamp: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString(),
      cooling_load: Math.round(coolingLoad * 10) / 10,
      power: Math.round(power * 10) / 10,
      efficiency: Math.round(efficiency * 1000) / 1000,
      num_chillers: numChillers,
      chiller_combination: combo,
      chs_temp: Math.round(chsTemp * 10) / 10,
      cds_temp: Math.round(cdsTemp * 10) / 10,
      outdoor_temp: Math.round(outdoorTemp * 10) / 10,
    });
  }
  return data;
}

const DataAnalyticsModal: React.FC<DataAnalyticsModalProps> = ({ isOpen, onClose }) => {
  const { siteId } = useParams<{ siteId: string }>();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  // Date range (stored as YYYY-MM-DD internally)
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() - 3);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);

  // Time resolution
  const [resolution, setResolution] = useState<'1m' | '15m' | '1h'>('1h');

  // Time filter
  const [startTime, setStartTime] = useState('00:00');
  const [endTime, setEndTime] = useState('23:59');
  const [dayType, setDayType] = useState('all');

  // Y-Axis
  const [yAxis, setYAxis] = useState<'efficiency' | 'power'>('efficiency');

  // Labeling
  const [primaryLabel, setPrimaryLabel] = useState<LabelField>('num_chillers');
  const [secondaryLabel, setSecondaryLabel] = useState<LabelField>('none');
  const [primaryBinSize, setPrimaryBinSize] = useState<number>(2);
  const [secondaryBinSize, setSecondaryBinSize] = useState<number>(2);

  // Filters
  const [selectedNumChillers, setSelectedNumChillers] = useState<number[]>([1, 2, 3, 4, 5]);

  // Data
  const [rawData, setRawData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(false);

  // Check if field needs binning
  const isPrimaryContinuous = LABEL_OPTIONS.find(o => o.value === primaryLabel)?.isContinuous || false;
  const isSecondaryContinuous = LABEL_OPTIONS.find(o => o.value === secondaryLabel)?.isContinuous || false;

  // Fetch data
  useEffect(() => {
    if (!isOpen || !siteId) return;
    const fetchData = async () => {
      setLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 300));
        setRawData(generateMockData());
      } catch (err) {
        console.error('Failed to fetch analytics data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [isOpen, siteId, startDate, endDate, startTime, endTime, dayType, resolution]);

  // Filter data
  const filteredData = useMemo(() => {
    return rawData.filter(d => selectedNumChillers.includes(d.num_chillers));
  }, [rawData, selectedNumChillers]);

  // Get unique categories
  const primaryCategories = useMemo(() => {
    if (primaryLabel === 'none') return ['all'];
    const cats = new Set<string>();
    filteredData.forEach(d => cats.add(getCategoryValue(d, primaryLabel, isPrimaryContinuous ? primaryBinSize : undefined)));
    return Array.from(cats).sort((a, b) => {
      const numA = parseFloat(a);
      const numB = parseFloat(b);
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
      return a.localeCompare(b);
    });
  }, [filteredData, primaryLabel, primaryBinSize, isPrimaryContinuous]);

  const secondaryCategories = useMemo(() => {
    if (secondaryLabel === 'none') return ['all'];
    const cats = new Set<string>();
    filteredData.forEach(d => cats.add(getCategoryValue(d, secondaryLabel, isSecondaryContinuous ? secondaryBinSize : undefined)));
    return Array.from(cats).sort((a, b) => {
      const numA = parseFloat(a);
      const numB = parseFloat(b);
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
      return a.localeCompare(b);
    });
  }, [filteredData, secondaryLabel, secondaryBinSize, isSecondaryContinuous]);

  // Update chart
  useEffect(() => {
    if (!isOpen || !chartRef.current) return;
    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current);
    }
    const chartInstance = chartInstanceRef.current;
    const series: any[] = [];

    const getSeriesName = (primary: string, secondary: string) => {
      if (primaryLabel === 'none' && secondaryLabel === 'none') return 'All Data';
      if (secondaryLabel === 'none') return primary;
      if (primaryLabel === 'none') return secondary;
      return `${primary} | ${secondary}`;
    };

    primaryCategories.forEach((primaryCat, pIdx) => {
      secondaryCategories.forEach((secondaryCat, sIdx) => {
        const data = filteredData
          .filter(d => {
            const pMatch = primaryLabel === 'none' || getCategoryValue(d, primaryLabel, isPrimaryContinuous ? primaryBinSize : undefined) === primaryCat;
            const sMatch = secondaryLabel === 'none' || getCategoryValue(d, secondaryLabel, isSecondaryContinuous ? secondaryBinSize : undefined) === secondaryCat;
            return pMatch && sMatch;
          })
          .map(d => [d.cooling_load, yAxis === 'efficiency' ? d.efficiency : d.power]);

        if (data.length === 0) return;

        series.push({
          name: getSeriesName(primaryCat, secondaryCat),
          type: 'scatter',
          data,
          symbol: secondaryLabel !== 'none' ? SYMBOLS[sIdx % SYMBOLS.length] : 'circle',
          symbolSize: secondaryLabel !== 'none' ? 10 : 8,
          itemStyle: {
            color: primaryLabel !== 'none' ? COLORS[pIdx % COLORS.length] : COLORS[sIdx % COLORS.length],
            opacity: 0.7,
            borderColor: secondaryLabel !== 'none' ? '#fff' : undefined,
            borderWidth: secondaryLabel !== 'none' ? 1 : 0,
          },
        });
      });
    });

    chartInstance.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const [load, value] = params.data;
          const unit = yAxis === 'efficiency' ? 'kW/RT' : 'kW';
          return `${params.seriesName}<br/>
            Cooling Load: <b>${load.toFixed(1)} RT</b><br/>
            ${yAxis === 'efficiency' ? 'Efficiency' : 'Power'}: <b>${value.toFixed(yAxis === 'efficiency' ? 3 : 1)} ${unit}</b>`;
        },
      },
      legend: {
        data: series.map(s => s.name),
        top: 10,
        right: 10,
        orient: 'vertical',
        type: 'scroll',
        textStyle: { fontSize: 11 },
      },
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: 'none',
            title: { zoom: 'Zoom', back: 'Reset' },
          },
          restore: { title: 'Reset' },
        },
        right: Math.max(150, series.length > 6 ? 180 : 150) + 10,
        top: 10,
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          filterMode: 'none',
        },
        {
          type: 'inside',
          yAxisIndex: 0,
          filterMode: 'none',
        },
        {
          type: 'slider',
          xAxisIndex: 0,
          bottom: 10,
          height: 20,
          filterMode: 'none',
        },
      ],
      grid: {
        left: 60,
        right: Math.max(150, series.length > 6 ? 180 : 150),
        top: 40,
        bottom: 60,
      },
      xAxis: {
        type: 'value',
        name: 'Cooling Load (RT)',
        nameLocation: 'middle',
        nameGap: 30,
        splitLine: { lineStyle: { color: '#eee' } },
      },
      yAxis: {
        type: 'value',
        name: yAxis === 'efficiency' ? 'Efficiency (kW/RT)' : 'Power (kW)',
        nameLocation: 'middle',
        nameGap: 40,
        splitLine: { lineStyle: { color: '#eee' } },
      },
      series,
    }, true);

    const handleResize = () => chartInstance.resize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen, filteredData, primaryCategories, secondaryCategories, primaryLabel, secondaryLabel, primaryBinSize, secondaryBinSize, yAxis, isPrimaryContinuous, isSecondaryContinuous]);

  // Cleanup
  useEffect(() => {
    if (!isOpen && chartInstanceRef.current) {
      chartInstanceRef.current.dispose();
      chartInstanceRef.current = null;
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const toggleNumChillers = (num: number) => {
    setSelectedNumChillers(prev =>
      prev.includes(num) ? prev.filter(n => n !== num) : [...prev, num].sort()
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-[95vw] max-w-[1600px] h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-[#065BA9]">Data Analytics - Plant Performance</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Filters Sidebar */}
          <div className="w-72 border-r p-4 space-y-4 overflow-y-auto">
            {/* Y-Axis */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Y-Axis</label>
              <select value={yAxis} onChange={e => setYAxis(e.target.value as any)} className="w-full px-3 py-2 border rounded-md text-sm">
                <option value="efficiency">Efficiency (kW/RT)</option>
                <option value="power">Power (kW)</option>
              </select>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
              <div className="flex gap-1 items-center">
                <input
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="flex-1 px-1.5 py-1 border rounded text-xs"
                />
                <span className="text-gray-400 text-xs">-</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  className="flex-1 px-1.5 py-1 border rounded text-xs"
                />
              </div>
            </div>

            {/* Time Resolution */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Resolution</label>
              <div className="flex gap-1">
                {[
                  { value: '1m', label: '1 min' },
                  { value: '15m', label: '15 min' },
                  { value: '1h', label: '1 hour' },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setResolution(opt.value as any)}
                    className={`flex-1 px-2 py-1.5 text-xs rounded border transition-colors ${
                      resolution === opt.value
                        ? 'bg-blue-500 text-white border-blue-500'
                        : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Time of Day */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Time of Day</label>
              <div className="flex gap-2 items-center">
                <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} className="flex-1 px-2 py-1.5 border rounded-md text-sm" />
                <span className="text-gray-400">-</span>
                <input type="time" value={endTime} onChange={e => setEndTime(e.target.value)} className="flex-1 px-2 py-1.5 border rounded-md text-sm" />
              </div>
            </div>

            {/* Day Type */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Day Type</label>
              <select value={dayType} onChange={e => setDayType(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm">
                <option value="all">All Days</option>
                <option value="weekdays">Weekdays Only</option>
                <option value="weekends">Weekends Only</option>
              </select>
            </div>

            <hr />

            {/* Primary Label (Color) */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Primary Label (Color)</label>
              <select value={primaryLabel} onChange={e => setPrimaryLabel(e.target.value as LabelField)} className="w-full px-3 py-2 border rounded-md text-sm">
                {LABEL_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {isPrimaryContinuous && (
                <div className="mt-2 flex items-center gap-2">
                  <label className="text-xs text-gray-500">Bin size:</label>
                  <input
                    type="number"
                    value={primaryBinSize}
                    onChange={e => setPrimaryBinSize(Math.max(0.5, parseFloat(e.target.value) || 1))}
                    className="w-16 px-2 py-1 border rounded text-sm"
                    step="0.5"
                    min="0.5"
                  />
                </div>
              )}
            </div>

            {/* Secondary Label (Shape) */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Secondary Label (Shape)</label>
              <select value={secondaryLabel} onChange={e => setSecondaryLabel(e.target.value as LabelField)} className="w-full px-3 py-2 border rounded-md text-sm">
                {LABEL_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {isSecondaryContinuous && (
                <div className="mt-2 flex items-center gap-2">
                  <label className="text-xs text-gray-500">Bin size:</label>
                  <input
                    type="number"
                    value={secondaryBinSize}
                    onChange={e => setSecondaryBinSize(Math.max(0.5, parseFloat(e.target.value) || 1))}
                    className="w-16 px-2 py-1 border rounded text-sm"
                    step="0.5"
                    min="0.5"
                  />
                </div>
              )}
            </div>

            <hr />

            {/* Filter by # Chillers */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">Filter by # Chillers</label>
              <div className="flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5].map(num => (
                  <button
                    key={num}
                    onClick={() => toggleNumChillers(num)}
                    className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                      selectedNumChillers.includes(num)
                        ? 'bg-blue-500 text-white border-blue-500'
                        : 'bg-white text-gray-600 border-gray-300 hover:border-blue-300'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="pt-4 border-t">
              <div className="text-xs text-gray-500 space-y-1">
                <div>Total points: <span className="font-medium text-gray-700">{filteredData.length}</span></div>
                {primaryLabel !== 'none' && (
                  <div>Primary groups: <span className="font-medium text-gray-700">{primaryCategories.length}</span></div>
                )}
                {secondaryLabel !== 'none' && (
                  <div>Secondary groups: <span className="font-medium text-gray-700">{secondaryCategories.length}</span></div>
                )}
              </div>
            </div>

            {/* Shape Legend */}
            {secondaryLabel !== 'none' && (
              <div className="pt-4 border-t">
                <div className="text-xs font-medium text-gray-600 mb-2">Shape Legend</div>
                <div className="space-y-1">
                  {secondaryCategories.slice(0, 6).map((cat, idx) => (
                    <div key={cat} className="flex items-center gap-2 text-xs text-gray-600">
                      <span className="w-4 text-center">{['●', '■', '▲', '◆', '📍', '→'][idx]}</span>
                      <span>{cat}</span>
                    </div>
                  ))}
                  {secondaryCategories.length > 6 && (
                    <div className="text-xs text-gray-400">+{secondaryCategories.length - 6} more...</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Chart Area */}
          <div className="flex-1 p-4">
            {loading ? (
              <div className="w-full h-full flex items-center justify-center">
                <div className="text-gray-500">Loading data...</div>
              </div>
            ) : (
              <div ref={chartRef} className="w-full h-full" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataAnalyticsModal;
