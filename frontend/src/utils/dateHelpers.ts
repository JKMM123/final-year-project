/**
 * Gets the default month for readings reports.
 * - If the current date is after the 15th of the month, it returns the current month.
 * - Otherwise, it returns the previous month.
 * @returns {string} The date in YYYY-MM format.
 */
export const getDefaultMonth = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth(); // 0-indexed (0 for January)
  const day = now.getDate();

  if (day > 15) {
    // Return current month in YYYY-MM format
    return `${year}-${String(month + 1).padStart(2, "0")}`;
  } else {
    // Go back one month
    const previousMonthDate = new Date(year, month - 1, 1);
    const prevYear = previousMonthDate.getFullYear();
    const prevMonth = previousMonthDate.getMonth() + 1;
    return `${prevYear}-${String(prevMonth).padStart(2, "0")}`;
  }
};