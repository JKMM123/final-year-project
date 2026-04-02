// src/pages/Messages/ManagePhoneNumber/whatsAppService.ts

import axiosInstance from "../../../services/axiosInstance"; // Assuming you have this
import type {
  ApiResponse,
  CreateSessionPayload,
  SessionCreationData,
  SessionStatusData,
} from "./types";
import { BASE_URL } from "../../../services/axiosInstance";
 // Or from env

/**
 * The URL for the Server-Sent Events (SSE) webhook.
 * We export this to be used with the EventSource API in the component.
 */
export const WEBHOOK_URL = `${BASE_URL}/session/webhook/events`;

/**
 * Retrieves the current status of the WhatsApp session.
 * @returns The session status data.
 */
export const getSessionStatus = async (): Promise<SessionStatusData> => {
  const response = await axiosInstance.get<ApiResponse<SessionStatusData>>(
    "/session/status"
  );
  return response.data.data;
};

/**
 * Creates a new WhatsApp session.
 * @param payload - The user's name and phone number.
 * @returns The QR code and initial status.
 */
export const createSession = async (
  payload: CreateSessionPayload
): Promise<SessionCreationData> => {
  const response = await axiosInstance.post<ApiResponse<SessionCreationData>>(
    "/session/create",
    payload
  );
  return response.data.data;
};

/**
 * Connects to an existing session, typically to generate a new QR code.
 * @returns A new QR code and status.
 */
export const connectSession = async (): Promise<SessionCreationData> => {
  const response = await axiosInstance.get<ApiResponse<SessionCreationData>>(
    "/session/connect"
  );
  return response.data.data;
};

/**
 * Deletes/disconnects the current WhatsApp session.
 */
export const deleteSession = async (): Promise<void> => {
  await axiosInstance.delete<ApiResponse<[]>>("/session/delete");
};