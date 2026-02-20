import {
  createContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  useContext,
} from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import type { User, LoginCredentials } from "../features/auth/types";
import * as authService from "../features/auth/loginService";
import { getDeviceId } from "../utils/uuid";
// import SessionExpiredModal from "../components/common/SessionExpiredModal";
import { UnauthorizedModal } from "../components/common/UnauthorizedModal";
//import { useAlert } from "../hooks/useAlert";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: (isSessionExpired?: boolean) => void; // ✅ fix here
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // NEW
  // const [showSessionExpiredModal, setShowSessionExpiredModal] = useState(false);
  const [showUnauthorizedModal, setShowUnauthorizedModal] = useState(false);
  const navigate = useNavigate();
  //  const { handleError } = useAlert();

  // --- Login and Logout ---
  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const device_id = getDeviceId();
      const userData = await authService.login({ ...credentials, device_id }); // no `.data`
      localStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);
      navigate("/");
    },
    [navigate]
  );

  const logout = useCallback(
    async (isSessionExpired = false) => {
      // 1) Grab and clear local user immediately
      const hadUser = !!localStorage.getItem("user");
      if (!hadUser) return;

      localStorage.removeItem("user");
      setUser(null);

      // 2) If this is a genuine, manual logout → call the API
      if (!isSessionExpired) {
        try {
          await authService.logout();
        } catch (err) {
          console.error("Logout API failed, but proceeding anyway", err);
        }
        // After a normal logout, just navigate away
        navigate("/login", { replace: true });
        return;
      }

      // 3) If the session expired → skip the API call, show modal then navigate
      // setShowSessionExpiredModal(true);
      // (you could also navigate immediately, or do it in the modal’s onConfirm)
      navigate("/login", { replace: true });
    },
    [navigate]
  );

  // --- Global Event Listeners for Modals ---
  useEffect(() => {
    const handleAuthError = (event: CustomEvent) => {
      const { reason } = event.detail;
      if (reason === "sessionExpired") {
        // → kicks off our “expired” path in logout()
        logout(true);
      } else if (reason === "unauthorized") {
        setShowUnauthorizedModal(true);
      }
    };

    window.addEventListener("authError", handleAuthError as EventListener);
    return () =>
      window.removeEventListener("authError", handleAuthError as EventListener);
  }, [logout]);

  // --- Initial Load ---
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false); // Set loading to false after checking localStorage
  }, []);

  // --- Memoized Context Value ---
  const authContextValue = useMemo(
    () => ({ user, isAuthenticated: !!user, login, logout, loading }),
    [user, login, logout, loading]
  );

  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
      {/* <SessionExpiredModal
        show={showSessionExpiredModal}
        onConfirm={() => {
          setShowSessionExpiredModal(false);
          navigate("/login", { replace: true });
        }}
        timeout={5000}
      /> */}
      <UnauthorizedModal
        show={showUnauthorizedModal}
        onConfirm={() => setShowUnauthorizedModal(false)}
      />
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
