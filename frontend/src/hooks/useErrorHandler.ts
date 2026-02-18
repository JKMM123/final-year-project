import { useContext } from 'react';
import { AlertContext } from '../context/AlertContext';

// This hook provides a more semantic alias for the error handling part of AlertContext
export const useErrorHandler = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useErrorHandler must be used within an AlertProvider');
  }
  return { handle: context.handleError };
};