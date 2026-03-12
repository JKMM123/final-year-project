import type { Pagination } from '../../hooks/usePaginatedFetch';

// Matches the user object from your API response
export interface User {
  user_id: string;
  username: string;
  phone_number: string;
  role: 'user' | 'admin';
}

// Payload for creating or updating a user
export type UserPayload = Omit<User, 'user_id'>;

// Matches the nested structure of your GET /users/search API response
export interface GetUsersApiResponse {
  message: string;
  data: {
    users: User[];
    pagination: Pagination;
  };
  status: number;
  timeStamp: string;
}