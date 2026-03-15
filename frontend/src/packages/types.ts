import type{ Pagination } from '../../hooks/usePaginatedFetch';

// Matches the package object from your API response
export interface Package {
  package_id: string;
  amperage: number ;
  activation_fee: number ;
  fixed_fee: number ;
  meters_count: number;
}

// Used only inside forms (Formik state)
export interface PackageFormValues {
  amperage: number | string;
  activation_fee: number | string;
  fixed_fee: number | string;
}


// Payload for creating or updating a package
export type PackagePayload = Omit<Package, 'package_id' | 'meters_count'>;

// The nested structure of your GET /packages/search API response
export interface GetPackagesApiResponse {
  data: {
    packages: Package[];
    pagination: Pagination;
  };
}

export interface GetPackagesParams {
  page: number;
  limit: number;
  amperage?: number | string;
}

/**
 * Represents the rate details for a specific month.
 * This corresponds to an object in the 'data' array from the /rates/all/{year} API response.
 */
export interface MonthlyRate {
  rate_id: string;
  mountain_kwh_rate: number;
  coastal_kwh_rate: number;
  dollar_rate: number;
  rate_month: string; // e.g., "October"
}

/**
 * Represents the structure of the successful API response for fetching rates by year.
 */
export interface RatesByYearResponse {
  message: string;
  data: MonthlyRate[];
  status: number;
  timeStamp: string;
}