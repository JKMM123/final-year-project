import { useState, useEffect, useCallback } from 'react';
import { useErrorHandler } from './useErrorHandler';

export interface Pagination {
  current_page: number;
  per_page: number;
  total_pages: number;
  total_items: number;
  has_next: boolean;
  has_previous: boolean;
}

interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

type FetchFunction<T> = (page: number, limit: number) => Promise<PaginatedResponse<T>>;

export const usePaginatedFetch = <T>(fetchFunction: FetchFunction<T>, limit = 10) => {
  const [data, setData] = useState<T[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const errorHandler = useErrorHandler();

  const fetchData = useCallback(
    async (page: number) => {
      setIsLoading(true);
      try {
        const response = await fetchFunction(page, limit);
        setData(response.items);
        setPagination(response.pagination);
      } catch (error) {
        errorHandler.handle(error);
        setData([]); // Clear data on error
        setPagination(null);
      } finally {
        setIsLoading(false);
      }
    },
    [fetchFunction, limit, errorHandler]
  );

  useEffect(() => {
    fetchData(currentPage);
  }, [currentPage, fetchData]);

  const goToPage = (page: number) => {
    setCurrentPage(page);
  };
  
  const refresh = () => {
    fetchData(currentPage);
  }

  return { data, pagination, isLoading, goToPage, refresh };
};