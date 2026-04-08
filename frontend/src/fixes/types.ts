// src/features/fixes/types.ts

import type { Pagination } from "../../hooks/usePaginatedFetch";

// The main Fix object returned from the API
export interface Fix {
  fix_id: string;
  meter_id: string;
  customer_name: string;
  description: string;
  fix_date: string; // "YYYY-MM-DD"
  cost: number;
}

// Payload for searching/fetching fixes
export interface FixSearchPayload {
  page: number;
  limit: number;
  query?: string;
  fix_date?: string; // "YYYY-MM-01"
}

// Payload for creating a new fix
export interface FixCreatePayload {
  meter_id: string;
  fix_date: string; // "YYYY-MM-DD"
  description: string;
  cost: number;
}

// Payload for updating an existing fix
export interface FixUpdatePayload {
  fix_date: string;
  description: string;
  cost: number;
}

// The structure of the API response for getting fixes
export interface GetFixesApiResponse {
  message: string;
  data: {
    fixes: Fix[];
    pagination: Pagination;
  };
  status: number;
  timeStamp: string;
}

// --- Meter related types for the search dropdown ---

export interface Meter {
  meter_id: string;
  customer_full_name: string; 
  customer_phone_number?: string;
  area_name?: string;
}

// Payload for searching meters (copied from your request)
export interface MeterSearchPayload {
  page: number;
  limit: number;
  query?: string;
  package_type?: string;
  package_ids?: string[];
  area_ids?: string[];
  status?: string[];
  reading_date?: string;
}

// API response for getting meters
export interface GetMetersApiResponse {
  message: string;
  data: {
    meters: Meter[];
    pagination: Pagination;
  };
  status: number;
  timeStamp: string;
}