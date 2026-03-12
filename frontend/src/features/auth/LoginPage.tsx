import { lazy, useState } from "react";
import { Formik, Form as FormikForm } from "formik";
import * as Yup from "yup";
import { Link, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, AlertCircle } from "lucide-react"; // Icons

// Context & Hooks
import { useAuth } from "../../context/AuthContext";
import { useAlert } from "../../hooks/useAlert";
import type { LoginCredentials } from "./types";

// Shadcn Components
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Alert, AlertDescription } from "../../components/ui/alert";

// Lazy Load Modal
const ForgotPasswordModal = lazy(() => import("./ForgotPasswordModal"));

const LoginPage = () => {
  const { t } = useTranslation();
  const auth = useAuth();
  const { handleError } = useAlert();

  const [validationError, setValidationError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  // Validation Schema
  const LoginSchema = Yup.object().shape({
    username_or_phone: Yup.string().required(
      t("loginPage.validation.usernameRequired"),
    ),
    password: Yup.string().required(t("loginPage.validation.passwordRequired")),
  });

  if (auth.isAuthenticated) {
    return <Navigate to="/" />;
  }

  const handleLogin = async (
    values: LoginCredentials,
    { setSubmitting }: any,
  ) => {
    try {
      await auth.login(values);
    } catch (err) {
      const message = handleError(err);
      setValidationError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {/* Container: Centered Layout (replaces Container, Row, Col) */}
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="w-full max-w-md">
          <Card className="shadow-lg border-0">
            <CardHeader className="space-y-1 pb-2">
              <CardTitle className="text-2xl font-bold text-center">
                {t("loginPage.title")}
              </CardTitle>
            </CardHeader>

            <CardContent className="p-6 md:p-8">
              {validationError && (
                <Alert
                  variant="destructive"
                  className="mb-4 bg-red-50 text-red-600 border-red-200"
                >
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{validationError}</AlertDescription>
                </Alert>
              )}

              <Formik
                initialValues={{ username_or_phone: "", password: "" }}
                validationSchema={LoginSchema}
                onSubmit={handleLogin}
              >
                {({
                  handleChange,
                  handleBlur,
                  handleSubmit,
                  values,
                  errors,
                  touched,
                  isSubmitting,
                }) => (
                  <FormikForm
                    onSubmit={handleSubmit}
                    autoComplete="on"
                    className="space-y-4"
                  >
                    {/* Username Field */}
                    <div className="space-y-2">
                      <Label htmlFor="username_or_phone">
                        {t("loginPage.usernameLabel")}
                      </Label>
                      <Input
                        id="username_or_phone"
                        type="text"
                        name="username_or_phone"
                        autoComplete="username"
                        value={values.username_or_phone}
                        onChange={handleChange}
                        onBlur={handleBlur}
                        // Apply red border on error to match Bootstrap "isInvalid"
                        className={
                          touched.username_or_phone && errors.username_or_phone
                            ? "border-red-500 focus-visible:ring-red-500"
                            : ""
                        }
                      />
                      {touched.username_or_phone &&
                        errors.username_or_phone && (
                          <p className="text-sm text-red-500 font-medium mt-1">
                            {errors.username_or_phone}
                          </p>
                        )}
                    </div>

                    {/* Password Field */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="password">
                          {t("loginPage.passwordLabel")}
                        </Label>
                      </div>

                      <div className="relative">
                        <Input
                          id="password"
                          type={showPassword ? "text" : "password"}
                          name="password"
                          autoComplete="current-password"
                          value={values.password}
                          onChange={handleChange}
                          onBlur={handleBlur}
                          className={`pr-10 ${
                            touched.password && errors.password
                              ? "border-red-500 focus-visible:ring-red-500"
                              : ""
                          }`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword((prev) => !prev)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                          tabIndex={-1}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>

                      {touched.password && errors.password && (
                        <p className="text-sm text-red-500 font-medium mt-1">
                          {errors.password}
                        </p>
                      )}
                    </div>

                    {/* Submit Button - Bootstrap Primary Blue (#0d6efd) approx: bg-blue-600 */}
                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      {isSubmitting
                        ? t("loginPage.submittingButton")
                        : t("loginPage.submitButton")}
                    </Button>
                  </FormikForm>
                )}
              </Formik>

              {/* Forgot Password Link */}
              <div className="mt-4 text-right">
                <Link
                  to="/reset-password"
                  className="text-sm text-blue-600 hover:underline hover:text-blue-800 font-medium"
                >
                  {t("loginPage.forgotPasswordLink")}
                </Link>
              </div>

              {/* Contact / WhatsApp Section */}
              <div className="mt-6 text-center">
                <p className="text-gray-500 text-sm mb-2">
                  {t("loginPage.contactHelpText")}
                </p>
                {/* WhatsApp Button - Bootstrap Success Green (#198754) approx: bg-green-700 */}
                <Button
                  asChild
                  variant="default"
                  className="w-full bg-[#198754] hover:bg-[#157347] text-white"
                >
                  <a
                    href="https://wa.me/96181239167"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2"
                  >
                    {/* SVG for WhatsApp (replacing bi-whatsapp) */}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      fill="currentColor"
                      viewBox="0 0 16 16"
                    >
                      <path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592zm3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.729.729 0 0 0-.529.247c-.182.198-.691.677-.691 1.654 0 .977.71 1.916.81 2.049.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z" />
                    </svg>
                    {t("loginPage.contactWhatsAppButton")}
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <ForgotPasswordModal
        show={showForgotPassword}
        handleClose={() => setShowForgotPassword(false)}
      />
    </>
  );
};

export default LoginPage;
