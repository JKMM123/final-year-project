// src/features/meters/modals/PayAllUnpaidBillsModal.tsx

import { useState } from "react";
import { Modal, Button, Alert, Spinner, Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import Select from "react-select";
import type { SingleValue } from "react-select";
import { useAlert } from "../../../hooks/useAlert"; // Make sure you import your hook
import { markAllUnpaidAsPaid } from "../metersService";

interface PayAllUnpaidBillsModalProps {
  show: boolean;
  handleClose: () => void;
  meterId: string | null;
  onSuccess: () => void;
}

interface PaymentOption {
  value: string;
  label: string;
}

export const PayAllUnpaidBillsModal = ({
  show,
  handleClose,
  meterId,
  onSuccess,
}: PayAllUnpaidBillsModalProps) => {
  const { t } = useTranslation();
  // Here we get the functions directly from your context via the hook
  const { handleError, success: handleSuccess } = useAlert();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedMethod, setSelectedMethod] =
    useState<SingleValue<PaymentOption>>(null);

  const paymentOptions: PaymentOption[] = [
    {
      value: "cash",
      label: t("meters.statementModal.payAllBillsModal.paymentMethods.cash"),
    },
    {
      value: "whish",
      label: t("meters.statementModal.payAllBillsModal.paymentMethods.wish"),
    },
    {
      value: "omt",
      label: t("meters.statementModal.payAllBillsModal.paymentMethods.omt"),
    },
  ];

  const handleConfirm = async () => {
    if (!meterId || !selectedMethod) {
      // Your handleError function handles string messages perfectly.
      handleError(
        t("meters.statementModal.payAllBillsModal.errors.noMethodSelected")
      );
      return;
    }

    setIsSubmitting(true);
    try {
      await markAllUnpaidAsPaid(meterId, selectedMethod.value);
      handleSuccess(t("meters.statementModal.payAllBillsModal.successMessage"));
      onSuccess();
      handleModalClose();
    } catch (err) {
      handleError(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleModalClose = () => {
    setSelectedMethod(null);
    handleClose();
  };

  return (
    <Modal show={show} onHide={handleModalClose} centered>
      <Modal.Header closeButton>
        <Modal.Title as="h5">
          {t("meters.statementModal.payAllBillsModal.title")}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Alert variant="warning">
          {t("meters.statementModal.payAllBillsModal.disclaimer")}
        </Alert>

        <Form.Group className="mt-3">
          <Form.Label className="fw-bold">
            {t("meters.statementModal.payAllBillsModal.paymentMethodLabel")}
          </Form.Label>
          <Select
            options={paymentOptions}
            value={selectedMethod}
            onChange={setSelectedMethod}
            placeholder={t(
              "meters.statementModal.payAllBillsModal.paymentMethodPlaceholder"
            )}
            isClearable
          />
        </Form.Group>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleModalClose}>
          {t("common.cancel")}
        </Button>
        <Button
          variant="primary"
          onClick={handleConfirm}
          disabled={!selectedMethod || isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Spinner
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
              />{" "}
              {t("common.submitting")}
            </>
          ) : (
            t("common.confirm")
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
