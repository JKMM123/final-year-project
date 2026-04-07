// src/features/readings/modals/VerifyAllReadingsModal.tsx

import { useState, useEffect } from "react";
import { Modal, Button, Form, Alert, Spinner, Col, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useAlert } from "../../../hooks/useAlert";
import { verifyAllReadings } from "../readingsService";
import type { VerifyAllApiResponse } from "../types";
import { getDefaultMonth } from "../../../utils/dateHelpers";

interface VerifyAllReadingsModalProps {
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
  initialMonth: string;
}

const VerifyAllReadingsModal = ({
  show,
  handleClose,
  initialMonth,
}: VerifyAllReadingsModalProps) => {
  const { t, i18n } = useTranslation();
  const { handleError } = useAlert();

  const [selectedMonth, setSelectedMonth] = useState(initialMonth);
  const [isLoading, setIsLoading] = useState(false);
  const [apiResponse, setApiResponse] = useState<VerifyAllApiResponse | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  // Reset state when modal is opened/closed
  useEffect(() => {
    if (show) {
      setSelectedMonth(initialMonth);
    } else {
      // Delay reset to allow for closing animation
      setTimeout(() => {
        setApiResponse(null);
        setError(null);
        setIsLoading(false);
      }, 300);
    }
  }, [show, initialMonth]);

  const handleConfirm = async () => {
    setIsLoading(true);
    setError(null);
    setApiResponse(null);

    try {
      const response = await verifyAllReadings({
        confirm: true,
        reading_date: selectedMonth,
      });
      setApiResponse(response);
    } catch (err: any) {
      setError(err.message || t("common.errors.unexpected"));
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFinalClose = () => {
    const verifiedCount =
      apiResponse?.data?.verified_count?.verified_count ?? 0;
    const needsRefresh = verifiedCount > 0;
    handleClose(needsRefresh);
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">{t("common.loading")}</span>
          </Spinner>
          <p className="mt-2">{t("readings.verifyAll.verifying")}</p>
        </div>
      );
    }

    if (error) {
      return <Alert variant="danger">{error}</Alert>;
    }

    if (apiResponse) {
      const { verified_count, message } = apiResponse.data.verified_count;
      return (
        <Alert variant={verified_count > 0 ? "success" : "info"}>
          <Alert.Heading>{t("readings.verifyAll.resultTitle")}</Alert.Heading>
          <p>{message}</p>
          <hr />
          <p className="mb-0">
            {t("readings.verifyAll.verifiedCount", { count: verified_count })}
          </p>
        </Alert>
      );
    }

    // Initial state
    return (
      <>
        <Alert variant="warning">
          {t("readings.verifyAll.confirmationWarning")}
        </Alert>
        <Form.Group as={Row} className="mb-3" controlId="verifyAllMonth">
          <Form.Label column sm="4">
            {t("readings.verifyAll.monthLabel")}
          </Form.Label>
          <Col sm="8">
            <Form.Control
              type="month"
              value={selectedMonth}
              onChange={(e) =>
                setSelectedMonth(e.target.value || getDefaultMonth())
              }
              style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
            />
          </Col>
        </Form.Group>
      </>
    );
  };

  return (
    <Modal show={show} onHide={() => handleClose(false)} centered>
      <Modal.Header closeButton>
        <Modal.Title>{t("readings.verifyAll.title")}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{renderContent()}</Modal.Body>
      <Modal.Footer>
        {apiResponse || error ? (
          <Button variant="secondary" onClick={handleFinalClose}>
            {t("common.close")}
          </Button>
        ) : (
          <>
            <Button variant="secondary" onClick={() => handleClose(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirm}
              disabled={isLoading}
            >
              {t("common.confirm")}
            </Button>
          </>
        )}
      </Modal.Footer>
    </Modal>
  );
};

export default VerifyAllReadingsModal;
