// src/pages/Messages/types.ts

import type { Pagination } from "../../hooks/usePaginatedFetch";

export interface Template {
  template_id: string;
  name: string;
  message: string;
}

export interface TemplateSearchPayload {
  page: number;
  limit: number;
  query?: string;
}

export interface CreateTemplatePayload {
  name: string;
  message: string;
}

export type UpdateTemplatePayload = Partial<CreateTemplatePayload>;

// For the API response structure
export interface GetTemplatesApiResponse {
  data: {
    templates: Template[];
    pagination: Pagination;
  };
}

// Type for react-select options
export interface SelectOption<T = string> {
  value: T;
  label: string;
}

// Interfaces for service functions
export interface Package {
  package_id: string;
  amperage: number;
  package_type: "usage" | "fixed";
}

export interface GetPackagesParams {
  page: number;
  limit: number;
  amperage?: string;
}

export interface Area {
  area_id: string;
  area_name: string;
}

export interface GetAreasParams {
  page: number;
  limit: number;
  query?: string;
}

export interface Meter {
  meter_id: string;
  customer_full_name: string;
  // ... other meter properties if needed
}

export interface MeterSearchPayload {
  page: number;
  limit: number;
  query?: string;
}


// Payload for the Send Message API
export interface MeterFilters {
  area_ids?: string[];
  package_ids?: string[];
  meter_status?: "active" | "inactive";
  package_type?: "usage" | "fixed";
}

export interface BillFilters {
  payment_status?: "paid" | "unpaid";
  due_date?: string | null; // YYYY-MM-DD
  payment_method?: ("cash" | "omt" | "wish")[];
  overdue_only?: boolean;
}

export interface SendMessagePayload {
  template_id?: string;
  message?: string;
  broadcast?: boolean;
  customer_ids?: string[];
  meter_filters?: MeterFilters;
  bill_filters?: BillFilters;
  scheduled_at?: string; // ISO 8601 format
  send_immediately?: boolean;
}