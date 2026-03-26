import type { Pagination } from '../../hooks/usePaginatedFetch';

export type BillStatus = 'paid' | 'unpaid' | 'partially_paid';

// Matches the bill object from your API response
export interface Bill {
  bill_id: string;
  customer_full_name?: string; // Add this from your UI requirement
  amount: number;
  amount_due_usd: number;
  amount_due_lbp:number;
  due_date: string;
  status: BillStatus;
  payment_date: string | null;
  payment_method: 'cash' | 'whish' | null;
  bill_url?: string;
  bill_number: number;
   total_paid_lbp: string;
  total_paid_usd: string;
}

// Search payload for the API
export interface BillSearchPayload {
  page: number;
  limit: number;
  query?: string;
  due_date?: string;
  status?: string[];
  payment_method?: string[];
}

// API Response Wrappers
export interface GetBillsApiResponse {
  data: {
    bills: Bill[];
    pagination: Pagination;
  };
}

export interface ApiResponse<T> {
  message: string;
  data: T;
  status: number;
  timeStamp: string;
}

// Data returned when starting the PDF generation task.

// ✅ Inner shape when bills exist
export interface StartDownloadSuccessData {
  task_id: string;
  total_bills: number;
  chunk_size: number;
  estimated_chunks: number;
}

// ✅ Unified API response wrapper
export interface StartDownloadBase<T> {
  message: string;
  data: T;
  status: number;
  timeStamp: string;
}

// ✅ Specializations
export type StartDownloadSuccess = StartDownloadBase<StartDownloadSuccessData>;
export type StartDownloadNoBills = StartDownloadBase<[]>;

// ✅ Union type for function return
export type StartDownloadResponse = StartDownloadSuccess | StartDownloadNoBills;

/**
 * The 'result' object when a task is successful.
 */
export interface TaskResult {
  status: 'completed';
  total_bills: number;
  processed: number;
  failed: number;
  failed_bills: string[];
  download_url: string;
  zip_file: string;
  processing_time: string;
}

/**
 * Data returned when checking the status of a task.
 */
export interface TaskStatusData {
  task_id: string;
  status: 'SUCCESS' | 'PENDING' | 'FAILURE' | 'RETRY'; // Using string literals for status
  result: TaskResult | null;
}

/**
 * Represents the structure of a successful response from the bill generation API.
 */
export interface GenerationMetrics {
  total_active_meters: number;
  fixed_package_meters: number;
  usage_based_meters: number;
  meters_with_readings: number;
  verified_readings: number;
  unverified_readings: number;
  meters_without_readings: number; // Renamed from missing_meters for clarity
  bills_created: number;
  bills_already_exist: number;
  skipped_meters: number;
  errors: string[];
}

export interface GenerateBillsResponseData {
  task_id?: string; // Task ID is only present on final success
  metrics: GenerationMetrics;
  billing_period: string; // e.g., "2025-08"
  due_date: string; // e.g., "2025-09-01"
}

export interface GenerateBillsApiResponse {
  message: string;
  data: GenerateBillsResponseData;
  status: number;
  timeStamp: string;
}
/**
 * Represents a single field error in a validation response.
 */
export interface FieldError {
  field: string;
  message: string;
}

/**
 * Represents the structure of a generic API error, especially for validation.
 */
export interface ApiErrorResponse {
  message: string;
  error: string;
  fieldErrors?: FieldError[]; // fieldErrors is optional
  status: number;
  timeStamp: string;
}

// Represents a single payment record for a bill
export interface Payment {
  payment_id: string;
  amount_lbp: string;
  amount_usd: string;
  payment_method: "cash" | "whish" | "omt";
  payment_date: string; // e.g., "2025-11-04"
}

// Payload for creating a new payment
export interface CreatePaymentPayload {
  bill_id: string;
  amount_usd: number;
  // Note: API shows amount_lbp, but your logic focuses on USD.
  // We'll assume the backend calculates LBP or it's not needed from the frontend here.
  payment_method: "cash" | "whish" | "omt";
  payment_date: string;
}

// Payload for updating an existing payment
export interface UpdatePaymentPayload {
  amount_usd: number;
  payment_method: "cash" | "whish" | "omt";
  payment_date: string;
}

/**
 * Represents the structure of a single rate record from the API.
 */
export interface Rate {
  rate_id: string;
  mountain_kwh_rate: number;
  coastal_kwh_rate: number;
  dollar_rate: number;
  rate_date: string; // The specific date it was created/updated
  fixed_sub_hours: number;
  fixed_sub_rate: number;

}

/**
 * Payload for creating new billing rates.
 */
export interface CreateRatePayload {
  mountain_kwh_rate: number;
  coastal_kwh_rate: number;
  dollar_rate: number;
  effective_date: string; // Format: "YYYY-MM"
  fixed_sub_hours: number;
  fixed_sub_rate: number;
}

/**
 * Payload for updating existing billing rates.
 * Note: rate_id is passed in the URL, not the body.
 */
export interface UpdateRatePayload {
  mountain_kwh_rate: number;
  coastal_kwh_rate: number;
  dollar_rate: number;
  fixed_sub_hours: number;
  fixed_sub_rate: number;
}