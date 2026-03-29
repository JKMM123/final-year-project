// src/pages/Bills/modals/DownloadBillsModal.tsx

import { useState, useEffect } from "react";
import { Modal, Button, Form, Spinner, Alert } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useAlert } from "../../../hooks/useAlert";
import { startBillsGeneration } from "../billsService";
import { useTask } from "../../../context/TaskContext";
import { getDefaultMonth } from "../../../utils/dateHelpers";

interface DownloadBillsModalProps {
  show: boolean;
  handleClose: () => void;
}

export const DownloadBillsModal = ({
  show,
  handleClose,
}: DownloadBillsModalProps) => {
  const { t, i18n } = useTranslation();
  const [selectedMonth, setSelectedMonth] = useState(getDefaultMonth());
  const { success, handleError } = useAlert();
  const { taskId, taskStatus, startTask, clearTask, checkTaskStatus } =
    useTask();

  const [isStartingGeneration, setIsStartingGeneration] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Poll for status updates when the modal opens
  useEffect(() => {
    if (show && taskId) {
      checkTaskStatus(taskId); // one-time refresh
    }
  }, [show, taskId, checkTaskStatus]);

  const handleCloseModal = () => {
    setModalError(null);
    handleClose();
  };

  const handleGenerate = async () => {
    setIsStartingGeneration(true);
    setModalError(null);
    try {
      const billingDate = `${selectedMonth}`;
      const response = await startBillsGeneration(billingDate);

      // CASE 1: No bills returned
      if (Array.isArray(response.data)) {
        const msg = t("bills.dowloadModal.messages.noBillsForMonth");
        handleError(msg);
        setModalError(msg);
        return;
      }

      // CASE 2: Normal case with task_id
      if (response.data.task_id) {
        startTask(response.data.task_id);
        success(t("bills.dowloadModal.messages.generationStarted"));
      } else {
        const msg = t("bills.dowloadModal.messages.unexpectedResponse");
        handleError(msg);
        setModalError(msg);
      }
    } catch (error: any) {
      const msg =
        error?.message || t("bills.dowloadModal.messages.generationError");
      handleError(msg);
      setModalError(msg);
    } finally {
      setIsStartingGeneration(false);
    }
  };

  const handleFileDownload = () => {
    if (taskStatus?.result?.download_url) {
      window.open(taskStatus.result.download_url, "_blank");
      success(t("bills.dowloadModal.messages.downloadStarting"));
      clearTask();
      handleClose();
    } else {
      handleError(t("bills.dowloadModal.messages.downloadUrlMissing"));
    }
  };

  const handleStartNew = () => {
    clearTask();
    setSelectedMonth(getDefaultMonth());
  };

  const renderBody = () => {
    return (
      <>
        {modalError && (
          <Alert variant="danger" className="mb-3">
            {modalError}
          </Alert>
        )}

        {!taskId ? (
          <>
            <p>{t("bills.downloadModal.initial.description")}</p>
            <Form.Group>
              <Form.Label>{t("bills.downloadModal.initial.label")}</Form.Label>
              <Form.Control
                type="month"
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                  setModalError(null); // clear old errors when user changes month
                }}
                style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
              />
            </Form.Group>
          </>
        ) : (
          (() => {
            switch (taskStatus?.status) {
              case "PENDING":
                return (
                  <Alert variant="info">
                    <Alert.Heading>
                      {t("bills.downloadModal.pending.title")}
                    </Alert.Heading>
                    <p>{t("bills.downloadModal.pending.body")}</p>
                    <hr />
                    <p className="mb-0">
                      {t("bills.downloadModal.pending.footer")}
                    </p>
                  </Alert>
                );
              case "SUCCESS":
                return (
                  <Alert variant="success">
                    <Alert.Heading>
                      {t("bills.downloadModal.success.title")}
                    </Alert.Heading>
                    <p>{t("bills.downloadModal.success.body")}</p>
                  </Alert>
                );
              case "FAILURE":
                return (
                  <Alert variant="danger">
                    <Alert.Heading>
                      {t("bills.downloadModal.failure.title")}
                    </Alert.Heading>
                    <p>{t("bills.downloadModal.failure.body")}</p>
                  </Alert>
                );
              default:
                return (
                  <div className="text-center">
                    <Spinner animation="border" role="status" />
                    <p className="mt-2">
                      {t("bills.downloadModal.checkingStatus")}
                    </p>
                  </div>
                );
            }
          })()
        )}
      </>
    );
  };

  const renderFooter = () => {
    return (
      <Modal.Footer>
        {!taskId && (
          <>
            <Button
              variant="secondary"
              onClick={handleClose}
              disabled={isStartingGeneration}
            >
              {t("common.cancel")}
            </Button>
            <Button
              variant="primary"
              onClick={handleGenerate}
              disabled={isStartingGeneration || !selectedMonth}
            >
              {isStartingGeneration
                ? t("bills.downloadModal.buttons.downloading")
                : t("bills.downloadModal.buttons.download")}
            </Button>
          </>
        )}
        {taskId && taskStatus?.status === "PENDING" && (
          <Button variant="primary" onClick={handleClose}>
            {t("common.close")}
          </Button>
        )}
        {taskId && taskStatus?.status === "SUCCESS" && (
          <>
            <Button variant="secondary" onClick={handleStartNew}>
              {t("bills.downloadModal.buttons.startNew")}
            </Button>
            <Button variant="success" onClick={handleFileDownload}>
              {t("bills.downloadModal.buttons.downloadReady")}
            </Button>
          </>
        )}
        {taskId && taskStatus?.status === "FAILURE" && (
          <Button variant="primary" onClick={handleStartNew}>
            {t("bills.downloadModal.buttons.tryNew")}
          </Button>
        )}
      </Modal.Footer>
    );
  };

  return (
    <Modal show={show} onHide={handleCloseModal} centered backdrop={true}>
      <Modal.Header closeButton>
        <Modal.Title>{t("bills.downloadModal.title")}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{renderBody()}</Modal.Body>
      {renderFooter()}
    </Modal>
  );
};
