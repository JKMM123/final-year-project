// src/utils/taskStorage.ts

const TASK_ID_KEY = "billsDownloadTaskId";
const TASK_EXPIRY_MS = 2.5 * 60 * 60 * 1000; // 2.5 hours in milliseconds

interface StoredTask {
  id: string;
  expiry: number; // Timestamp when the task ID should expire
}

/**
 * Saves the task ID and its expiry timestamp to local storage.
 * @param taskId The task ID received from the API.
 */
export const saveTaskId = (taskId: string): void => {
  const expiry = Date.now() + TASK_EXPIRY_MS;
  const storedTask: StoredTask = { id: taskId, expiry };
  localStorage.setItem(TASK_ID_KEY, JSON.stringify(storedTask));
};

/**
 * Retrieves the task ID from local storage, only if it has not expired.
 * If the task has expired, it's cleared from storage.
 * @returns The task ID string or null if not found or expired.
 */
export const getTaskId = (): string | null => {
  const storedTaskString = localStorage.getItem(TASK_ID_KEY);
  if (!storedTaskString) {
    return null;
  }

  try {
    const storedTask: StoredTask = JSON.parse(storedTaskString);
    if (Date.now() > storedTask.expiry) {
      console.log("Task ID has expired. Clearing from storage.");
      clearTaskId();
      return null;
    }
    return storedTask.id;
  } catch (error) {
    console.error("Failed to parse task ID from local storage.", error);
    clearTaskId();
    return null;
  }
};

/**
 * Removes the task ID from local storage.
 */
export const clearTaskId = (): void => {
  localStorage.removeItem(TASK_ID_KEY);
};