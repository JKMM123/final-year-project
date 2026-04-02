// src/pages/Messages/ManagePhoneNumber/ManagePhoneNumber.tsx

import { useState, useEffect, useRef, useCallback, lazy, useMemo } from "react";
import { Formik, Form, Field, ErrorMessage } from "formik";
import * as Yup from "yup";
import { QRCodeSVG } from "qrcode.react";
import {
  Button,
  Card,
  Spinner,
  Alert,
  Container,
  Row,
  Col,
} from "react-bootstrap";
import { FaCheckCircle, FaExclamationTriangle } from "react-icons/fa";
import { useTranslation, Trans } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { BsArrowLeft, BsArrowRight } from "react-icons/bs";

import { useAlert } from "../../../hooks/useAlert";
import {
  getSessionStatus,
  createSession,
  connectSession,
  deleteSession,
  WEBHOOK_URL,
} from "./whatsAppService";
import type { WebhookEventData } from "./types";

const ConfirmationModal = lazy(() =>
  import("../../../components/common/ConfirmationModal").then((module) => ({
    default: module.ConfirmationModal,
  }))
);

// State machine views for the component
type ViewState =
  | "LOADING"
  | "SHOW_FORM"
  | "SHOW_QR"
  | "CONNECTING"
  | "CONNECTED";

// Lebanese phone number validation
const lebanesePhoneNumberRegex = /^(03|70|71|76|78|79|81)\d{6}$/;

const QR_EXPIRY_SECONDS = 45;

export const ManagePhoneNumber = () => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.dir() === "rtl";
  const [view, setView] = useState<ViewState>("LOADING");
  const [qrCode, setQrCode] = useState<string>("");
  const [persistentError, setPersistentError] = useState<string | null>(null);
  const [timerKey, setTimerKey] = useState(Date.now()); // Used to reset the timer
  const { success, handleError } = useAlert();
  const eventSourceRef = useRef<EventSource | null>(null);
  const [showDisconnectModal, setShowDisconnectModal] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [qrLoading, setQrLoading] = useState(false);
  const navigate = useNavigate();

  const validationSchema = useMemo(
    () =>
      Yup.object({
        name: Yup.string().required(
          t("messages.managePhoneNumber.form.validations.nameRequired")
        ),
        phone_number: Yup.string()
          .matches(
            lebanesePhoneNumberRegex,
            t("messages.managePhoneNumber.form.validations.phoneInvalid")
          )
          .required(
            t("messages.managePhoneNumber.form.validations.phoneRequired")
          ),
      }),
    [t]
  );

  const startWebhookListener = useCallback(() => {
    // Ensure no old listener is running
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const events = new EventSource(WEBHOOK_URL);
    eventSourceRef.current = events;

    events.onmessage = (event) => {
      try {
        const data: WebhookEventData = JSON.parse(event.data);
        if (data.event === "session.status") {
          switch (data.status) {
            case "connecting":
              setView("CONNECTING");
              break;
            case "connected":
              setView("CONNECTED");
              events.close(); // Stop listening once connected
              break;
            case "need_scan":
              break;
          }
        }
      } catch (error) {
        console.error("Failed to parse webhook event:", error);
      }
    };

    events.onerror = () => {
      console.error("EventSource failed.");
      events.close();
    };
  }, []);

  const handleGenerateQr = useCallback(
    async (apiCall: () => Promise<any>, isRefresh: boolean = false) => {
      if (!isRefresh) {
        setView("LOADING");
      }

      setPersistentError(null);
      try {
        const response = await apiCall();
        if (response.data?.qrCode) {
          setQrCode(response.data.qrCode);
          setView("SHOW_QR");
          setTimerKey(Date.now()); // Reset timer
          startWebhookListener();
        }
      } catch (error: any) {
        handleError(error);
        setView("SHOW_FORM");
      }
    },
    [handleError, startWebhookListener]
  );

  const handleCreateSession = useCallback(
    async (values: { name: string; phone_number: string }) => {
      await handleGenerateQr(async () => {
        try {
          return await createSession(values);
        } catch (error: any) {
          if (
            error.response?.data?.message?.includes("already has a session")
          ) {
            setPersistentError(
              t("messages.managePhoneNumber.errors.alreadyRegistered")
            );
            return connectSession();
          }
          throw error;
        }
      });
    },
    [handleGenerateQr, t]
  );

  const handleRefreshQr = useCallback(async () => {
    setQrLoading(true);
    try {
      await handleGenerateQr(connectSession, true);
    } finally {
      setQrLoading(false);
    }
  }, [handleGenerateQr]);

  useEffect(() => {
    const checkInitialStatus = async () => {
      try {
        const { status } = await getSessionStatus();
        if (status === "connected") {
          setView("CONNECTED");
        } else {
          setView("SHOW_FORM");
        }
      } catch (error: any) {
        if (error.response?.status === 404) {
          setView("SHOW_FORM");
        } else {
          handleError(error);
          setPersistentError(
            t("messages.managePhoneNumber.errors.statusFetchFailed")
          );
        }
      }
    };
    checkInitialStatus();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [handleError, t]);

  const handleConfirmDisconnect = async () => {
    setIsDisconnecting(true);
    try {
      await deleteSession();
      success(t("messages.managePhoneNumber.notifications.disconnected"));
      setView("SHOW_FORM");
      setPersistentError(null);
    } catch (error) {
      handleError(error);
      setView("CONNECTED");
    } finally {
      setIsDisconnecting(false);
      setShowDisconnectModal(false);
    }
  };

  const renderContent = () => {
    switch (view) {
      case "LOADING":
        return (
          <div className="text-center px-3 py-5">
            <Spinner animation="border" />
          </div>
        );

      case "SHOW_FORM":
        return (
          <Card.Body className="px-3 py-5">
            <Card.Title>
              {t("messages.managePhoneNumber.form.title")}
            </Card.Title>
            <p className="text-muted">
              {t("messages.managePhoneNumber.form.description")}
            </p>
            {persistentError && (
              <Alert variant="warning">{persistentError}</Alert>
            )}
            <Formik
              initialValues={{ name: "", phone_number: "" }}
              validationSchema={validationSchema}
              onSubmit={handleCreateSession}
            >
              {({ isSubmitting }) => (
                <Form>
                  <div className="mb-3">
                    <label htmlFor="name" className="form-label">
                      {t("messages.managePhoneNumber.form.nameLabel")}
                    </label>
                    <Field name="name" type="text" className="form-control" />
                    <ErrorMessage
                      name="name"
                      component="div"
                      className="text-danger small"
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="phone_number" className="form-label">
                      {t("messages.managePhoneNumber.form.phoneLabel")}
                    </label>
                    <Field
                      name="phone_number"
                      type="tel"
                      className="form-control"
                      placeholder={t(
                        "messages.managePhoneNumber.form.phonePlaceholder"
                      )}
                    />
                    <ErrorMessage
                      name="phone_number"
                      component="div"
                      className="text-danger small"
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    variant="primary"
                  >
                    {isSubmitting ? (
                      <Spinner as="span" size="sm" />
                    ) : (
                      t("messages.managePhoneNumber.form.button")
                    )}
                  </Button>
                </Form>
              )}
            </Formik>
          </Card.Body>
        );

      case "SHOW_QR":
        return (
          <Card.Body className="text-center px-3 py-5">
            <Card.Title>{t("messages.managePhoneNumber.qr.title")}</Card.Title>
            <p className="text-muted">
              <Trans i18nKey="messages.managePhoneNumber.qr.description">
                Open WhatsApp on your phone, go to{" "}
                <strong>Settings &gt; Linked Devices</strong>, and scan this
                code.
              </Trans>
            </p>

            <div className="d-inline-block">
              <div
                className="bg-white p-3 rounded shadow-sm mb-3 d-flex justify-content-center align-items-center"
                style={{ maxWidth: "280px", minHeight: "280px" }}
              >
                {qrLoading ? (
                  <Spinner animation="border" variant="secondary" />
                ) : (
                  <QRCodeSVG
                    value={qrCode}
                    style={{ width: "100%", height: "auto" }}
                  />
                )}
              </div>

              <CountdownTimer
                key={timerKey}
                duration={QR_EXPIRY_SECONDS}
                onComplete={handleRefreshQr}
              />

              <div className="mt-2">
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={handleRefreshQr}
                  disabled={qrLoading}
                >
                  {t("messages.managePhoneNumber.qr.refreshButton")}
                </Button>
              </div>
            </div>
          </Card.Body>
        );

      case "CONNECTING":
        return (
          <Card.Body className="text-center px-3 py-5">
            <Spinner animation="border" variant="primary" />
            <h5 className="mt-3">
              {t("messages.managePhoneNumber.connecting.title")}
            </h5>
            <p className="text-muted">
              {t("messages.managePhoneNumber.connecting.description")}
            </p>
          </Card.Body>
        );

      case "CONNECTED":
        return (
          <Card.Body className="text-center px-3 py-5">
            <FaCheckCircle size={60} className="text-success mb-3" />
            <h3>{t("messages.managePhoneNumber.connected.title")}</h3>
            <p className="text-muted">
              {t("messages.managePhoneNumber.connected.description")}
            </p>
            <hr />
            <Button
              variant="danger"
              onClick={() => setShowDisconnectModal(true)}
            >
              <FaExclamationTriangle className="me-2" />
              {t("messages.managePhoneNumber.connected.disconnectButton")}
            </Button>
          </Card.Body>
        );

      default:
        return null;
    }
  };

  return (
    <Container className="mt-2 ">
      <Row className="mb-2">
        <Col xs="auto">
          <Button variant="outline" onClick={() => navigate("/messages")}>
            {isRTL ? (
              <>
                <BsArrowRight className="ms-2" />
                {t("messages.managePhoneNumber.backButton")}
              </>
            ) : (
              <>
                <BsArrowLeft className="me-2" />
                {t("messages.managePhoneNumber.backButton")}
              </>
            )}
          </Button>
        </Col>
      </Row>

      <Row className="justify-content-center">
        <Col md={8} lg={8} sm={12}>
          <Card>{renderContent()}</Card>
        </Col>
      </Row>

      <ConfirmationModal
        show={showDisconnectModal}
        title={t("messages.managePhoneNumber.disconnectModal.title")}
        body={<p>{t("messages.managePhoneNumber.disconnectModal.body")}</p>}
        onConfirm={handleConfirmDisconnect}
        onHide={() => setShowDisconnectModal(false)}
        isConfirming={isDisconnecting}
        confirmText={t(
          "messages.managePhoneNumber.disconnectModal.confirmText"
        )}
        confirmingText={t(
          "messages.managePhoneNumber.disconnectModal.confirmingText"
        )}
      />
    </Container>
  );
};

// --- Reusable Countdown Timer Component ---
interface CountdownTimerProps {
  duration: number;
  onComplete: () => void;
  key: any;
}

const CountdownTimer = ({ duration, onComplete }: CountdownTimerProps) => {
  const [timeLeft, setTimeLeft] = useState(duration);

  useEffect(() => {
    if (timeLeft <= 0) {
      onComplete();
      return;
    }
    const intervalId = setInterval(() => {
      setTimeLeft(timeLeft - 1);
    }, 1000);
    return () => clearInterval(intervalId);
  }, [timeLeft, onComplete]);

  return (
    <Alert variant="info" className="d-inline-block p-2 mb-3">
      <Trans
        i18nKey="messages.managePhoneNumber.qr.expiryMessage"
        values={{ timeLeft }}
      >
        QR code expires in <strong>{timeLeft}</strong> seconds.
      </Trans>
    </Alert>
  );
};
