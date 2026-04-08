import axiosInstance from '../../services/axiosInstance';
import type { DashboardSummary, GetDashboardApiResponse } from './types';

// Fetches the dashboard summary for a given month (e.g., "2025-07")
export const getDashboardSummary = async (month: string): Promise<DashboardSummary> => {
  const response = await axiosInstance.get<GetDashboardApiResponse>(`/dashboard/summary?month=${month}`);
  // Return the nested data object directly for cleaner use in the component
  return response.data.data;
};