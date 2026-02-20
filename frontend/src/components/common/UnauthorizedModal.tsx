import { Modal, Button } from "react-bootstrap";

interface UnauthorizedModalProps {
  show: boolean;
  onConfirm: () => void;
}

export const UnauthorizedModal = ({
  show,
  onConfirm,
}: UnauthorizedModalProps) => {
  return (
    <Modal show={show} onHide={onConfirm} centered>
      <Modal.Header closeButton>
        <Modal.Title className="text-danger">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>Access Denied
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        You do not have permission to access this page or perform this action.
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onConfirm}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
