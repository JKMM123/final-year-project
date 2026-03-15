import axiosInstance from '../../services/axiosInstance';
import type { GetPackagesApiResponse, GetPackagesParams, MonthlyRate, Package, PackagePayload, RatesByYearResponse } from './types';
import type { Pagination } from '../../hooks/usePaginatedFetch';



// --- Package Services ---

export const getPackages = async (params: GetPackagesParams): Promise<{ items: Package[], pagination: Pagination }> => {
  const urlParams = new URLSearchParams({
    page: String(params.page),
    limit: String(params.limit),
  });
  if (params.amperage) urlParams.append('amperage', String(params.amperage));

  const response = await axiosInstance.get<GetPackagesApiResponse>(`/packages/search?${urlParams.toString()}`);
  return {
    items: response.data.data.packages,
    pagination: response.data.data.pagination,
  };
};

export const createPackage = async (payload: PackagePayload): Promise<Package> => {
  const response = await axiosInstance.post<Package>('/packages/create', payload);
  return response.data;
};

export const updatePackage = async (packageId: string, payload: PackagePayload): Promise<Package> => {
  const response = await axiosInstance.put<Package>(`/packages/${packageId}`, payload);
  return response.data;
};

export const deletePackage = async (packageId: string): Promise<void> => {
  await axiosInstance.delete(`/packages/${packageId}`);
};


/**
 * Fetches all the rates recorded for a specific year.
 * @param {number} year The year to fetch rates for.
 * @returns {Promise<MonthlyRate[]>} A promise that resolves to an array of monthly rates.
 */
export const getRatesByYear = async (year: number): Promise<MonthlyRate[]> => {
  // The endpoint expects the year to be part of the URL path
  const response = await axiosInstance.get<RatesByYearResponse>(`/rates/all/${year}`);
  
  // The API returns the rates within the 'data' property of the response
  // We return response.data.data to get the array of MonthlyRate objects
  return response.data.data;
};