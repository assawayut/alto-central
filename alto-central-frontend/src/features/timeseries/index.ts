/**
 * Timeseries feature - Mock implementation
 */

interface FetchAggregatedDataParams {
  site_id: string;
  device_id: string;
  datapoints: string[];
  start_timestamp: string | null;
  end_timestamp: string | null;
  resampling: string;
}

interface TimeseriesValue {
  timestamp: string;
  value: number;
}

interface TimeseriesDatapoint {
  site_id: string;
  device_id: string;
  model: string;
  datapoint: string;
  values: TimeseriesValue[];
}

interface TimeseriesResponse {
  data: {
    data: TimeseriesDatapoint[];
  };
}

// Generate mock hourly data for today
function generateMockHourlyData(baseValue: number, variance: number): TimeseriesValue[] {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const values: TimeseriesValue[] = [];

  for (let i = 0; i < 24; i++) {
    const timestamp = new Date(now);
    timestamp.setHours(i);

    // Simulate typical building load pattern
    let multiplier = 0.3; // Night
    if (i >= 6 && i <= 8) multiplier = 0.5 + (i - 6) * 0.15; // Morning ramp up
    else if (i >= 9 && i <= 17) multiplier = 0.8 + Math.sin((i - 9) * 0.3) * 0.2; // Peak hours
    else if (i >= 18 && i <= 21) multiplier = 0.7 - (i - 18) * 0.1; // Evening ramp down

    values.push({
      timestamp: timestamp.toISOString(),
      value: baseValue * multiplier + (Math.random() - 0.5) * variance,
    });
  }

  return values;
}

export async function fetchAggregatedData(params: FetchAggregatedDataParams): Promise<TimeseriesResponse> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));

  const data: TimeseriesDatapoint[] = [];

  if (params.device_id === 'plant') {
    if (params.datapoints.includes('power')) {
      data.push({
        site_id: params.site_id,
        device_id: 'plant',
        model: 'plant',
        datapoint: 'power',
        values: generateMockHourlyData(80, 20),
      });
    }
    if (params.datapoints.includes('cooling_rate')) {
      data.push({
        site_id: params.site_id,
        device_id: 'plant',
        model: 'plant',
        datapoint: 'cooling_rate',
        values: generateMockHourlyData(100, 30),
      });
    }
  }

  if (params.device_id === 'air_distribution_system') {
    if (params.datapoints.includes('power')) {
      data.push({
        site_id: params.site_id,
        device_id: 'air_distribution_system',
        model: 'air_distribution_system',
        datapoint: 'power',
        values: generateMockHourlyData(50, 15),
      });
    }
  }

  return { data: { data } };
}
