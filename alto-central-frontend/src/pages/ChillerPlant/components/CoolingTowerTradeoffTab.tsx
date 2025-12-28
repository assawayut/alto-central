import { useState, useRef, useEffect, useMemo } from 'react';
import * as echarts from 'echarts';
import { API_ENDPOINTS } from '@/config/api';

interface CTDataPoint {
  timestamp: string;
  cds: number;
  power_chillers: number;
  power_cts: number;
  outdoor_wbt: number;
  cooling_load: number;
}

interface CoolingTowerTradeoffTabProps {
  siteId: string;
}

// Bin value into range
function binValue(value: number, step: number): number {
  return Math.floor(value / step) * step;
}

const CoolingTowerTradeoffTab: React.FC<CoolingTowerTradeoffTabProps> = ({
  siteId,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  // Date range state (stored as YYYY-MM-DD internally)
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() - 3);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);

  // Refs for date input navigation
  const startMonthRef = useRef<HTMLInputElement>(null);
  const startYearRef = useRef<HTMLInputElement>(null);
  const endDayRef = useRef<HTMLInputElement>(null);
  const endMonthRef = useRef<HTMLInputElement>(null);
  const endYearRef = useRef<HTMLInputElement>(null);

  // Split date parts for separate inputs
  const [startDay, setStartDay] = useState(() => startDate.split('-')[2]);
  const [startMonth, setStartMonth] = useState(() => startDate.split('-')[1]);
  const [startYear, setStartYear] = useState(() => startDate.split('-')[0]);
  const [endDay, setEndDay] = useState(() => endDate.split('-')[2]);
  const [endMonth, setEndMonth] = useState(() => endDate.split('-')[1]);
  const [endYear, setEndYear] = useState(() => endDate.split('-')[0]);

  // Sync to main date state
  useEffect(() => {
    if (startDay.length === 2 && startMonth.length === 2 && startYear.length === 4) {
      const d = `${startYear}-${startMonth}-${startDay}`;
      if (!isNaN(Date.parse(d))) setStartDate(d);
    }
  }, [startDay, startMonth, startYear]);

  useEffect(() => {
    if (endDay.length === 2 && endMonth.length === 2 && endYear.length === 4) {
      const d = `${endYear}-${endMonth}-${endDay}`;
      if (!isNaN(Date.parse(d))) setEndDate(d);
    }
  }, [endDay, endMonth, endYear]);

  const handleDatePartChange = (
    value: string,
    maxLen: number,
    setter: (v: string) => void,
    nextRef?: React.RefObject<HTMLInputElement>
  ) => {
    const cleaned = value.replace(/\D/g, '').slice(0, maxLen);
    setter(cleaned);
    if (cleaned.length === maxLen && nextRef?.current) {
      nextRef.current.focus();
      nextRef.current.select();
    }
  };

  const handleDatePartFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.select();
  };

  const [resolution, setResolution] = useState<'1m' | '15m' | '1h'>('1h');
  const [startTime, setStartTime] = useState('00:00');
  const [endTime, setEndTime] = useState('23:59');
  const [dayType, setDayType] = useState('all');

  // Data
  const [rawData, setRawData] = useState<CTDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataCount, setDataCount] = useState<number | null>(null);

  // Filters
  const [wbtMin, setWbtMin] = useState<number>(70);
  const [wbtMax, setWbtMax] = useState<number>(85);
  const [loadMin, setLoadMin] = useState<number>(500);
  const [loadMax, setLoadMax] = useState<number>(3000);
  const [cdsBinSize, setCdsBinSize] = useState<number>(1);

  // Fetch data
  const fetchData = async () => {
    if (!siteId) return;
    setLoading(true);
    try {
      const url = API_ENDPOINTS.coolingTowerTradeoff(siteId, {
        start_date: startDate,
        end_date: endDate,
        resolution,
        start_time: startTime,
        end_time: endTime,
        day_type: dayType,
      });
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch data');
      const result = await response.json();
      setRawData(result.data || []);
      setDataCount(result.count || result.data?.length || 0);
    } catch (err) {
      console.error('Failed to fetch CT tradeoff data:', err);
      setRawData([]);
      setDataCount(null);
    } finally {
      setLoading(false);
    }
  };

  // Filter data by WBT and Load ranges
  const filteredData = useMemo(() => {
    return rawData.filter(d =>
      d.outdoor_wbt >= wbtMin &&
      d.outdoor_wbt <= wbtMax &&
      d.cooling_load >= loadMin &&
      d.cooling_load <= loadMax
    );
  }, [rawData, wbtMin, wbtMax, loadMin, loadMax]);

  // Group by CDS bins and calculate averages
  const chartData = useMemo(() => {
    const bins: Record<number, { chillerPower: number[]; ctPower: number[] }> = {};

    filteredData.forEach(d => {
      const cdsBin = binValue(d.cds, cdsBinSize);
      if (!bins[cdsBin]) {
        bins[cdsBin] = { chillerPower: [], ctPower: [] };
      }
      bins[cdsBin].chillerPower.push(d.power_chillers);
      bins[cdsBin].ctPower.push(d.power_cts);
    });

    const sortedBins = Object.keys(bins)
      .map(Number)
      .sort((a, b) => a - b);

    return sortedBins.map(cds => {
      const bin = bins[cds];
      const avgChiller = bin.chillerPower.reduce((a, b) => a + b, 0) / bin.chillerPower.length;
      const avgCT = bin.ctPower.reduce((a, b) => a + b, 0) / bin.ctPower.length;
      return {
        cds,
        chillerPower: avgChiller,
        ctPower: avgCT,
        totalPower: avgChiller + avgCT,
        count: bin.chillerPower.length,
      };
    });
  }, [filteredData, cdsBinSize]);

  // Find optimal CDS (minimum total power)
  const optimalPoint = useMemo(() => {
    if (chartData.length === 0) return null;
    return chartData.reduce((min, curr) =>
      curr.totalPower < min.totalPower ? curr : min
    );
  }, [chartData]);

  // Update chart
  useEffect(() => {
    if (!chartRef.current) return;
    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current);
    }
    const chartInstance = chartInstanceRef.current;

    // Prepare scatter data (raw points)
    const scatterChiller = filteredData.map(d => [d.cds, d.power_chillers]);
    const scatterCT = filteredData.map(d => [d.cds, d.power_cts]);
    const scatterTotal = filteredData.map(d => [d.cds, d.power_chillers + d.power_cts]);

    chartInstance.setOption({
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.seriesType === 'scatter') {
            return `<b>CDS: ${params.data[0].toFixed(1)}°F</b><br/>
              ${params.seriesName}: <b>${params.data[1].toFixed(0)} kW</b>`;
          }
          // Line series
          const dataPoint = chartData.find(d => d.cds === params.data[0]);
          if (!dataPoint) return '';
          return `<b>CDS: ${params.data[0]}°F (avg)</b><br/>
            Chiller Power: <b>${dataPoint.chillerPower.toFixed(0)} kW</b><br/>
            CT Power: <b>${dataPoint.ctPower.toFixed(0)} kW</b><br/>
            Total Power: <b>${dataPoint.totalPower.toFixed(0)} kW</b><br/>
            <span style="color:#888">Data points: ${dataPoint.count}</span>`;
        },
      },
      legend: {
        data: [
          'Chiller Power (avg)', 'CT Power (avg)', 'Total Power (avg)',
          'Chiller Power (raw)', 'CT Power (raw)', 'Total Power (raw)'
        ],
        selected: {
          'Chiller Power (avg)': true,
          'CT Power (avg)': true,
          'Total Power (avg)': true,
          'Chiller Power (raw)': false,
          'CT Power (raw)': false,
          'Total Power (raw)': false,
        },
        top: 10,
        right: 10,
        textStyle: { fontSize: 11 },
      },
      toolbox: {
        feature: {
          dataZoom: {
            xAxisIndex: 0,
            yAxisIndex: 0,
            title: { zoom: 'Box Zoom', back: 'Reset Zoom' },
          },
          restore: { title: 'Reset All' },
        },
        right: 10,
        top: 40,
      },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
        { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
      ],
      grid: {
        left: 60,
        right: 20,
        top: 70,
        bottom: 50,
      },
      xAxis: {
        type: 'value',
        name: 'CDS (°F)',
        nameLocation: 'middle',
        nameGap: 30,
        scale: true,
        splitLine: { lineStyle: { color: '#eee' } },
      },
      yAxis: {
        type: 'value',
        name: 'Power (kW)',
        nameLocation: 'middle',
        nameGap: 45,
        scale: true,
        splitLine: { lineStyle: { color: '#eee' } },
      },
      series: [
        // Scatter series (raw data) - hidden by default
        {
          name: 'Chiller Power (raw)',
          type: 'scatter',
          data: scatterChiller,
          symbolSize: 4,
          itemStyle: { color: '#3b82f6', opacity: 0.3 },
        },
        {
          name: 'CT Power (raw)',
          type: 'scatter',
          data: scatterCT,
          symbolSize: 4,
          itemStyle: { color: '#f97316', opacity: 0.3 },
        },
        {
          name: 'Total Power (raw)',
          type: 'scatter',
          data: scatterTotal,
          symbolSize: 4,
          itemStyle: { color: '#22c55e', opacity: 0.3 },
        },
        // Line series (averaged data)
        {
          name: 'Chiller Power (avg)',
          type: 'line',
          data: chartData.map(d => [d.cds, d.chillerPower]),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: { color: '#3b82f6' },
          lineStyle: { width: 2 },
        },
        {
          name: 'CT Power (avg)',
          type: 'line',
          data: chartData.map(d => [d.cds, d.ctPower]),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: { color: '#f97316' },
          lineStyle: { width: 2 },
        },
        {
          name: 'Total Power (avg)',
          type: 'line',
          data: chartData.map(d => [d.cds, d.totalPower]),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: { color: '#22c55e' },
          lineStyle: { width: 3 },
        },
      ],
    }, true);

    const handleResize = () => chartInstance.resize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [chartData, optimalPoint]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose();
        chartInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <>
      {/* Filters Sidebar */}
      <div className="w-72 border-r p-4 space-y-4 overflow-y-auto">
        {/* Date Range */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Date Range</label>
          <div className="flex items-center bg-gray-100 rounded px-2 py-1.5 text-sm">
            {/* Start Date */}
            <input
              type="text"
              value={startDay}
              onChange={e => handleDatePartChange(e.target.value, 2, setStartDay, startMonthRef)}
              onFocus={handleDatePartFocus}
              placeholder="dd"
              className="bg-transparent outline-none w-6 text-center"
            />
            <span className="text-gray-400">/</span>
            <input
              ref={startMonthRef}
              type="text"
              value={startMonth}
              onChange={e => handleDatePartChange(e.target.value, 2, setStartMonth, startYearRef)}
              onFocus={handleDatePartFocus}
              placeholder="mm"
              className="bg-transparent outline-none w-6 text-center"
            />
            <span className="text-gray-400">/</span>
            <input
              ref={startYearRef}
              type="text"
              value={startYear}
              onChange={e => handleDatePartChange(e.target.value, 4, setStartYear, endDayRef)}
              onFocus={handleDatePartFocus}
              placeholder="yyyy"
              className="bg-transparent outline-none w-10 text-center"
            />

            <span className="text-gray-400 mx-2">-</span>

            {/* End Date */}
            <input
              ref={endDayRef}
              type="text"
              value={endDay}
              onChange={e => handleDatePartChange(e.target.value, 2, setEndDay, endMonthRef)}
              onFocus={handleDatePartFocus}
              placeholder="dd"
              className="bg-transparent outline-none w-6 text-center"
            />
            <span className="text-gray-400">/</span>
            <input
              ref={endMonthRef}
              type="text"
              value={endMonth}
              onChange={e => handleDatePartChange(e.target.value, 2, setEndMonth, endYearRef)}
              onFocus={handleDatePartFocus}
              placeholder="mm"
              className="bg-transparent outline-none w-6 text-center"
            />
            <span className="text-gray-400">/</span>
            <input
              ref={endYearRef}
              type="text"
              value={endYear}
              onChange={e => handleDatePartChange(e.target.value, 4, setEndYear)}
              onFocus={handleDatePartFocus}
              placeholder="yyyy"
              className="bg-transparent outline-none w-10 text-center"
            />
          </div>
        </div>

        {/* Resolution */}
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
                className={`flex-1 px-2 py-1.5 text-xs rounded transition-colors ${
                  resolution === opt.value
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
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
          <div className="flex items-center bg-gray-100 rounded px-2 py-1.5">
            <input
              type="time"
              value={startTime}
              onChange={e => setStartTime(e.target.value)}
              className="bg-transparent text-sm outline-none flex-1 min-w-0"
            />
            <span className="text-gray-400 mx-2">-</span>
            <input
              type="time"
              value={endTime}
              onChange={e => setEndTime(e.target.value)}
              className="bg-transparent text-sm outline-none flex-1 min-w-0"
            />
          </div>
        </div>

        {/* Day Type */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Day Type</label>
          <select
            value={dayType}
            onChange={e => setDayType(e.target.value)}
            className="w-full px-3 py-1.5 bg-gray-100 rounded text-sm outline-none focus:bg-white focus:ring-1 focus:ring-blue-400"
          >
            <option value="all">All Days</option>
            <option value="weekdays">Weekdays Only</option>
            <option value="weekends">Weekends Only</option>
          </select>
        </div>

        <hr />

        {/* WBT Range */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Outdoor WBT Range (°F)</label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={wbtMin}
              onChange={e => setWbtMin(Number(e.target.value))}
              className="w-20 px-2 py-1.5 bg-gray-100 rounded text-sm outline-none focus:bg-white focus:ring-1 focus:ring-blue-400"
            />
            <span className="text-gray-400">-</span>
            <input
              type="number"
              value={wbtMax}
              onChange={e => setWbtMax(Number(e.target.value))}
              className="w-20 px-2 py-1.5 bg-gray-100 rounded text-sm outline-none focus:bg-white focus:ring-1 focus:ring-blue-400"
            />
          </div>
        </div>

        {/* Load Range */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Cooling Load Range (RT)</label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={loadMin}
              onChange={e => setLoadMin(Number(e.target.value))}
              className="w-20 px-2 py-1.5 bg-gray-100 rounded text-sm outline-none focus:bg-white focus:ring-1 focus:ring-blue-400"
            />
            <span className="text-gray-400">-</span>
            <input
              type="number"
              value={loadMax}
              onChange={e => setLoadMax(Number(e.target.value))}
              className="w-20 px-2 py-1.5 bg-gray-100 rounded text-sm outline-none focus:bg-white focus:ring-1 focus:ring-blue-400"
            />
          </div>
        </div>

        {/* CDS Bin Size */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">CDS Bin Size (°F)</label>
          <input
            type="number"
            value={cdsBinSize}
            onChange={e => setCdsBinSize(Math.max(0.5, Number(e.target.value)))}
            className="w-full px-3 py-1.5 bg-gray-100 rounded text-sm outline-none focus:bg-white focus:ring-1 focus:ring-blue-400"
            step="0.5"
            min="0.5"
          />
        </div>

        {/* Plot Button */}
        <button
          onClick={fetchData}
          disabled={loading}
          className="w-full py-2 bg-[#0E7EE4] text-white text-sm font-medium rounded-md hover:bg-[#0a6bc4] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Loading...' : 'Plot Graph'}
        </button>

        <hr />

        {/* Stats */}
        <div className="pt-2">
          <div className="text-xs text-gray-500 space-y-1">
            {dataCount !== null && (
              <div>From API: <span className="font-medium text-gray-700">{dataCount.toLocaleString()}</span></div>
            )}
            <div>After filter: <span className="font-medium text-gray-700">{filteredData.length.toLocaleString()}</span></div>
            <div>CDS bins: <span className="font-medium text-gray-700">{chartData.length}</span></div>
          </div>
        </div>

        {/* Optimal Point */}
        {optimalPoint && (
          <div className="pt-4 border-t">
            <div className="text-xs font-medium text-gray-600 mb-2">Optimal Point</div>
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <div className="text-lg font-bold text-green-700">{optimalPoint.cds}°F</div>
              <div className="text-xs text-green-600 mt-1">
                Total: {optimalPoint.totalPower.toFixed(0)} kW
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Chiller: {optimalPoint.chillerPower.toFixed(0)} kW<br />
                CT: {optimalPoint.ctPower.toFixed(0)} kW
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="pt-4 border-t">
          <div className="text-xs font-medium text-gray-600 mb-2">Legend</div>
          <div className="space-y-1 text-xs">
            <div className="text-[10px] text-gray-400 mb-1">Lines (averaged)</div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#3b82f6]"></span>
              <span>Chiller Power</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#f97316]"></span>
              <span>CT Power</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-0.5 bg-[#22c55e]"></span>
              <span>Total Power</span>
            </div>
            <div className="text-[10px] text-gray-400 mt-2 mb-1">Points (raw, click legend to show)</div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#3b82f6] opacity-50"></span>
              <span className="text-gray-400">Chiller Power</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#f97316] opacity-50"></span>
              <span className="text-gray-400">CT Power</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#22c55e] opacity-50"></span>
              <span className="text-gray-400">Total Power</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 p-4">
        {loading ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-gray-500">Loading data...</div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center text-gray-400">
              <div className="text-lg mb-2">No data</div>
              <div className="text-sm">Click "Plot Graph" to load data</div>
            </div>
          </div>
        ) : (
          <div ref={chartRef} className="w-full h-full" />
        )}
      </div>
    </>
  );
};

export default CoolingTowerTradeoffTab;
