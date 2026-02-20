// src/contexts/TaskContext.tsx

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import type { ReactNode } from "react";
import { getTaskStatus } from "../features/bills/billsService";
import type { TaskStatusData } from "../features/bills/types";
import { getTaskId, saveTaskId, clearTaskId } from "../utils/taskStorage";
import { useAlert } from "../hooks/useAlert"; // Assuming useAlert is globally accessible

interface TaskContextType {
  taskId: string | null;
  taskStatus: TaskStatusData | null;
  isLoading: boolean;
  startTask: (newTaskId: string) => void;
  clearTask: () => void;
  checkTaskStatus: (id: string) => Promise<void>;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

export const useTask = () => {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error("useTask must be used within a TaskProvider");
  }
  return context;
};

export const TaskProvider = ({ children }: { children: ReactNode }) => {
  const [taskId, setTaskId] = useState<string | null>(getTaskId());
  const [taskStatus, setTaskStatus] = useState<TaskStatusData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { success: showSuccessToast, error: showErrorToast } = useAlert();

  const clearTask = useCallback(() => {
    clearTaskId();
    setTaskId(null);
    setTaskStatus(null);
  }, []);

  const checkTaskStatus = useCallback(
    async (id: string) => {
      setIsLoading(true);
      try {
        const raw = await getTaskStatus(id);

        // Normalize different possible shapes:
        // - raw could be { message, data: { task_id, status, result }, status } (your example)
        // - or raw could already be the data object { task_id, status, result }
        const normalized =
          (raw && (raw as any).data && (raw as any).data.data) ??
          (raw && (raw as any).data) ??
          raw;

        // At this point normalized should be { task_id, status, result }
        setTaskStatus(normalized);

        const status = (normalized as any)?.status;

        if (status === "SUCCESS") {
          // full success
          showSuccessToast?.("Your bills PDF is ready for download!");
        } else if (status === "FAILURE") {
          // server tells us the task failed — clear to allow restart
          showErrorToast?.("Failed to generate bills. Please try again.");
          clearTask();
        } else if (status === "RETRY") {
          // YOUR REQUEST: stop polling and surface an error
          showErrorToast?.(
            "Something went wrong during generation. Please try again or contact support."
          );
          // clear stored task and state — this will also cause the polling effect to clean up
          clearTask();
        }
        // For other states like "PENDING" do nothing; polling will continue.
      } catch (error) {
        // Network or unexpected error -> clear and surface message
        console.error("Failed to check task status:", error);
        showErrorToast?.("Unable to check task status. Please try again.");
        clearTask();
      } finally {
        setIsLoading(false);
      }
    },
    [clearTask, showSuccessToast, showErrorToast]
  );

  // Polling effect — do not poll if success or retry (retry should stop polling)
  useEffect(() => {
    if (
      taskId &&
      taskStatus?.status !== "SUCCESS" &&
      taskStatus?.status !== "RETRY"
    ) {
      const interval = setInterval(() => {
        checkTaskStatus(taskId);
      }, 15000); // Poll every 15 seconds

      return () => clearInterval(interval);
    }
    // If taskStatus is SUCCESS or RETRY, effect will not create (or will cleanup) the interval.
  }, [taskId, taskStatus, checkTaskStatus]);

  // Initial check when the app loads
  useEffect(() => {
    const existingTaskId = getTaskId();
    if (existingTaskId) {
      setTaskId(existingTaskId);
      checkTaskStatus(existingTaskId);
    }
  }, [checkTaskStatus]);

  const startTask = (newTaskId: string) => {
    saveTaskId(newTaskId);
    setTaskId(newTaskId);
    setTaskStatus({ task_id: newTaskId, status: "PENDING", result: null }); // Set initial status
  };

  const value = {
    taskId,
    taskStatus,
    isLoading,
    startTask,
    clearTask,
    checkTaskStatus,
  };

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
};
