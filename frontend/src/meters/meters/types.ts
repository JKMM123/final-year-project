import type { Pagination } from '../../hooks/usePaginatedFetch';

// Matches the meter object from your API response
export interface Meter {
  meter_id: string;
  customer_full_name: string;
  customer_phone_number: string;
  initial_reading?: number;
  status?: 'active' | 'inactive';
  address: string;
  package_id: string;
  amperage: number;
  package_type: 'usage' | 'fixed';
  area_id: string;
  area_name?: string; // Added for convenience in UI
  previous_reading?: number; // Optional, for meters that have readings
  hasReading ?: boolean; // Optional, indicates if a reading exists for the current period
}

// Payload for creating a meter
export type MeterCreatePayload = Omit<Meter, 'meter_id' | 'status' | 'amperage'>;
// Payload for updating a meter
export type MeterUpdatePayload = Omit<Meter, 'meter_id' | 'amperage' >;

// Structure for the complex search API body
export interface MeterSearchPayload {
  page: number;
  limit: number;
  query?: string;
  package_type?: string;
  package_ids?: string[];
  area_ids?: string[];
  status?: string[];
  reading_date?: string; // Optional, for searching by reading date
}

// The nested structure of your GET /meters/search API response
export interface GetMetersApiResponse {
  data: {
    meters: Meter[];
    pagination: Pagination;
  };
}

// QR Code API Response
export interface QrCodeResponse {
  data: {
    qr_code_url: string;
  };
}

// Represents the meter information within the statement
export interface StatementMeterInfo {
  meter_id: string;
  customer_name: string;
  customer_phone: string;
  address: string;
  area_name: string;
  elevation: number;
  package_type: "fixed" | "usage";
  amperage: number;
  status: "active" | "inactive";
}

// Represents the summary for the entire year
export interface YearSummary {
  total_bills: number;
  total_billed_lbp: number;
  total_billed_usd: number;
  total_paid_lbp: number;
  total_paid_usd: number;
  total_unpaid_lbp: number;
  total_unpaid_usd: number;
  total_fixes_cost: number;
  payment_completion_rate: number;
}

// Represents the detailed breakdown for a single month
export interface MonthDetail {
  month: number;
  month_name: string;
  billing_period: string;
  package_type: "fixed" | "usage";
  amperage: number;
  bill_exists: boolean;
  bill_id: string | null;
  bill_number: string | null;
  due_date: string | null;
  status: "paid" | "unpaid" | "partially_paid" | "no_bill";
  amount_due_lbp: number;
  amount_due_usd: number;
  total_paid_lbp: number;
  total_paid_usd: number;
  unpaid_lbp: number;
  unpaid_usd: number;
  dollar_rate: number | null;
  kwh_rate: number | null;
  kwh_rate_type: string;
  fixes_count: number;
  fixes_cost: number;
  fixes: any[]; // Define a proper type if needed
  payments_count: number;
  payments: any[]; // Define a proper type if needed
  activation_fee: number;
  reading_exists: boolean;
  current_reading: number | null;
  previous_reading: number | null;
  usage: number | null;
  reading_date: string | null;
  reading_sequence: number | null;
  usage_cost: number;
}

// Represents the entire payload from the /statement API
export interface StatementData {
  year: number;
  meter_info: StatementMeterInfo;
  year_summary: YearSummary;
  months: MonthDetail[];
}