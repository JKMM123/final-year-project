// src/features/auth/ForgotPasswordModal.tsx

import React, { useState, useEffect } from "react";
import { Modal, Button, Form, Alert, Spinner } from "react-bootstrap";
import { Formik, Form as FormikForm, Field } from "formik";
import * as Yup from "yup";
import { useTranslation, Trans } from "react-i18next";
import type { TFunction } from "i18next";
import { useAlert } from "../../hooks/useAlert";
import { sendOtp, verifyOtp, resetPassword } from "./loginService";

// Helper to handle API errors
const getApiErrorMessage = (error: any, t: TFunction) => {
  return error.response?.data?.message || t("common.errors.unexpected");
};

// Props for the modal
interface ForgotPasswordModalProps {
  show: boolean;
  handleClose: () => void;
}

const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({
  show,
  handleClose,
}) => {
  const { t } = useTranslation();
  const [step, setStep] = useState<"phone" | "otp" | "password" | "success">(
    "phone"
  );
  const [phoneNumber, setPhoneNumber] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { success, handleError } = useAlert();

  const handleModalClose = () => {
    // Reset state completely when modal is closed
    setTimeout(() => {
      setStep("phone");
      setPhoneNumber("");
      setResetToken("");
      setError(null);
    }, 300); // Delay to allow modal fade-out animation
    handleClose();
  };

  const renderStepContent = () => {
    switch (step) {
      case "phone":
        return (
          <PhoneNumberStep
            onSubmit={handlePhoneSubmit}
            error={error}
            setError={setError}
          />
        );
      case "otp":
        return (
          <OtpStep
            phoneNumber={phoneNumber}
            onSubmit={handleOtpSubmit}
            error={error}
            setError={setError}
          />
        );
      case "password":
        return (
          <ResetPasswordStep
            onSubmit={handlePasswordSubmit}
            error={error}
            setError={setError}
          />
        );
      case "success":
        return <SuccessStep onClose={handleModalClose} />;
      default:
        return null;
    }
  };

  // --- Handlers for each step ---

  const handlePhoneSubmit = async (
    values: { phone_number: string },
    { setSubmitting }: any
  ) => {
    setError(null);
    try {
      await sendOtp(values.phone_number);
      success(t("forgotPassword.notifications.otpSent"));
      setPhoneNumber(values.phone_number);
      setStep("otp");
    } catch (err: any) {
      const message = getApiErrorMessage(err, t);
      setError(message);
      handleError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOtpSubmit = async (
    values: { otp: string },
    { setSubmitting }: any
  ) => {
    setError(null);
    try {
      const response = await verifyOtp({
        phone_number: phoneNumber,
        otp: values.otp,
      });
      success(t("forgotPassword.notifications.otpVerified"));
      setResetToken(response.data.reset_token);
      setStep("password");
    } catch (err: any) {
      const message = getApiErrorMessage(err, t);
      setError(message);
      handleError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePasswordSubmit = async (
    values: { new_password: string },
    { setSubmitting }: any
  ) => {
    setError(null);
    try {
      await resetPassword({
        phone_number: phoneNumber,
        reset_token: resetToken,
        new_password: values.new_password,
      });
      success(t("forgotPassword.notifications.passwordResetSuccess"));
      setStep("success");
    } catch (err: any) {
      const message = getApiErrorMessage(err, t);
      setError(message);
      handleError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal show={show} onHide={handleModalClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>{t("forgotPassword.title")}</Modal.Title>
      </Modal.Header>
      <Modal.Body className="p-4">{renderStepContent()}</Modal.Body>
    </Modal>
  );
};

// --- Step Components ---

const PhoneNumberStep = ({ onSubmit, error, setError }: any) => {
  const { t } = useTranslation();

  const PhoneSchema = Yup.object().shape({
    phone_number: Yup.string()
      .matches(/^[0-9]{8}$/, t("forgotPassword.validations.phoneInvalid"))
      .required(t("forgotPassword.validations.phoneRequired")),
  });

  return (
    <>
      <p className="text-muted">{t("forgotPassword.phone.description")}</p>
      {error && <Alert variant="danger">{error}</Alert>}
      <Formik
        initialValues={{ phone_number: "" }}
        validationSchema={PhoneSchema}
        onSubmit={onSubmit}
      >
        {({ isSubmitting, errors, touched }) => (
          <FormikForm>
            <Form.Group>
              <Form.Label>{t("forgotPassword.phone.label")}</Form.Label>
              <Field name="phone_number">
                {({ field, form }: any) => (
                  <Form.Control
                    {...field}
                    type="tel"
                    isInvalid={touched.phone_number && !!errors.phone_number}
                    onChange={(e: any) => {
                      setError(null);
                      const onlyNums = e.target.value.replace(/[^0-9]/g, "");
                      form.setFieldValue(field.name, onlyNums);
                    }}
                  />
                )}
              </Field>
              <Form.Control.Feedback type="invalid">
                {errors.phone_number}
              </Form.Control.Feedback>
            </Form.Group>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-100 mt-4"
            >
              {isSubmitting ? (
                <Spinner as="span" animation="border" size="sm" />
              ) : (
                t("forgotPassword.phone.button")
              )}
            </Button>
          </FormikForm>
        )}
      </Formik>
    </>
  );
};

const OtpStep = ({ phoneNumber, onSubmit, error, setError }: any) => {
  const { t } = useTranslation();
  const [timer, setTimer] = useState(60);
  const { success, handleError } = useAlert();

  const OtpSchema = Yup.object().shape({
    otp: Yup.string()
      .matches(/^[0-9]{4}$/, t("forgotPassword.validations.otpInvalid"))
      .required(t("forgotPassword.validations.otpRequired")),
  });

  useEffect(() => {
    if (timer === 0) return;
    const interval = setInterval(() => setTimer((t) => t - 1), 1000);
    return () => clearInterval(interval);
  }, [timer]);

  const handleResend = async () => {
    if (timer > 0) return;
    try {
      await sendOtp(phoneNumber);
      success(t("forgotPassword.notifications.newOtpSent"));
      setTimer(60); // Reset timer
      setError(null);
    } catch (err: any) {
      const message = getApiErrorMessage(err, t);
      setError(message);
      handleError(message);
    }
  };

  return (
    <>
      <p className="text-muted text-center">
        <Trans
          i18nKey="forgotPassword.otp.description"
          values={{ phoneNumber }}
          components={{ strong: <strong /> }}
        >
          Enter the 4-digit code sent to <br />
          <strong>+961 {phoneNumber}</strong>
        </Trans>
      </p>
      {error && <Alert variant="danger">{error}</Alert>}
      <Formik
        initialValues={{ otp: "" }}
        validationSchema={OtpSchema}
        onSubmit={onSubmit}
      >
        {({ isSubmitting, errors, touched }) => (
          <FormikForm>
            <Form.Group>
              <Form.Label>{t("forgotPassword.otp.label")}</Form.Label>
              <Field name="otp">
                {({ field, form }: any) => (
                  <Form.Control
                    {...field}
                    type="tel"
                    maxLength={4}
                    isInvalid={touched.otp && !!errors.otp}
                    onChange={(e: any) => {
                      setError(null);
                      const onlyNums = e.target.value.replace(/[^0-9]/g, "");
                      form.setFieldValue(field.name, onlyNums);
                    }}
                  />
                )}
              </Field>
              <Form.Control.Feedback type="invalid">
                {errors.otp}
              </Form.Control.Feedback>
            </Form.Group>
            <div className="text-center mt-3">
              <Button
                variant="link"
                onClick={handleResend}
                disabled={timer > 0}
                className="p-0"
              >
                {timer > 0
                  ? t("forgotPassword.otp.resendTimer", { seconds: timer })
                  : t("forgotPassword.otp.resendButton")}
              </Button>
            </div>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-100 mt-3"
            >
              {isSubmitting ? (
                <Spinner as="span" animation="border" size="sm" />
              ) : (
                t("forgotPassword.otp.verifyButton")
              )}
            </Button>
          </FormikForm>
        )}
      </Formik>
    </>
  );
};

const ResetPasswordStep = ({ onSubmit, error, setError }: any) => {
  const { t } = useTranslation();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const PasswordSchema = Yup.object().shape({
    new_password: Yup.string()
      .min(8, t("forgotPassword.validations.passwordMin"))
      .matches(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        t("forgotPassword.validations.passwordPattern")
      )
      .required(t("forgotPassword.validations.newPasswordRequired")),
    confirm_password: Yup.string()
      .oneOf(
        [Yup.ref("new_password")],
        t("forgotPassword.validations.passwordsMustMatch")
      )
      .required(t("forgotPassword.validations.confirmPasswordRequired")),
  });

  return (
    <>
      <p className="text-muted">{t("forgotPassword.password.description")}</p>
      {error && <Alert variant="danger">{error}</Alert>}
      <Formik
        initialValues={{ new_password: "", confirm_password: "" }}
        validationSchema={PasswordSchema}
        onSubmit={onSubmit}
      >
        {({ isSubmitting, errors, touched }) => (
          <FormikForm>
            <Form.Group className="mb-3 position-relative">
              <Form.Label>
                {t("forgotPassword.password.newPasswordLabel")}
              </Form.Label>
              <Field name="new_password">
                {({ field, form }: any) => (
                  <Form.Control
                    {...field}
                    type={showPassword ? "text" : "password"}
                    isInvalid={touched.new_password && !!errors.new_password}
                    onChange={(e: any) => {
                      setError(null);
                      form.setFieldValue(field.name, e.target.value);
                    }}
                  />
                )}
              </Field>
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="btn p-0 border-0 bg-transparent text-muted position-absolute"
                style={{
                  top: "38px",
                  insetInlineEnd: "10px",
                  boxShadow: "none",
                }}
              >
                <i
                  className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`}
                />
              </button>
              <Form.Control.Feedback type="invalid">
                {errors.new_password}
              </Form.Control.Feedback>
            </Form.Group>

            <Form.Group className="position-relative">
              <Form.Label>
                {t("forgotPassword.password.confirmPasswordLabel")}
              </Form.Label>
              <Field name="confirm_password">
                {({ field, form }: any) => (
                  <Form.Control
                    {...field}
                    type={showConfirmPassword ? "text" : "password"}
                    isInvalid={
                      touched.confirm_password && !!errors.confirm_password
                    }
                    onChange={(e: any) => {
                      setError(null);
                      form.setFieldValue(field.name, e.target.value);
                    }}
                  />
                )}
              </Field>
              <button
                type="button"
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                className="btn p-0 border-0 bg-transparent text-muted position-absolute"
                style={{
                  top: "38px",
                  insetInlineEnd: "10px",
                  boxShadow: "none",
                }}
              >
                <i
                  className={`bi ${
                    showConfirmPassword ? "bi-eye-slash" : "bi-eye"
                  }`}
                />
              </button>
              <Form.Control.Feedback type="invalid">
                {errors.confirm_password}
              </Form.Control.Feedback>
            </Form.Group>

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-100 mt-4"
            >
              {isSubmitting ? (
                <Spinner as="span" animation="border" size="sm" />
              ) : (
                t("forgotPassword.password.resetButton")
              )}
            </Button>
          </FormikForm>
        )}
      </Formik>
    </>
  );
};

const SuccessStep = ({ onClose }: any) => {
  const { t } = useTranslation();
  return (
    <div className="text-center p-3">
      <i
        className="bi bi-check-circle-fill text-success"
        style={{ fontSize: "4rem" }}
      ></i>
      <h4 className="mt-3">{t("forgotPassword.success.title")}</h4>
      <p className="text-muted">{t("forgotPassword.success.description")}</p>
      <Button onClick={onClose} className="w-100 mt-3">
        {t("forgotPassword.success.button")}
      </Button>
    </div>
  );
};

export default ForgotPasswordModal;
