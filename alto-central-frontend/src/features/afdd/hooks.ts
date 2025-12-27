/**
 * AFDD (Automated Fault Detection & Diagnostics) - Mock implementation
 */

export interface CategoryAlertSummary {
  category: string;
  critical: number;
  warning: number;
  info: number;
  total: number;
}

export function useAFDDAlertSummary() {
  // Mock data - no alerts
  const categories: CategoryAlertSummary[] = [
    { category: 'water-side', critical: 0, warning: 0, info: 0, total: 0 },
    { category: 'air-side', critical: 0, warning: 0, info: 0, total: 0 },
    { category: 'others', critical: 0, warning: 0, info: 0, total: 0 },
  ];

  return {
    categories,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}
