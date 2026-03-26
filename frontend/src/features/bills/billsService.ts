import axiosInstance from '../../services/axiosInstance';
import type { ApiResponse, Bill, BillSearchPayload, CreateRatePayload, GenerateBillsApiResponse,
   GetBillsApiResponse, Rate, StartDownloadResponse, TaskStatusData,
   UpdateRatePayload} from './types';
import type { Pagination } from '../../hooks/usePaginatedFetch';

import type { CreatePaymentPayload, Payment, UpdatePaymentPayload } from "./types";

export const getBills = async (payload: BillSearchPayload): Promise<{ items: Bill[], pagination: Pagination }> => {
  const response = await axiosInstance.post<GetBillsApiResponse>('/bills/search', payload);
  return {
    items: response.data.data.bills,
    pagination: response.data.data.pagination,
  };
};

/**
 * Triggers the bill generation process on the backend.
 * @param billingDate - The due date for the bills, formatted as 'YYYY-MM-DD'. This is the first day of the month *after* the billing period.
 * @param forceMissingMeter - Flag to generate bills even if some meters have no readings.
 * @param forceUnverifiedReadings - Flag to generate bills using only verified readings, ignoring unverified ones.
 * @returns A promise that resolves to the API response data.
 */
// export const generateBills = async (
//   billingDate: string,
//   forceMissingMeter = false,
//   forceUnverifiedReadings = false
// ): Promise<GenerateBillsSuccessResponse> => {
//   const urlParams = new URLSearchParams();
  
//   // Append the new mandatory billing_date parameter
//   urlParams.append('billing_date', billingDate);

//   // Append optional force flags if they are true
//   if (forceMissingMeter) {
//     urlParams.append('force_missing_meter', 'true');
//   }
//   if (forceUnverifiedReadings) {
//     urlParams.append('force_unverified_readings', 'true');
//   }
  
//   const response = await axiosInstance.post(`/bills/generate?${urlParams.toString()}`);
//   return response.data;
// };

export const deleteBill = async (billId: string): Promise<void> => {
  await axiosInstance.delete(`/bills/${billId}`);
};

export const getBillById = async (billId: string): Promise<Bill> => {
  const response = await axiosInstance.get<ApiResponse<Bill>>(`/bills/${billId}`);
  // Returning the nested data object which matches the 'Bill' type
  return response.data.data;
};

/**
 * Sends a request to the API to start the generation of the bills PDF.
 * This is an asynchronous task.
 * @param billingDate The billing date in 'YYYY-MM-DD' format.
 * @returns An object containing the task_id.
 */
export const startBillsGeneration = async (
  billingDate: string
): Promise<StartDownloadResponse> => {
  const urlParams = new URLSearchParams({ billing_date: billingDate });

  const response = await axiosInstance.post<StartDownloadResponse>(
    `/bills/download?${urlParams.toString()}`
  );

  return response.data;
};



/**
 * Checks the status of a previously started PDF generation task.
 * @param taskId The ID of the task to check.
 * @returns The current status and result of the task.
 */
export const getTaskStatus = async (taskId: string): Promise<TaskStatusData> => {
  const response = await axiosInstance.get<ApiResponse<TaskStatusData>>(
    `/tasks/${taskId}/status`
  );

  if (!response.data?.data) {
    throw new Error("API did not return valid task status information.");
  }

  return response.data.data;
};


/**
 * Fetches all payments associated with a specific bill.
 */
export const getAllPaymentsForBill = async (billId: string): Promise<Payment[]> => {
  const response = await axiosInstance.get<ApiResponse<Payment[]>>(`/payments/all?bill_id=${billId}`);
  return response.data.data;
};

/**
 * Creates a new payment for a bill.
 */
export const createPayment = async (payload: CreatePaymentPayload): Promise<Payment> => {
  const response = await axiosInstance.post<Payment>(`/payments/create`, payload);
  return response.data;
};

/**
 * Updates an existing payment.
 */
export const updatePayment = async (
  paymentId: string,
  payload: UpdatePaymentPayload
): Promise<Payment> => {
  const response = await axiosInstance.put<Payment>(`/payments/${paymentId}`, payload);
  return response.data;
};

/**
 * Deletes a payment.
 */
export const deletePayment = async (paymentId: string): Promise<void> => {
  await axiosInstance.delete(`/payments/${paymentId}`);
};



/**
 * Fetches the billing rates for a specific month.
 * @param month - The billing month in "YYYY-MM" format.
 * @returns A promise that resolves to the API response containing the rate data.
 */
export const getRateByMonth = async (month: string): Promise<ApiResponse<Rate>> => {
  const response = await axiosInstance.get(`/rates/${month}`);
  return response.data;
};

/**
 * Creates new billing rates for a specific month.
 * @param payload - The rate data to create.
 * @returns A promise that resolves to the API response with the newly created rate data.
 */
export const createRate = async (payload: CreateRatePayload): Promise<ApiResponse<Rate>> => {
  const response = await axiosInstance.post('/rates/create', payload);
  return response.data;
};

/**
 * Updates existing billing rates.
 * @param rateId - The ID of the rate record to update.
 * @param payload - The new rate data.
 * @returns A promise that resolves to the API response with the updated rate data.
 */
export const updateRate = async (rateId: string, payload: UpdateRatePayload): Promise<ApiResponse<Rate>> => {
  const response = await axiosInstance.put(`/rates/${rateId}`, payload);
  return response.data;
};


/**
 * Triggers the bill generation process on the backend.
 * @param billingDate - The billing period, formatted as 'YYYY-MM'.
 * @param rateId - The ID of the rates to use for this billing period.
 * @param forceMissingMeter - Flag to generate bills even if some meters have no readings.
 * @param forceUnverifiedReadings - Flag to generate bills using only verified readings.
 * @returns A promise that resolves to the API response data.
 */

export const generateBills = async (
  billingDate: string,
  rateId: string,
  forceMissingMeter = false,
  forceUnverifiedReadings = false
): Promise<GenerateBillsApiResponse> => {
  const urlParams = new URLSearchParams();
  
  urlParams.append('billing_date', billingDate);
  urlParams.append('rate_id', rateId);

  if (forceMissingMeter) {
    urlParams.append('force_missing_meter', 'true');
  }
  if (forceUnverifiedReadings) {
    urlParams.append('force_unverified_readings', 'true');
  }
  
  // The API now returns 200 for all these scenarios, so we expect the success type.
  const response = await axiosInstance.post(`/bills/generate?${urlParams.toString()}`);
  return response.data;
};