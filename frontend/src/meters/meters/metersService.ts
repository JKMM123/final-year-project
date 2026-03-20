import axiosInstance from '../../services/axiosInstance';
import type { GetMetersApiResponse, Meter, MeterCreatePayload, MeterSearchPayload, MeterUpdatePayload, QrCodeResponse, StatementData } from './types';
import type { Pagination } from '../../hooks/usePaginatedFetch';

// This is a POST request with a JSON body for filtering
export const getMeters = async (payload: MeterSearchPayload): Promise<{ items: Meter[], pagination: Pagination }> => {
  const response = await axiosInstance.post<GetMetersApiResponse>('/meters/search', payload);
  return {
    items: response.data.data.meters,
    pagination: response.data.data.pagination,
  };
};

export const createMeter = async (payload: MeterCreatePayload): Promise<Meter> => {
  const response = await axiosInstance.post<Meter>('/meters/create', payload);
  return response.data;
};

export const updateMeter = async (meterId: string, payload: MeterUpdatePayload): Promise<Meter> => {
  const response = await axiosInstance.put<Meter>(`/meters/${meterId}`, payload);
  return response.data;
};

export const deleteMeter = async (meterId: string): Promise<void> => {
  await axiosInstance.delete(`/meters/${meterId}`);
};

export const getMeterQrCode = async (meterId: string): Promise<string> => {
  const response = await axiosInstance.get<QrCodeResponse>(`/meters/${meterId}/qr-code`);
  return response.data.data.qr_code_url;
};

// ... existing getMeters, createMeter, updateMeter, deleteMeter, getMeterQrCode functions

// Gets the URL for the all-in-one QR code zip file
export const getAllQrCodesZipUrl = async (): Promise<string> => {
  // Assuming the API returns a simple object with a url property
  const response = await axiosInstance.get<{ data: string }>('/meters/qr-codes');
  return response.data.data;
};

// Uploads a meters file (CSV or Excel)
export const uploadMetersFile = async (file: File): Promise<any> => {
  const formData = new FormData();
  formData.append('meters_file', file); // The key 'meters_file' must match your backend API

  // Axios will automatically set the 'Content-Type' to 'multipart/form-data'
  const response = await axiosInstance.post(
  "/meters/upload",
  formData,
  { headers: { "Content-Type": "multipart/form-data" },
    timeout: 70000  // Set timeout to 60 seconds
}
);
  return response.data;
};


interface StatementApiResponse {
  data: StatementData;
  message: string;
  status: number;
}

/**
 * Fetches the annual statement for a given meter.
 * @param meterId The ID of the meter.
 * @param year The year for the statement.
 * @returns A promise that resolves to the statement data.
 */
export const getStatement = async (
  meterId: string,
  year: number
): Promise<StatementData> => {
  const response = await axiosInstance.get<StatementApiResponse>(
    `/bills/statement`,
    {
      params: {
        meter_id: meterId,
        year,
      },
    }
  );
  return response.data.data;
};

/**
 * Marks all unpaid bills for a given meter as paid.
 * @param {string} meterId - The ID of the meter.
 * @param {string} paymentMethod - The method of payment (e.g., 'cash', 'omt').
 */
export const markAllUnpaidAsPaid = async (
  meterId: string,
  paymentMethod: string
): Promise<void> => {
  // The original cURL command uses a GET request, but a POST is more semantically
  // correct for an action that changes data on the server.
  // I'll use POST here, but you can change it to `apiClient.get` if your backend requires it.
  const response = await axiosInstance.post(
    `/payments/mark-as-paid?meter_id=${meterId}&payment_method=${paymentMethod}`
  );
  return response.data;
};