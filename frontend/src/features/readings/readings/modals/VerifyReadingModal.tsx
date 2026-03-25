// src/features/readings/components/VerifyReadingModal.tsx
import { useState, useEffect } from "react";
import {
  Modal,
  Button,
  Form,
  FloatingLabel,
  Row,
  Col,
  Spinner,
  Alert,
  Image,
} from "react-bootstrap";
import { Formik } from "formik";
import * as Yup from "yup";
import { useTranslation } from "react-i18next"; // Import useTranslation
import { useAlert } from "../../../hooks/useAlert";
import type { Reading } from "../types";
import { verifyReading, getReadingDetails } from "../readingsService";

interface VerifyReadingModalProps {
  show: boolean;
  reading: Reading | null;
  handleClose: (needsRefresh: boolean) => void;
}

const VerifyReadingModal = ({
  show,
  reading,
  handleClose,
}: VerifyReadingModalProps) => {
  const { t } = useTranslation(); // Initialize the translation function
  const { success, handleError } = useAlert();

  const [detailedReading, setDetailedReading] = useState<Reading | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const viewMode = reading?.status === "verified";

  useEffect(() => {
    if (show && reading?.reading_id) {
      const fetchDetails = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const data = await getReadingDetails(reading.reading_id);
          setDetailedReading(data);
        } catch (err: any) {
          setError(t("readings.verifyModal.fetchError")); // Use translated error
          handleError(err);
        } finally {
          setIsLoading(false);
        }
      };

      fetchDetails();
    } else {
      setDetailedReading(null);
      setIsLoading(false);
      setError(null);
    }
  }, [show, reading, handleError, t]); // Add 't' to dependency array

  if (!reading) return null;

  // Define the validation schema using the fetched detailed data
  const VerifyReadingSchema = detailedReading
    ? Yup.object().shape({
        current_reading: Yup.number()
          .min(
            detailedReading.previous_reading,
            // Use translated validation message with interpolation
            t("readings.verifyModal.validation.min", {
              value: detailedReading.previous_reading.toFixed(2),
            })
          )
          .required(t("readings.verifyModal.validation.required")),
      })
    : Yup.object();

  return (
    <Modal show={show} onHide={() => handleClose(false)} centered size="lg">
      <Modal.Header closeButton>
        <Modal.Title>
          {t("readings.verifyModal.title", {
            customerName: reading.customer_full_name,
          })}
        </Modal.Title>
      </Modal.Header>

      {isLoading && (
        <Modal.Body
          className="d-flex justify-content-center align-items-center"
          style={{ minHeight: "300px" }}
        >
          <Spinner animation="border" role="status">
            <span className="visually-hidden">
              {t("readings.verifyModal.loadingDetails")}
            </span>
          </Spinner>
        </Modal.Body>
      )}

      {error && !isLoading && (
        <Modal.Body>
          <Alert variant="danger">{error}</Alert>
          <div className="d-flex justify-content-end">
            <Button variant="secondary" onClick={() => handleClose(false)}>
              {t("common.close")}
            </Button>
          </div>
        </Modal.Body>
      )}

      {!isLoading && !error && detailedReading && (
        <Formik
          initialValues={{ current_reading: detailedReading.current_reading }}
          validationSchema={VerifyReadingSchema}
          onSubmit={async (values, { setSubmitting }) => {
            try {
              await verifyReading(detailedReading.reading_id, {
                current_reading: values.current_reading,
                status: "verified",
              });
              success(t("readings.verifyModal.successMessage"));
              handleClose(true);
            } catch (err) {
              handleError(err);
            } finally {
              setSubmitting(false);
            }
          }}
          enableReinitialize
        >
          {({
            values,
            errors,
            touched,
            handleChange,
            handleSubmit,
            isSubmitting,
            isValid,
          }) => (
            <Form onSubmit={handleSubmit}>
              <Modal.Body>
                <Row>
                  <Col md={6}>
                    <h5 className="mb-3">
                      {t("readings.verifyModal.scannedImageTitle")}
                    </h5>
                    {detailedReading.reading_url ? (
                      <>
                        <Image
                          src={detailedReading.reading_url}
                          alt={t("readings.verifyModal.imageAlt", {
                            customerName: detailedReading.customer_full_name,
                          })}
                          fluid
                          rounded
                          className="border"
                          style={{ cursor: "pointer" }}
                          onClick={() => setShowPreview(true)}
                        />
                        <Modal
                          show={showPreview}
                          onHide={() => setShowPreview(false)}
                          size="lg"
                          centered
                        >
                          <Modal.Body className="d-flex justify-content-center align-items-center">
                            <Image
                              src={detailedReading.reading_url}
                              alt={t("readings.verifyModal.previewAlt")}
                              fluid
                              rounded
                            />
                          </Modal.Body>
                        </Modal>
                      </>
                    ) : (
                      <div className="d-flex align-items-center justify-content-center h-100 bg-light border rounded text-muted p-4">
                        <p className="text-center mb-0">
                          {t("readings.verifyModal.noImage")}
                        </p>
                      </div>
                    )}
                  </Col>

                  <Col md={6}>
                    <h5 className="mb-3">
                      {t("readings.verifyModal.verificationTitle")}
                    </h5>
                    <p className="text-muted">
                      <strong>{t("readings.verifyModal.customerLabel")}</strong>{" "}
                      {detailedReading.customer_full_name} <br />
                    </p>
                    <hr />
                    <FloatingLabel
                      label={t("readings.verifyModal.previousReadingLabel")}
                      className="mb-3"
                    >
                      <Form.Control
                        readOnly
                        disabled
                        value={detailedReading.previous_reading.toFixed(2)}
                      />
                    </FloatingLabel>
                    <FloatingLabel
                      label={t("readings.verifyModal.currentReadingLabel")}
                    >
                      <Form.Control
                        type="number"
                        name="current_reading"
                        value={values.current_reading}
                        onChange={handleChange}
                        isInvalid={
                          touched.current_reading && !!errors.current_reading
                        }
                        step="0.01"
                        readOnly={viewMode}
                        disabled={viewMode}
                      />
                      {!viewMode && (
                        <Form.Control.Feedback type="invalid">
                          {errors.current_reading}
                        </Form.Control.Feedback>
                      )}
                    </FloatingLabel>
                  </Col>
                </Row>
              </Modal.Body>
              <Modal.Footer>
                {viewMode ? (
                  <Button
                    variant="secondary"
                    onClick={() => handleClose(false)}
                  >
                    {t("common.close")}
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="secondary"
                      onClick={() => handleClose(false)}
                      disabled={isSubmitting}
                    >
                      {t("common.cancel")}
                    </Button>
                    <Button
                      variant="success"
                      type="submit"
                      disabled={!isValid || isSubmitting}
                    >
                      {isSubmitting
                        ? t("readings.verifyModal.verifyingButton")
                        : t("readings.verifyModal.verifyButton")}
                    </Button>
                  </>
                )}
              </Modal.Footer>
            </Form>
          )}
        </Formik>
      )}
    </Modal>
  );
};

export default VerifyReadingModal;
