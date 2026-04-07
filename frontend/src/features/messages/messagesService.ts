// src/pages/Messages/messagesService.ts

import axiosInstance from '../../services/axiosInstance';
import type { 
  Template, 
  TemplateSearchPayload, 
  GetTemplatesApiResponse,
  CreateTemplatePayload,
  UpdateTemplatePayload,
  SendMessagePayload,
  GetAreasParams,
  Area,
  GetPackagesParams,
  Package,
  MeterSearchPayload,
  Meter
} from './types';
import type { Pagination } from '../../hooks/usePaginatedFetch';

// Helper type for single-item API responses
interface ApiResponse<T> {
  data: T;
}

export const getTemplates = async (payload: TemplateSearchPayload): Promise<{ items: Template[], pagination: Pagination }> => {
  const params = new URLSearchParams({
    page: String(payload.page),
    limit: String(payload.limit),
  });
  if (payload.query) {
    params.append('query', payload.query);
  }

  const response = await axiosInstance.get<GetTemplatesApiResponse>(`/templates/search?${params.toString()}`);
  return {
    items: response.data.data.templates,
    pagination: response.data.data.pagination,
  };
};

export const createTemplate = async (payload: CreateTemplatePayload): Promise<Template> => {
  const response = await axiosInstance.post<ApiResponse<Template>>('/templates/create', payload);
  return response.data.data;
};

export const updateTemplate = async (templateId: string, payload: UpdateTemplatePayload): Promise<Template> => {
  const response = await axiosInstance.put<ApiResponse<Template>>(`/templates/${templateId}`, payload);
  return response.data.data;
};

export const deleteTemplate = async (templateId: string): Promise<void> => {
  await axiosInstance.delete(`/templates/${templateId}`);
};

export const sendMessage = async (payload: SendMessagePayload): Promise<void> => {
  await axiosInstance.post('/messages/send-messages', payload);
};
export const getMeters = async (
  payload: MeterSearchPayload
): Promise<{ items: Meter[]; pagination: Pagination }> => {
  const response = await axiosInstance.post<{ data: { meters: Meter[]; pagination: Pagination } }>(
    '/meters/search', 
    payload
  );
  return {
    items: response.data.data.meters,
    pagination: response.data.data.pagination,
  };
};


// --- New Service Functions ---

// Note: Your snippet for getPackages had a typo `response.data.data.areas`, I corrected it to `packages`
export const getPackages = async (
  params: GetPackagesParams
): Promise<{ items: Package[]; pagination: Pagination }> => {
  const urlParams = new URLSearchParams({
    page: String(params.page),
    limit: String(params.limit),
  });
  if (params.amperage) urlParams.append("amperage", String(params.amperage));
  
  const response = await axiosInstance.get<{ data: { packages: Package[]; pagination: Pagination } }>(
    `/packages/search?${urlParams.toString()}`
  );
  return {
    items: response.data.data.packages,
    pagination: response.data.data.pagination,
  };
};

// I've created this based on the pattern of your other services
export const getAreas = async (
  params: GetAreasParams
): Promise<{ items: Area[]; pagination: Pagination }> => {
  const urlParams = new URLSearchParams({
    page: String(params.page),
    limit: String(params.limit),
  });
  if (params.query) urlParams.append("query", params.query);

  const response = await axiosInstance.get<{ data: { areas: Area[]; pagination: Pagination } }>(
    `/areas/search?${urlParams.toString()}`
  );
  return {
    items: response.data.data.areas,
    pagination: response.data.data.pagination,
  };
};


interface GetSessionStatusResponse {
  message: string;
  status: number;
  data?: {
    status: string;
  };
}

/**
 * Fetch the current WhatsApp session status.
 * Returns the raw status string or null if disconnected.
 */
export const getSessionStatus = async (): Promise<string | null> => {
  try {
    const response = await axiosInstance.get<GetSessionStatusResponse>(
      'session/status'
    );
    return response.data?.data?.status || null;
  } catch (error) {
    // Any error (including 404) means not connected
    return null;
  }
};