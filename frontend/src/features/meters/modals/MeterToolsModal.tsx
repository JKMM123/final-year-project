import { useState } from "react";
import {
  Modal,
  Button,
  Nav,
  Spinner,
  Alert,
  ListGroup,
  Form,
} from "react-bootstrap";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { getAllQrCodesZipUrl, uploadMetersFile } from "../metersService";

interface MeterToolsModalProps {
  show: boolean;
  handleClose: () => void;
  onUploadSuccess?: () => void;
}

type ActiveTab = "download" | "upload";

export const MeterToolsModal = ({
  show,
  handleClose,
  onUploadSuccess,
}: MeterToolsModalProps) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<ActiveTab>("download");

  // State for Download tab
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [isFetchingUrl, setIsFetchingUrl] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // State for Upload tab
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadErrors, setUploadErrors] = useState<string[]>([]);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [didUploadSucceed, setDidUploadSucceed] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUploadErrors([]);
    setUploadSuccess(null);
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadErrors([]);
    setUploadSuccess(null);
    setDidUploadSucceed(false);

    try {
      const response = await uploadMetersFile(selectedFile);
      setUploadSuccess(
        response.message || t("meters.toolsModal.uploadTab.successMessage")
      );
      setSelectedFile(null);
      setDidUploadSucceed(true);
    } catch (error: any) {
      setDidUploadSucceed(false);
      if (error instanceof AxiosError && error.response?.data?.errors) {
        setUploadErrors(error.response.data.message);
      } else {
        setUploadErrors([
          error.response?.data?.message ||
            t("meters.toolsModal.uploadTab.genericError"),
        ]);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const onModalExit = () => {
    if (didUploadSucceed && uploadErrors.length === 0 && onUploadSuccess) {
      onUploadSuccess();
    }
    setActiveTab("download");
    setDownloadUrl(null);
    setFetchError(null);
    setSelectedFile(null);
    setUploadErrors([]);
    setUploadSuccess(null);
    setDidUploadSucceed(false);
  };

  return (
    <Modal show={show} onHide={handleClose} centered onExited={onModalExit}>
      <Modal.Header closeButton>
        <Modal.Title>{t("meters.toolsModal.title")}</Modal.Title>
      </Modal.Header>
      <Nav
        variant="tabs"
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k as ActiveTab)}
        className="px-3 pt-3"
      >
        <Nav.Item>
          <Nav.Link eventKey="download">
            {t("meters.toolsModal.downloadTab.title")}
          </Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link eventKey="upload">
            {t("meters.toolsModal.uploadTab.title")}
          </Nav.Link>
        </Nav.Item>
      </Nav>
      <Modal.Body>
        {activeTab === "download" && (
          <div>
            <h5>{t("meters.toolsModal.downloadTab.heading")}</h5>
            <p className="text-muted">
              {t("meters.toolsModal.downloadTab.description")}
            </p>

            {fetchError && <Alert variant="danger">{fetchError}</Alert>}
            {uploadSuccess && <Alert variant="success">{uploadSuccess}</Alert>}

            <div className="d-grid mb-3">
              <Button
                variant="outline-primary"
                onClick={async () => {
                  setIsFetchingUrl(true);
                  setFetchError(null);
                  setDownloadUrl(null);
                  try {
                    const url = await getAllQrCodesZipUrl();
                    setDownloadUrl(url);
                  } catch (err) {
                    setFetchError(
                      t("meters.toolsModal.downloadTab.fetchError")
                    );
                  } finally {
                    setIsFetchingUrl(false);
                  }
                }}
                disabled={isFetchingUrl}
              >
                {isFetchingUrl ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                    />{" "}
                    {t("meters.toolsModal.downloadTab.requestingBtn")}
                  </>
                ) : (
                  t("meters.toolsModal.downloadTab.requestBtn")
                )}
              </Button>
            </div>

            <div className="d-grid">
              <a
                href={downloadUrl || "#"}
                download={downloadUrl ? "meter_qr_codes.zip" : undefined}
                className={`btn btn-primary ${!downloadUrl ? "disabled" : ""}`}
                style={{
                  pointerEvents: !downloadUrl ? "none" : "auto",
                }}
              >
                <i className="bi bi-file-earmark-zip-fill me-2"></i>
                {t("meters.toolsModal.downloadTab.downloadBtn")}
              </a>
            </div>
          </div>
        )}

        {activeTab === "upload" && (
          <div>
            <h5>{t("meters.toolsModal.uploadTab.heading")}</h5>
            <div className="mb-3 p-3 bg-light border rounded">
              <h6 className="mb-2">
                📋 {t("meters.toolsModal.uploadTab.requirements.title")}
              </h6>
              <ul className="mb-2">
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.fullName.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.fullName.description",
                    { example: "Fadi Hadid" }
                  )}
                </li>
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.phoneNumber.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.phoneNumber.description",
                    { example: "70186126" }
                  )}
                </li>
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.address.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.address.description",
                    { example: "street 2 building 3" }
                  )}
                </li>
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.amperage.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.amperage.description",
                    { example1: 5, example2: 10 }
                  )}
                </li>
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.area.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.area.description",
                    { example1: "broumana", example2: "zaraoun" }
                  )}
                </li>
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.packageType.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.packageType.description",
                    { example1: "fixed", example2: "usage" }
                  )}
                </li>
                <li>
                  <strong>
                    {t(
                      "meters.toolsModal.uploadTab.requirements.fields.initialReading.label"
                    )}
                  </strong>
                  :{" "}
                  {t(
                    "meters.toolsModal.uploadTab.requirements.fields.initialReading.description",
                    { example1: 7, example2: 123 }
                  )}
                </li>
              </ul>
              <p className="mb-0">
                ✅{" "}
                <strong>
                  {t(
                    "meters.toolsModal.uploadTab.requirements.acceptedFormats"
                  )}
                </strong>{" "}
                <code>.csv</code>, <code>.xlsx(excel)</code>
                <br />
                ⚠️ {t("meters.toolsModal.uploadTab.requirements.columnWarning")}
              </p>
            </div>

            <Form.Group controlId="formFile" className="mb-3">
              <Form.Label>
                {t("meters.toolsModal.uploadTab.fileInputLabel")}
              </Form.Label>
              <Form.Control
                type="file"
                accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                onChange={handleFileChange}
              />
            </Form.Group>

            {uploadSuccess && <Alert variant="success">{uploadSuccess}</Alert>}

            {uploadErrors.length > 0 && (
              <Alert variant="danger">
                <Alert.Heading>
                  {t("meters.toolsModal.uploadTab.errorAlert.title")}
                </Alert.Heading>
                <p>{t("meters.toolsModal.uploadTab.errorAlert.description")}</p>
                <hr />
                <ListGroup variant="flush">
                  {uploadErrors.map((err, index) => (
                    <ListGroup.Item
                      key={index}
                      className="bg-transparent border-0 px-0 py-1"
                    >
                      {err}
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              </Alert>
            )}

            <div className="d-grid">
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
              >
                {isUploading ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                    />{" "}
                    {t("meters.toolsModal.uploadTab.uploadingBtn")}
                  </>
                ) : (
                  t("meters.toolsModal.uploadTab.uploadBtn")
                )}
              </Button>
            </div>
          </div>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          {t("meters.toolsModal.closeBtn")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
