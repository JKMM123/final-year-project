import { Suspense, lazy, useContext } from "react";
import { Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";
import Layout from "../components/layout/Layout";
import { Spinner } from "react-bootstrap";

// Lazy load pages
const LoginPage = lazy(() => import("../features/auth/LoginPage"));
const UsersPage = lazy(() => import("../features/users/UsersPage"));
const PackagesPage = lazy(() => import("../features/packages/PackagesPage"));
const MetersPage = lazy(() => import("../features/meters/MetersPage"));
const MessagesPage = lazy(() => import("../features/messages/MessagesPage"));
const BillsPage = lazy(() => import("../features/bills/BillsPage"));
const AreasPage = lazy(() => import("../features/areas/AreasPage"));
const ReadingsPage = lazy(() => import("../features/readings/ReadingsPage"));
const DashboardPage = lazy(() => import("../features/dashboard/DashboardPage"));
const CameraPage = lazy(
  () => import("../features/readings/components/CameraPage")
);
const AddReadingPage = lazy(
  () => import("../features/readings/modals/AddReadingPage")
);

const FixesPage = lazy(() => import("../features/fixes/FixesPage"));
const ForgotPasswordPage = lazy(
  () => import("../features/auth/ForgotPasswordPage")
);

const ManagePhoneNumber = lazy(() =>
  import("../features/messages/ManagePhoneNumber/ManagePhoneNumber").then(
    (module) => ({
      default: module.ManagePhoneNumber,
    })
  )
);
const FullPageSpinner = () => (
  <div className="vh-100 d-flex justify-content-center align-items-center">
    <Spinner animation="border" />
  </div>
);

// A simple Forbidden page component
const ForbiddenPage = () => (
  <div className="text-center">
    <h2>403 - Forbidden</h2>
    <p>You do not have permission to access this page.</p>
  </div>
);

// A simple Not Found page component
const NotFoundPage = () => (
  <div className="text-center">
    <h2>404 - Page Not Found</h2>
    <p>The page you are looking for does not exist.</p>
  </div>
);

// Define all application routes in a configuration array
const appRoutesConfig = [
  {
    path: "dashboard",
    component: <DashboardPage />,
    allowedRoles: ["system", "admin"],
  },
  {
    path: "users",
    component: <UsersPage />,
    allowedRoles: ["system", "admin"],
  },
  {
    path: "packages",
    component: <PackagesPage />,
    allowedRoles: ["system", "admin"],
  },
  {
    path: "messages",
    component: <MessagesPage />,
    allowedRoles: ["system", "admin"],
  },
  {
    path: "readings",

    component: <ReadingsPage />,
    allowedRoles: ["system", "admin", "user"],
  },

  {
    path: "areas",
    component: <AreasPage />,
    allowedRoles: ["system", "admin"],
  },
  {
    path: "fixes",
    component: <FixesPage />,
    allowedRoles: ["system", "admin"],
  },
  {
    path: "meters",
    component: <MetersPage />,
    allowedRoles: ["system", "admin", "user"],
  },
  {
    path: "bills",
    component: <BillsPage />,
    allowedRoles: ["system", "admin", "user"],
  },

  {
    path: "manage-phone-number",
    component: <ManagePhoneNumber />,
    allowedRoles: ["system", "admin"],
  },
];

export const AppRoutes = () => {
  const auth = useContext(AuthContext);
  const location = useLocation();
  const state = location.state as { backgroundLocation?: Location } | undefined;

  if (!auth) {
    console.error(
      "AuthContext is undefined. Make sure AuthProvider wraps your App."
    );
    return <div>Error: Missing AuthContext</div>;
  }

  const { user, loading } = auth;

  if (loading) {
    return <FullPageSpinner />; // Or any placeholder
  }

  return (
    <Suspense fallback={<FullPageSpinner />}>
      {/* main routes */}
      <Routes location={state?.backgroundLocation || location}>
        {/* Public Routes */}
        <Route
          path="/login"
          element={user ? <Navigate to="/" /> : <LoginPage />}
        />
        <Route
          path="/reset-password"
          element={user ? <Navigate to="/" /> : <ForgotPasswordPage />}
        />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout>
                <Outlet />
              </Layout>
            </ProtectedRoute>
          }
        >
          {/* default redirect */}
          <Route
            path=""
            element={
              <Navigate
                to={user?.role === "user" ? "meters" : "dashboard"}
                replace
              />
            }
          />

          {/* main pages */}
          {appRoutesConfig.map(({ path, component, allowedRoles }) => {
            const isAllowed = allowedRoles.includes(user?.role ?? "");
            return (
              <Route
                key={path}
                path={path}
                element={isAllowed ? component : <ForbiddenPage />}
              />
            );
          })}

          {/* always defined modal pages */}

          {/* fallback */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>

      {/* modal overlays */}
      {state?.backgroundLocation && (
        <Routes>
          <Route
            path="readings/add-reading/:meter_id"
            element={<AddReadingPage />}
          />
          <Route
            path="readings/take-photo/:meter_id"
            element={<CameraPage />}
          />
        </Routes>
      )}
    </Suspense>
  );
};
