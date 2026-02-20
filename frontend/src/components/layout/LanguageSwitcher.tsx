import { useTranslation } from "react-i18next";

const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  const currentLanguage = i18n.language;

  return (
    <div className="dropdown">
      <button
        className="btn btn-secondary dropdown-toggle"
        type="button"
        id="languageDropdown"
        data-bs-toggle="dropdown"
        aria-expanded="false"
      >
        {t("common.language")}:{" "}
        {currentLanguage === "en" ? t("common.english") : t("common.arabic")}
      </button>
      <ul className="dropdown-menu" aria-labelledby="languageDropdown">
        <li>
          <button
            className={`dropdown-item ${
              currentLanguage === "en" ? "active" : ""
            }`}
            onClick={() => handleLanguageChange("en")}
          >
            {t("common.english")}
          </button>
        </li>
        <li>
          <button
            className={`dropdown-item ${
              currentLanguage === "ar" ? "active" : ""
            }`}
            onClick={() => handleLanguageChange("ar")}
          >
            {t("common.arabic")}
          </button>
        </li>
      </ul>
    </div>
  );
};

export default LanguageSwitcher;
