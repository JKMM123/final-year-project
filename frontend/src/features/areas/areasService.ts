import axiosInstance from '../../services/axiosInstance';
import type { Area, AreaPayload, GetAreasApiResponse } from './types';
import type { Pagination } from '../../hooks/usePaginatedFetch';

interface GetAreasParams {
  page: number;
  limit: number;
  query?: string;
}

export const getAreas = async (params: GetAreasParams): Promise<{ items: Area[], pagination: Pagination }> => {
  const urlParams = new URLSearchParams({
    page: String(params.page),
    limit: String(params.limit),
  });
  if (params.query) urlParams.append('query', params.query);

  const response = await axiosInstance.get<GetAreasApiResponse>(`/areas/search?${urlParams.toString()}`);
  return {
    items: response.data.data.areas,
    pagination: response.data.data.pagination,
  };
};

export const createArea = async (payload: AreaPayload): Promise<Area> => {
  const response = await axiosInstance.post<Area>('/areas/create', payload);
  return response.data;
};

export const updateArea = async (areaId: string, payload: AreaPayload): Promise<Area> => {
  const response = await axiosInstance.put<Area>(`/areas/${areaId}`, payload);
  return response.data;
};

export const deleteArea = async (areaId: string): Promise<void> => {
  await axiosInstance.delete(`/areas/${areaId}`);
};