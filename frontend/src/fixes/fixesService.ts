// src/features/fixes/fixesService.ts

import axiosInstance from "../../services/axiosInstance"; // Assuming you have a configured axios instance
import type { Pagination } from "../../hooks/usePaginatedFetch";
import type {
  Fix,
  FixSearchPayload,
  FixCreatePayload,
  FixUpdatePayload,
  GetFixesApiResponse,
  Meter,
  MeterSearchPayload,
  GetMetersApiResponse,
} from "./types";

/**
 * Fetches a paginated list of fixes based on search criteria.
 */
export const getFixes = async (payload: FixSearchPayload): Promise<{ items: Fix[], pagination: Pagination }> => {
  const response = await axiosInstance.post<GetFixesApiResponse>('/fixes/search', payload);
  return {
    items: response.data.data.fixes,
    pagination: response.data.data.pagination,
  };
};

/**
 * Creates a new fix.
 */
export const createFix = async (payload: FixCreatePayload): Promise<Fix> => {
  const response = await axiosInstance.post<{ data: Fix }>('/fixes/create', payload);
  return response.data.data;
};

/**
 * Updates an existing fix.
 */
export const updateFix = async (fixId: string, payload: FixUpdatePayload): Promise<Fix> => {
  const response = await axiosInstance.put<{ data: Fix }>(`/fixes/${fixId}`, payload);
  return response.data.data;
};

/**
 * Deletes one or more fixes. For this implementation, we delete one at a time.
 */
export const deleteFix = async (fixId: string): Promise<void> => {
  // API expects an array of IDs
  const payload = { fix_ids: [fixId] };
  await axiosInstance.delete('/fixes/delete', { data: payload });
};

/**

 * Searches for meters by customer name.
 * Used in the Create Fix modal.
 */
export const getMeters = async (payload: MeterSearchPayload): Promise<{ items: Meter[], pagination: Pagination }> => {
  const response = await axiosInstance.post<GetMetersApiResponse>('/meters/search', payload);
  return {
    items: response.data.data.meters,
    pagination: response.data.data.pagination,
  };
};