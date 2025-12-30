import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Loader } from "@/components/ui/loader";
import * as echarts from "echarts";
import { API_ENDPOINTS } from "@/config/api";
import { getSiteById } from "@/config/sites";
import { DateTime } from 'luxon';

interface TimeseriesDataPoint {
  timestamp: string;
  value: number;
}

interface TimeseriesResponse {
  site_id: string;
  device_id: string;
  datapoint: string;
  period: string;
  aggregation: string;
  data: TimeseriesDataPoint[];
}

const BuildingLoadGraph: React.FC = () => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { siteId } = useParams<{ siteId: string }>();
  const site = getSiteById(siteId || '');

  // Initialize chart with default configuration
  const initializeChart = () => {
    if (!chartRef.current) return;

    // Make sure any existing chart is disposed first
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispose();
    }

    // Check if the container has proper dimensions
    if (chartRef.current.clientWidth === 0 || chartRef.current.clientHeight === 0) {
      console.log("Chart container has no dimensions yet, will retry");
      setTimeout(initializeChart, 50);
      return;
    }

    const chartInstance = echarts.init(chartRef.current);
    chartInstanceRef.current = chartInstance;

    // Use midnight-to-midnight in site timezone
    const timezone = site?.timezone || 'Asia/Bangkok';
    const now = DateTime.now().setZone(timezone);
    const startDatetime = now.startOf('day');
    const endDateTime = startDatetime.plus({ days: 1 });

    // Create empty data arrays for initial display
    const emptyData = Array.from({ length: 24 }, (_, i) => [
      startDatetime.plus({ hours: i }).toJSDate().getTime(),
      0
    ]);

    chartInstance.setOption({
      tooltip: {
        trigger: "axis",
        formatter: function (params: any[]) {
          const timezone = site?.timezone || 'Asia/Bangkok';
          const dt = DateTime.fromMillis(params[0].data[0]).setZone(timezone);
          const dateString = dt.toFormat('dd MMM yyyy, HH:mm');

          const tooltipItems = params
            .map((param: any) => {
              const name = param.seriesName.replace(" (Predicted)", "");
              const unit = param.seriesName.includes("Cooling") ? " RT" : " kW";
              return `<span style="color: ${param.color}; font-size: 16px;">●</span> ${name}: <b>${param.value[1].toFixed(1)}${unit}</b>`;
            })
            .join("<br/>");
          return `${dateString}<br/>${tooltipItems}`;
        },
        backgroundColor: '#fff',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333' }
      },
      legend: {
        data: [
          { name: "Cooling Load (RT)", icon: 'circle' },
          { name: "Power (kW)", icon: 'circle' }
        ],
        top: 0,
        right: 10,
        orient: "horizontal",
        textStyle: {
          fontSize: 12,
        },
        itemGap: 24,
      },
      xAxis: {
        type: "time",
        min: startDatetime.toMillis(),
        max: endDateTime.toMillis(),
        interval: 3600 * 1000 * 6, // 6 hours interval
        axisLabel: {
          formatter: function (params: number) {
            const dt = DateTime.fromMillis(params).setZone(timezone);
            const hour = dt.hour;
            // Show 24 at end of day instead of 0
            if (hour === 0 && params >= endDateTime.toMillis() - 1000) {
              return '24';
            }
            return hour.toString();
          },
          margin: 12,
          fontSize: 12,
          color: "#788796",
        },
        axisTick: { show: false },
        axisLine: {
          lineStyle: { color: '#ddd' }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#eee',
            type: 'solid'
          }
        }
      },
      yAxis: {
        type: "value",
        name: "",
        min: 0,
        max: 1000,
        interval: 200,
        axisLabel: {
          fontSize: 12,
          formatter: (value: number) => value.toFixed(0),
        },
        nameTextStyle: {
          fontSize: 12,
          padding: [0, 0, 0, 0],
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#eee',
            type: 'solid'
          }
        }
      },
      series: [
        {
          name: "Cooling Load",
          type: "line",
          showSymbol: false,
          symbolSize: 0,
          data: emptyData,
          color: "#14B8B4",
          lineStyle: {
            width: 2,
            type: "solid"
          },
          smooth: true,
          z: 2,
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: "rgba(20, 184, 180, 0.3)",
                },
                {
                  offset: 1,
                  color: "rgba(20, 184, 180, 0.1)",
                },
              ],
            },
          },
        },
        {
          name: "Power",
          type: "line",
          showSymbol: false,
          symbolSize: 0,
          data: emptyData,
          color: "#3b82f6",
          lineStyle: {
            width: 2,
            type: "solid"
          },
          smooth: true,
          z: 2,
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: "rgba(59, 130, 246, 0.3)",
                },
                {
                  offset: 1,
                  color: "rgba(59, 130, 246, 0.1)",
                },
              ],
            },
          },
        }
      ],
      grid: {
        left: "3%",
        right: "4%",
        bottom: "5%",
        top: "18%",
        containLabel: true,
      },
      toolbox: {
        show: false,
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
      ],
    });
  };

  const updateChartWithData = (powerData: TimeseriesDataPoint[], coolingLoadData: TimeseriesDataPoint[]) => {
    if (!chartInstanceRef.current) return;

    const chartInstance = chartInstanceRef.current;

    const transformData = (data: TimeseriesDataPoint[]) => {
      return data.map(item => [
        new Date(item.timestamp).getTime(),
        item.value
      ]);
    };

    const powerChartData = transformData(powerData);
    const coolingLoadChartData = transformData(coolingLoadData);

    // Calculate max values for y-axis scaling
    const maxPowerValue = Math.max(...powerChartData.map(data => data[1]), 1);
    const maxLoadValue = Math.max(...coolingLoadChartData.map(data => data[1]), 1);

    // Find the overall maximum value
    const maxValue = Math.max(maxPowerValue, maxLoadValue);

    // Calculate appropriate y-axis max and interval
    const yAxisMax = Math.ceil((maxValue * 1.2) / 100) * 100;

    // Calculate appropriate interval
    let yAxisInterval;

    if (yAxisMax <= 500) {
      yAxisInterval = 100;
    } else if (yAxisMax <= 1000) {
      yAxisInterval = 200;
    } else {
      yAxisInterval = 400;
    }

    chartInstance.setOption({
      yAxis: {
        max: yAxisMax,
        interval: yAxisInterval
      },
      series: [
        {
          name: "Cooling Load (RT)",
          data: coolingLoadChartData,
          showSymbol: false,
          symbolSize: 4,
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: "rgba(20, 184, 180, 0.3)",
                },
                {
                  offset: 1,
                  color: "rgba(20, 184, 180, 0.1)",
                },
              ],
            },
          },
        },
        {
          name: "Power (kW)",
          data: powerChartData,
          showSymbol: false,
          symbolSize: 4,
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: "rgba(59, 130, 246, 0.3)",
                },
                {
                  offset: 1,
                  color: "rgba(59, 130, 246, 0.1)",
                },
              ],
            },
          },
        }
      ]
    });
  };

  useEffect(() => {
    if (!siteId) return;

    console.log('BuildingLoadGraph component mounted');

    const handleResize = () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.resize();
      }
    };

    const fetchTimeseries = async (datapoint: string): Promise<TimeseriesResponse> => {
      const url = API_ENDPOINTS.timeseriesAggregated(siteId, {
        device_id: 'plant',
        datapoint,
        period: 'today',
        aggregation: 'hourly'
      });
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${datapoint} data`);
      }
      return response.json();
    };

    const initializeAndFetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Initialize chart first
        initializeChart();

        // Fetch power and cooling load data in parallel
        const [powerResponse, coolingResponse] = await Promise.all([
          fetchTimeseries('power'),
          fetchTimeseries('cooling_rate')
        ]);

        const powerData = powerResponse.data || [];
        const coolingLoadData = coolingResponse.data || [];

        // Try updating chart with a small delay to ensure container is ready
        setTimeout(() => {
          if (!chartInstanceRef.current) {
            initializeChart();
          }
          updateChartWithData(powerData, coolingLoadData);
        }, 200);

      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    // Initial load with a delay to ensure DOM is ready
    const initTimer = setTimeout(initializeAndFetchData, 300);

    // Add resize event listener
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      console.log('BuildingLoadGraph component unmounting');
      clearTimeout(initTimer);
      window.removeEventListener('resize', handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose();
        chartInstanceRef.current = null;
      }
    };
  }, [siteId]);

  return (
    <div className="p-2.5 alto-card">
      <div className="text-[#065BA9] text-sm font-semibold mb-2">Building Load</div>
      {loading ? (
        <div className="flex items-center justify-center h-[300px]">
          <Loader/>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-[300px] text-red-500">
          {error}
        </div>
      ) : (
        <div ref={chartRef} style={{ width: "100%", height: "250px" }} />
      )}
    </div>
  );
};

export default BuildingLoadGraph;
