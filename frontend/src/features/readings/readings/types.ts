// types.ts

import type { Pagination } from '../../hooks/usePaginatedFetch';
import type { Meter } from '../meters/types'; // Re-use existing Meter type

// The Meter object as it appears in the 'awaiting_reading' search
export interface MeterForReading extends Meter {
    area_name: string;
    has_reading: boolean;
    // This is the last known reading for validation purposes.
    // Mapped from `initial_reading` from the backend.
    previous_reading?: number;
}

// The Reading object from the /readings/search endpoint
export interface Reading {
    reading_id: string;
    meter_id: string;
    customer_full_name: string;
    customer_phone_number: string;
    reading_date: string;
    current_reading: number; // The newly recorded reading value
    previous_reading: number; // The reading value before this one
    usage: number;
    status: 'pending' | 'verified';
    area_name?: string;
    reading_url?: string;
}

// The summary object from the /readings/summary endpoint
export interface ReadingsSummary {
    total_active_meters: number;
    meters_with_readings: number;
    meters_needing_readings: number;
    verified_readings_count: number;
    pending_readings_count: number;
}

// Describes the 'data' object in the initial scan response
export interface ScanData {
  current_reading: number;
  image_url?: string;
}

// Describes the full API response from the initial scan
export interface ScanApiResponse {
  message: string;
  data: ScanData;
  status: number;
  timeStamp: string;
}

// API Response Wrappers
export interface GetMetersForReadingApiResponse {
  data: { meters: MeterForReading[], pagination: Pagination };
}
export interface GetReadingsApiResponse {
  data: { readings: Reading[], pagination: Pagination };
}
export interface GetSummaryApiResponse {
  data: ReadingsSummary;
}

export interface GetReadingDetailsApiResponse {
    message: string;
    data: Reading; // This contains the full reading object
    status: number;
    timeStamp: string;
}


export interface VerifyAllReadingsPayload {
  confirm: boolean;
  reading_date: string;
}

interface VerifiedCountInfo {
  message: string;
  verified_count: number;
  reading_date: string;
  date_range?: {
    start_date: string;
    end_date: string;
  };
}

export interface VerifyAllApiResponse {
  message: string;
  data: {
    verified_count: VerifiedCountInfo;
  };
  status: number;
}