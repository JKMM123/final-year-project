import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Toaster } from "react-hot-toast";
import { AppRoutes } from "./routes/AppRoutes";
import { TaskProvider } from "./context/TaskContext";

// Helper function to dynamically load Bootstrap CSS
const loadBootstrap = (dir: "ltr" | "rtl") => {
  const existingLink = document.getElementById("bootstrap-css");
  if (existingLink) {
    // No need to remove and re-add if the href is already correct
    const expectedHref =
      dir === "rtl"
        ? "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css"
        : "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css";
    if (existingLink.getAttribute("href") === expectedHref) {
      return;
    }
    existingLink.remove();
  }

  const link = document.createElement("link");
  link.id = "bootstrap-css";
  link.rel = "stylesheet";
  if (dir === "rtl") {
    link.href =
      "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css";
    link.integrity =
      "sha384-nU14brUcp6StFntEOOEBvcJm4huWjB0OcIeQ3flBFcfYI4ma8GM6LCA30GASuA8g";
  } else {
    link.href =
      "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css";
    link.integrity =
      "sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN";
  }
  link.crossOrigin = "anonymous";
  document.head.appendChild(link);
};

function App() {
  // NEW: Get the i18n instance to listen for language changes
  const { i18n } = useTranslation();

  // NEW: This effect manages the global document direction and styles
  useEffect(() => {
    const dir = i18n.language === "ar" ? "rtl" : "ltr";
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
    loadBootstrap(dir);
  }, [i18n.language]);

  return (
    <>
      <TaskProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            className: "",
            style: {
              border: "1px solid #713200",
              padding: "16px",
              color: "#713200",
            },
          }}
        />
      </TaskProvider>
    </>
  );
}

export default App;
