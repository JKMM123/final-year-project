import { Modal, Button, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

interface ConfirmationModalProps {
  show: boolean;
  title: string;
  body: React.ReactNode; // Can be a string or more complex JSX
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onHide: () => void;
  isConfirming?: boolean;
  confirmingText?: string;
}

export const ConfirmationModal = ({
  show,
  title,
  body,
  onConfirm,
  onHide,
  isConfirming = false,
}: ConfirmationModalProps) => {
  const { t } = useTranslation();

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title className="text-danger">{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{body}</Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide} disabled={isConfirming}>
          {t("common.cancel")}
        </Button>
        <Button variant="danger" onClick={onConfirm} disabled={isConfirming}>
          {isConfirming ? (
            <>
              <Spinner
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
              />
              <span className="ms-2">{t("common.confirming")}</span>
            </>
          ) : (
            t("common.confirm")
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
