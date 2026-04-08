// src/pages/Dashboard/types.ts

// Represents earnings for a specific currency pair
export interface CurrencyEarnings {
  total_earnings_lbp: number;
  total_earnings_usd: number;
}

// Represents the breakdown of meters by type (fixed, usage, total)
export interface MeterCategoryDetail {
  fixed: number;
  usage: number;
  total: number;
}

// Nested object for Meters summary
export interface MeterSummary {
  active: MeterCategoryDetail;
  inactive: MeterCategoryDetail;
  total: MeterCategoryDetail;
}

// Nested object for Readings summary
export interface ReadingSummary {
  verified: number;
  pending: number;
}

// Nested object for Bills summary
export interface BillSummary {
  generated: number;
  ungenerated: number;
}

// Nested object for Bills Payment Status
export interface BillPaymentStatus {
  paid: {
    total: number;
    cash: number;
    whish: number;
    omt: number;
  };
  unpaid: number;
  partially_paid?: number; // New metric, made optional
}

// Nested object for Earnings, now with breakdown
export interface EarningsSummary {
  whish?: CurrencyEarnings;
  cash?: CurrencyEarnings;
  omt?: CurrencyEarnings;
  total: CurrencyEarnings;
}

// Nested object for Unpaid Arrears
export interface UnpaidArrearsSummary {
  total_unpaid_lbp: number;
  total_unpaid_usd: number;
  total_unpaid_this_month_lbp: number;
  total_unpaid_this_month_usd: number;
}

// The main data object for the dashboard
export interface DashboardSummary {
  month: string;
  meters: MeterSummary;
  readings: ReadingSummary;
  meters_without_readings: number;
  bills: BillSummary;
  bills_payment_status: BillPaymentStatus;
  earnings: EarningsSummary;
  unpaid_arrears?: UnpaidArrearsSummary; // New section, made optional
}

// The complete API response wrapper
export interface GetDashboardApiResponse {
  message: string;
  data: DashboardSummary;
  status: number;
  timeStamp: string;
}