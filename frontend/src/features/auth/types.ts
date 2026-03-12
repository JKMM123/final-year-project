export interface User {
  user_id: string;
  username: string;
  phone_number: string;
  role: 'system' | 'admin' | 'user';
}

export interface LoginResponse {
  data: User;
}
// No longer need AuthResponse as tokens are in cookies

export interface LoginCredentials {
  username_or_phone: string;
  password?: string;
}

export interface LoginPayload extends LoginCredentials {
  device_id: string;
}

export interface VerifyOtpResponseData {
  reset_token: string;
  expires_at: string;
}

export interface VerifyOtpResponse {
    data: VerifyOtpResponseData;
}

export interface VerifyOtpPayload {
  phone_number: string;
  otp: string;
}

export interface ResetPasswordPayload {
  phone_number: string;
  reset_token: string;
  new_password: string;
}