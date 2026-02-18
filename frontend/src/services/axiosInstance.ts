import axios from 'axios';
import type {AxiosInstance, AxiosError, InternalAxiosRequestConfig} from "axios";
import * as authService from '../features/auth/loginService'; // Make sure this path is correct

export const BASE_URL = "http://localhost:8080/billing-system/api/v1" ;
//"https://api-billing-system.skylinelb.com/billing-system/api/v1";
//"http://192.168.1.6:8080/billing-system/api/v1" ;


const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // ✅ sends HttpOnly cookies
});


// --- NEW: Refresh Logic State ---
let isRefreshing = false;
let failedQueue: { resolve: (value?: any) => void; reject: (reason?: any) => void; }[] = [];

const processQueue = (error: Error | null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });

  failedQueue = [];
};

// --- Updated Response Interceptor ---
instance.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // --- Handle Timeout Errors ---
    if (error.code === "ECONNABORTED") {
      return Promise.reject({
        message: "Request timed out. Please try again later.",
        code: error.code,
        originalError: error, // keep original if you want debugging
      });
    }

        // --- Handle Network Errors ---
    if (!error.response) {
      return Promise.reject({
        message: "Network error. Please check your internet connection.",
        code: "NETWORK_ERROR",
        originalError: error,
      });
    }

    // If the error is not a 401, or if it's a 401 on the refresh token endpoint,
    // or if the request has already been retried, just reject it.
    if (error.response?.status !== 401 || originalRequest.url?.includes('/auth/refresh') || originalRequest._retry) {
       // Handle 403 Forbidden specifically
       if (error.response?.status === 403) {
         window.dispatchEvent(
           new CustomEvent("authError", { detail: { reason: "unauthorized" } })
         );
       }
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // If a refresh is already in progress, queue this request
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then(() => instance(originalRequest))
        .catch(err => Promise.reject(err));
    }

    // This is the first 401. Start the refresh process.
    isRefreshing = true;
    originalRequest._retry = true;

    try {
      console.log("Attempting to refresh token...");
      await authService.refreshToken(); // This should handle updating cookies/tokens
      console.log("Token refreshed successfully.");
      
      // Process the queue with success
      processQueue(null);

      // Retry the original request
      return instance(originalRequest);

    } catch (refreshError) {
      console.error("Failed to refresh token:", refreshError);

      // Process the queue with an error
      processQueue(refreshError as Error);

      // Dispatch event to trigger global logout
      window.dispatchEvent(
        new CustomEvent("authError", { detail: { reason: "sessionExpired" } })
      );

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default instance;