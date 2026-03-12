import axiosInstance from '../../services/axiosInstance';
import type { User, LoginPayload,LoginResponse, VerifyOtpPayload, VerifyOtpResponse, ResetPasswordPayload } from './types';

// Login now returns the User object directly
export const login = async (credentials: LoginPayload): Promise<User> => {
  const response = await axiosInstance.post<LoginResponse>('/auth/login', credentials);
  return response.data.data; // ✅ extract the actual User from the `data` field
};

// Logout is a simple POST request with no payload
export const logout = async (): Promise<void> => {
  await axiosInstance.post('/auth/logout');
};

// Refresh is a simple GET request
export const refreshToken = async (): Promise<void> => {
  // Use a different baseURL for refresh if it's on a different port like in your cURL
  // This is an example, adjust if your setup is different
 
  await axiosInstance.get('/auth/refresh');
};

/**
 * Sends an OTP to the provided phone number.
 */
export const sendOtp = async (phoneNumber: string): Promise<void> => {
  await axiosInstance.post(`/auth/send-otp?phone_number=${phoneNumber}`);
};

/**
 * Verifies the OTP and returns a reset token on success.
 */
export const verifyOtp = async (
  payload: VerifyOtpPayload
): Promise<VerifyOtpResponse> => {
  const response = await axiosInstance.post<VerifyOtpResponse>(
    "/auth/verify-otp",
    payload
  );
  return response.data;
};

/**
 * Resets the user's password using the reset token.
 */
export const resetPassword = async (
  payload: ResetPasswordPayload
): Promise<void> => {
  await axiosInstance.post("/auth/reset-password", payload);
};