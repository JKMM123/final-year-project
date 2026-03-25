import axiosInstance from '../../services/axiosInstance';
import type { GetMetersForReadingApiResponse, GetReadingDetailsApiResponse, GetReadingsApiResponse, GetSummaryApiResponse, Reading, ReadingsSummary, VerifyAllApiResponse, VerifyAllReadingsPayload } from './types';
import type { MeterSearchPayload } from '../meters/types'; // Reuse from meters
import type { Pagination } from '../../hooks/usePaginatedFetch';

interface ReadingsSearchPayload {
  page: number;
  limit: number;
  query?: string;
  status?: string[];
  reading_date?: string;
  area_ids?: string[];
}

export const getMetersAwaitingReading = async (payload: MeterSearchPayload): Promise<{ items: any[], pagination: Pagination }> => {
  const response = await axiosInstance.post<GetMetersForReadingApiResponse>('/meters/search', payload);
  // Map initial_reading to current_reading for UI consistency if backend doesn't send it yet
  const items = response.data.data.meters.map(m => ({...m, current_reading: m.initial_reading}));
  return { items, pagination: response.data.data.pagination };
};

export const createReading = async (payload: { meter_id: string; current_reading: number }): Promise<Reading> => {
  const response = await axiosInstance.post<Reading>('/readings/create', payload);
  return response.data;
};

export const getCollectedReadings = async (payload: ReadingsSearchPayload): Promise<{ items: Reading[], pagination: Pagination }> => {
  const response = await axiosInstance.post<GetReadingsApiResponse>('/readings/search', payload);
  return {
    items: response.data.data.readings,
    pagination: response.data.data.pagination,
  };
};

export const getReadingDetails = async (readingId: string): Promise<Reading> => {
  const response = await axiosInstance.get<GetReadingDetailsApiResponse>(`/readings/${readingId}`);
  return response.data.data;
}

export const verifyReading = async (readingId: string, payload: { current_reading: number; status: 'verified' }): Promise<Reading> => {
  const response = await axiosInstance.put<Reading>(`/readings/${readingId}`, payload);
  return response.data;
};

export const getReadingsSummary = async (readingDate: string): Promise<ReadingsSummary> => {
  const response = await axiosInstance.get<GetSummaryApiResponse>(`/readings/summary?reading_date=${readingDate}`);
  return response.data.data;
};

export const validateSession = async (): Promise<boolean> => {
  try {
    // This API call relies on the HttpOnly cookie being sent automatically by the browser.
    await axiosInstance.get('/auth/validate-token');
    return true;
  } catch {
    return false;
  }
};

interface ScanResponse {
  current_reading: number;
  image_url: string;
}

// Uploads the captured image for a specific meter
export const scanReading = async (meterId: string, imageFile: Blob): Promise<ScanResponse> => {
  const formData = new FormData();
  formData.append('reading', imageFile, `reading_${meterId}.jpg`);

  const response = await axiosInstance.post<{ data: ScanResponse }>(
    `/readings/${meterId}/scan`, 
    formData,
    {
      headers: { "Content-Type": undefined }
    }
  );
  return response.data.data;
};

interface ConfirmScanPayload {
  meterId: string;
  current_reading: number;
  imageFile: Blob;
}

export const confirmScannedReading = async ({ meterId, current_reading, imageFile }: ConfirmScanPayload): Promise<Reading> => {
  const formData = new FormData();
  formData.append('reading', imageFile, `reading_${meterId}_confirmed.jpg`);

  // Build the URL with query parameters as required
  const url = `/readings/${meterId}/scan?current_reading=${current_reading}&accept_reading=true`;

  const response = await axiosInstance.post<GetReadingDetailsApiResponse>(
    url,
    formData,
    {
      headers: { "Content-Type": undefined }
    }
  );
  // Assuming the API returns the final created reading object upon confirmation
  return response.data.data;
};

export const createReadingWithImage = async (
  meterId: string,
  currentReading: number,
  imageFile: File | Blob
): Promise<Reading> => {
  const formData = new FormData();
  // The key 'reading' must match the API specification
  formData.append('reading', imageFile, `manual_reading_${meterId}.jpg`);

  // --- CHANGE: Build the URL with query parameters for the /create endpoint ---
  const url = `/readings/create?current_reading=${currentReading}&meter_id=${meterId}`;

  const response = await axiosInstance.post<GetReadingDetailsApiResponse>(
    url,
    formData,
    {
      // Let the browser set the Content-Type header to multipart/form-data
      headers: { "Content-Type": undefined }
    }
  );
  // Assuming the API response for a successful upload returns the complete reading object
  return response.data.data;
};

/**
 * Verifies all pending readings for a specific month.
 * @param payload - The payload containing the confirmation and reading date.
 * @returns A promise with the verification API response.
 */
export const verifyAllReadings = async (
  payload: VerifyAllReadingsPayload
): Promise<VerifyAllApiResponse> => {
  const response = await axiosInstance.post<VerifyAllApiResponse>(
    '/readings/verify-all',
    payload
  );
  // The API returns the full response object directly in the data property
  return response.data;
};

export const deleteReading = async (readingId: string): Promise<void> => {
  await axiosInstance.delete(`/readings/${readingId}`);
};
