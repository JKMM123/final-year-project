import type { Pagination } from '../../hooks/usePaginatedFetch';

// Matches the area object from your API response
export interface Area {
  area_id: string;
  area_name: string;
  elevation: number;
}

// Payload for creating or updating an area
export type AreaPayload = Omit<Area, 'area_id'>;

// The nested structure of your GET /areas/search API response
export interface GetAreasApiResponse {
  data: {
    areas: Area[];
    pagination: Pagination;
  };
}