import React from "react";
import ReactDOM from "react-dom/client";
import "./i18n/i18n"; // Import i18n configuration

import "bootstrap/dist/css/bootstrap.min.css";
import App from "./App";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { AlertProvider } from "./context/AlertContext";

// Import Bootstrap and custom styles
import "./index.css";
// import "bootstrap/dist/css/bootstrap.min.css";
// import "bootstrap-icons/font/bootstrap-icons.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AlertProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </AlertProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
