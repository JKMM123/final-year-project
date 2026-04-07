// src/pages/Messages/ManagePhoneNumber/types.ts

// The generic API response wrapper you already have
export interface ApiResponse<T> {
  message: string;
  data: T;
  status: number;
  timeStamp: string;
  error?: string; // Add for error responses
}

// Payload for creating a new session
export interface CreateSessionPayload {
  name: string;
  phone_number: string;
}

// Data returned by create/connect session APIs
export interface SessionCreationData {
  success: boolean;
  data: {
    status: "NEED_SCAN";
    qrCode: string;
  };
}

// Possible statuses for a session
export type SessionStatus = "connected" | "logged_out" | "need_scan" | "connecting";

// Data returned by the get status API
export interface SessionStatusData {
  status: SessionStatus;
}

// Data received from the SSE webhook
export interface WebhookEventData {
  event: "session.status";
  status: SessionStatus;
}