import { useEffect, useState } from "react";
import { Modal, Button, Spinner, Alert } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { getMeterQrCode } from "../metersService";

interface QrCodeModalProps {
  meterId: string;
  show: boolean;
  handleClose: () => void;
}

const QrCodeModal = ({ meterId, show, handleClose }: QrCodeModalProps) => {
  const { t } = useTranslation();
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (show && meterId) {
      setIsLoading(true);
      setError(null);
      setQrCodeUrl(null);
      getMeterQrCode(meterId)
        .then((url) => setQrCodeUrl(url))
        .catch(() => setError(t("meters.qrModal.qrCodeLoadError")))
        .finally(() => setIsLoading(false));
    }
    // Adding `t` to dependency array as it's an external function
  }, [show, meterId, t]);

  const handleDownload = () => {
    if (!qrCodeUrl) return;

    const a = document.createElement("a");
    a.href = qrCodeUrl;
    a.download = `meter_${meterId}_qr_code.png`; // Provide a meaningful default filename
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>{t("meters.qrModal.qrCodeTitle")}</Modal.Title>
      </Modal.Header>
      <Modal.Body className="text-center">
        {isLoading && <Spinner animation="border" />}
        {error && <Alert variant="danger">{error}</Alert>}
        {qrCodeUrl && (
          <img
            src={qrCodeUrl}
            alt={t("meters.qrModal.qrCodeAltText", { meterId })}
            className="img-fluid"
          />
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          {t("common.close")}
        </Button>
        <Button
          variant="primary"
          onClick={handleDownload}
          disabled={!qrCodeUrl || isLoading}
        >
          <i className="bi bi-download mx-2"></i>
          {t("common.download")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default QrCodeModal;
