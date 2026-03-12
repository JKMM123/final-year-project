import axiosInstance from '../../services/axiosInstance';
import type { GetUsersApiResponse, User, UserPayload } from './types';
import type { Pagination } from '../../hooks/usePaginatedFetch';

interface GetUsersParams {
  page: number;
  limit: number;
  query?: string;
  role?: string;
}

// GET all users with filtering, search, and pagination
export const getUsers = async (params: GetUsersParams): Promise<{ items: User[], pagination: Pagination }> => {
  const { page, limit, query, role } = params;
  
  // Construct URL parameters, ignoring empty values
  const urlParams = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });
  if (query) urlParams.append('query', query);
  if (role) urlParams.append('role', role);

  const response = await axiosInstance.get<GetUsersApiResponse>(`/users/search?${urlParams.toString()}`);
  
  // Unwrap the nested response to return a cleaner object
  return {
    items: response.data.data.users,
    pagination: response.data.data.pagination
  };
};

// CREATE a new user
export const createUser = async (payload: UserPayload): Promise<User> => {
  const response = await axiosInstance.post<User>('/users/create', payload);
  return response.data;
};

// UPDATE an existing user
export const updateUser = async (userId: string, payload: UserPayload): Promise<User> => {
  const response = await axiosInstance.put<User>(`/users/${userId}`, payload);
  return response.data;
};

// DELETE a user
export const deleteUser = async (userId: string): Promise<void> => {
  await axiosInstance.delete(`/users/${userId}`);
};