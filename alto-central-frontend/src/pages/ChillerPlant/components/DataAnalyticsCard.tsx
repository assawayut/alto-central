import { useState, useRef, useEffect } from 'react';
import * as echarts from 'echarts';
import { FiArrowRight } from 'react-icons/fi';
import DataAnalyticsModal from './DataAnalyticsModal';

const DataAnalyticsCard: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const chartInstance = echarts.init(chartRef.current);
    chartInstanceRef.current = chartInstance;

    // Mini scatter plot preview - mock data showing efficiency vs load
    const mockData: number[][] = [];
    const colors: string[] = [];

    // Generate more realistic scatter data
    // 1 chiller (blue)
    for (let i = 0; i < 12; i++) {
      mockData.push([40 + Math.random() * 30, 0.78 + Math.random() * 0.08]);
      colors.push('#3b82f6');
    }
    // 2 chillers (green)
    for (let i = 0; i < 15; i++) {
      mockData.push([80 + Math.random() * 40, 0.70 + Math.random() * 0.08]);
      colors.push('#22c55e');
    }
    // 3 chillers (orange)
    for (let i = 0; i < 10; i++) {
      mockData.push([140 + Math.random() * 50, 0.65 + Math.random() * 0.08]);
      colors.push('#f59e0b');
    }

    chartInstance.setOption({
      grid: {
        left: 25,
        right: 10,
        top: 10,
        bottom: 20,
        containLabel: false,
      },
      xAxis: {
        type: 'value',
        min: 30,
        max: 200,
        axisLabel: { fontSize: 8, color: '#999' },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0.6,
        max: 0.9,
        axisLabel: { fontSize: 8, color: '#999', formatter: (v: number) => v.toFixed(2) },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
        { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
      ],
      series: [{
        type: 'scatter',
        data: mockData,
        symbolSize: 6,
        itemStyle: {
          color: (params: any) => colors[params.dataIndex] || '#3b82f6',
          opacity: 0.7,
        },
      }],
    });

    const handleResize = () => chartInstance.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.dispose();
    };
  }, []);

  return (
    <>
      <div
        className="alto-card p-3 cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => setIsModalOpen(true)}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="text-[#065BA9] text-sm font-semibold">Data Analytics</div>
          <FiArrowRight className="w-4 h-4 text-[#065BA9]" />
        </div>

        {/* Mini chart preview */}
        <div ref={chartRef} className="w-full h-[120px]" />

        <div className="text-[10px] text-[#788796] mt-2 text-center">
          Plant Efficiency vs Cooling Load
        </div>
        <div className="text-[9px] text-[#0E7EE4] mt-1 text-center">
          Click to explore data
        </div>
      </div>

      <DataAnalyticsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

export default DataAnalyticsCard;
