import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// Import translation files
import en from "./locales/en.json";
import ar from "./locales/ar.json";

const resources = {
  en: {
    translation: en,
  },
  ar: {
    translation: ar,
  },
};

i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next.
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources,
    fallbackLng: "en", // Fallback language if detection fails
    interpolation: {
      escapeValue: false, // React already safes from xss
    },
    detection: {
      // Order and from where user language should be detected
      order: ["localStorage", "cookie", "htmlTag", "navigator"],
      // Keys or params to lookup language from
      lookupLocalStorage: 'i18nextLng',
      // Cache user language on
      caches: ["localStorage"],
    },
  });

export default i18n;