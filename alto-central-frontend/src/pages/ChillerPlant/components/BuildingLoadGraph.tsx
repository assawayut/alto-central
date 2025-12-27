import { useEffect, useRef, useState } from "react";
import { Loader } from "@/components/ui/loader";
import * as echarts from "echarts";
import { useAuth } from "@/features/auth";
import { fetchAggregatedData } from "@/features/timeseries";
import { getSiteId } from "@/features/auth";
import { DateTime } from 'luxon';

// Define the interface for the transformed data structure that matches what the component expects
interface TransformedData {
  bucket: string;
  avg_value: number;
  site_id: string;
  device_id: string;
  model: string;
  datapoint: string;
}

const BuildingLoadGraph: React.FC = () => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { site } = useAuth();

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

    const startDatetime = DateTime.now().startOf('day');
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
          const date = new Date(params[0].data[0]);
          const dateString = date.toLocaleString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          timeZone: site?.timezone || "Asia/Bangkok",
          });

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
        splitNumber: 8,
        min: startDatetime.toJSDate().toISOString(),
        max: endDateTime.toJSDate().toISOString(),
        axisLabel: {
          formatter: function (params: number) {
            const date = new Date(params);
            return String(date.getHours()).padStart(2, "0");
          },
          margin: 12,
          fontSize: 12,
          color: "#788796",
          interval: 2 * 3600 * 1000,
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
        bottom: "3%",
        top: "15%",
        containLabel: true,
      },
    });
  };

  const updateChartWithData = (powerData: TransformedData[], coolingLoadData: TransformedData[]) => {
    if (!chartInstanceRef.current) return;

    const chartInstance = chartInstanceRef.current;

    const transformData = (data: TransformedData[]) => {
      return data.map(item => [
        new Date(item.bucket).getTime(),
        item.avg_value
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
    console.log('BuildingLoadGraph component mounted');
    
    const handleResize = () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.resize();
      }
    };

    const initializeAndFetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Initialize chart first
        initializeChart();

        // Get site ID
        const siteId = getSiteId() || '';
        
        const startTime = DateTime.now().startOf('day');
        const endTime = startTime.plus({ days: 1 });

        // Fetch power and cooling load data using fetchAggregatedData
        const [plantResponse, airResponse] = await Promise.all([
          fetchAggregatedData({
            site_id: siteId,
            device_id: 'plant',
            datapoints: ['power', 'cooling_rate'],
            start_timestamp: startTime.toISO(),
            end_timestamp: endTime.toISO(),
            resampling: '1h'
          }),
          fetchAggregatedData({
            site_id: siteId,
            device_id: 'air_distribution_system',
            datapoints: ['power'],
            start_timestamp: startTime.toISO(),
            end_timestamp: endTime.toISO(),
            resampling: '1h'
          })
        ]);
        
        // Access the nested data array from the API response
        // Type assertion needed because API returns nested structure not reflected in types
        const plantResponseData = (plantResponse.data as any)?.data || [];
        const airResponseData = (airResponse.data as any)?.data || [];
        
        // Extract plant power data
        const plantPowerData = plantResponseData
          .filter((item: any) => item.datapoint === 'power')
          .flatMap((item: any) => item.values.map((value: any) => ({
            bucket: value.timestamp,
            avg_value: value.value,
            site_id: item.site_id,
            device_id: item.device_id,
            model: item.model,
            datapoint: item.datapoint
          })));
        
        // Extract air distribution system power data
        const airPowerData = airResponseData
          .filter((item: any) => item.datapoint === 'power')
          .flatMap((item: any) => item.values.map((value: any) => ({
            bucket: value.timestamp,
            avg_value: value.value,
            site_id: item.site_id,
            device_id: item.device_id,
            model: item.model,
            datapoint: item.datapoint
          })));
        
        // Combine plant and air distribution system power data
        const combinedPowerData: TransformedData[] = [];
        plantPowerData.forEach((plantPoint: TransformedData) => {
          const airPoint = airPowerData.find((air: TransformedData) => air.bucket === plantPoint.bucket);
          combinedPowerData.push({
            bucket: plantPoint.bucket,
            avg_value: plantPoint.avg_value + (airPoint?.avg_value || 0),
            site_id: plantPoint.site_id,
            device_id: 'combined_power',
            model: plantPoint.model,
            datapoint: 'power'
          });
        });
        
        const coolingLoadData = plantResponseData
          .filter((item: any) => item.datapoint === 'cooling_rate')
          .flatMap((item: any) => item.values.map((value: any) => ({
            bucket: value.timestamp,
            avg_value: value.value,
            site_id: item.site_id,
            device_id: item.device_id,
            model: item.model,
            datapoint: item.datapoint
          })));

        // Try updating chart with a small delay to ensure container is ready
        setTimeout(() => {
          if (!chartInstanceRef.current) {
            initializeChart();
          }
          updateChartWithData(combinedPowerData, coolingLoadData);
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
  }, []);

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