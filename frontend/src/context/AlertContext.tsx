// AlertContext.tsx

import { createContext, useMemo } from "react";
import type { ReactNode } from "react";
import toast from "react-hot-toast";
import { AxiosError } from "axios";

// ... (interfaces remain the same)

interface AlertContextType {
  success: (message: string) => void;
  error: (message: string) => void;
  // Change the return type from void to string
  handleError: (error: unknown) => string;
}

export const AlertContext = createContext<AlertContextType | undefined>(
  undefined
);

export const AlertProvider = ({ children }: { children: ReactNode }) => {
  const alertContextValue = useMemo(
    () => ({
      success: (message: string) => toast.success(message),
      error: (message: string) => toast.error(message),
      // Modify this function
      handleError: (error: unknown): string => {
        // Add return type annotation
        let errorMessage = "An unexpected error occurred.";

        if (typeof error === "string") {
          errorMessage = error;
        } else if (error instanceof AxiosError) {
          const fieldErrors = error.response?.data?.fieldErrors;
          if (Array.isArray(fieldErrors) && fieldErrors.length > 0) {
            const firstError = fieldErrors[0];
            errorMessage = `${firstError.field || "Field"} ${
              firstError.message || "is invalid"
            }`;
          } else {
            errorMessage = error.response?.data?.message || error.message;
          }
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        if (
          errorMessage !== "Invalid token or token has expired." &&
          errorMessage !== "Invalid refresh token cookies" &&
          errorMessage !== "Invalid refresh token."
        ) {
          toast.error(errorMessage);
        }

        // Return the processed message
        return errorMessage;
      },
    }),
    []
  );

  return (
    <AlertContext.Provider value={alertContextValue}>
      {children}
    </AlertContext.Provider>
  );
};
