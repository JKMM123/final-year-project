// // Example formatter
// export const formatDate = (dateString: string) => {
//   return new Date(dateString).toLocaleDateString('en-US', {
//     year: 'numeric',
//     month: 'long',
//     day: 'numeric',
//   });
// };

// src/utils/formatters.ts

/**
 * Utility functions for formatting numbers and currencies
 * in a consistent, locale-aware way.
 *
 * These helpers are fully typed and can be reused across the app.
 */

/**
 * Formats a numeric value with thousands separators.
 *
 * @param value - The number to format (can be number or string)
 * @param decimals - Number of digits after the decimal point
 * @param locale - Optional locale, defaults to user's browser setting
 * @returns Formatted number as a string (e.g. "1,234.56")
 */
export const formatNumber = (
  value: number | string | undefined | null,
  decimals: number = 2,
  locale: string = navigator.language
): string => {
  if (value === undefined || value === null || value === "") return "-";
  const num = Number(value);
  if (isNaN(num)) return "-";

  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

/**
 * Formats a number as a currency string.
 *
 * @param amount - The number to format
 * @param currency - The ISO 4217 currency code (e.g., "USD", "LBP", "EUR")
 * @param locale - Optional locale for formatting
 * @param showSymbol - Whether to include the currency symbol
 * @returns Formatted currency string (e.g. "$1,234.00" or "1,234 USD")
 */
export const formatCurrency = (
  amount: number | string | undefined | null,
  currency: string = "USD",
  locale: string = navigator.language,
  showSymbol: boolean = true
): string => {
  if (amount === undefined || amount === null || amount === "") return "-";
  const num = Number(amount);
  if (isNaN(num)) return "-";

  try {
    const formatter = new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      currencyDisplay: showSymbol ? "symbol" : "code",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return formatter.format(num);
  } catch (err) {
    // fallback for non-standard currency codes like "LBP"
    const formatted = formatNumber(num, 2, locale);
    return showSymbol ? `${formatted} ${currency}` : formatted;
  }
};

/**
 * Formats a date into a readable string (e.g., "2025-10-11" → "Oct 11, 2025")
 *
 * @param date - A Date object, string, or timestamp
 * @param locale - Optional locale
 * @returns Formatted date string or "-" if invalid
 */
export const formatDate = (
  date: Date | string | number | null | undefined,
  locale: string = navigator.language
): string => {
  if (!date) return "-";
  const parsed = new Date(date);
  if (isNaN(parsed.getTime())) return "-";

  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(parsed);
};

/**
 * Converts a boolean to a "Yes"/"No" (or localized) string.
 */
export const formatBoolean = (
  value: boolean | null | undefined,
  yesText = "Yes",
  noText = "No"
): string => {
  if (value === undefined || value === null) return "-";
  return value ? yesText : noText;
};
