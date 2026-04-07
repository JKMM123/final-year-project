// AddReadingModal.tsx

import { useState, useEffect, useRef, useMemo } from "react";
import { Modal, Button, Form, FloatingLabel, Image } from "react-bootstrap";
import { useLocation, useNavigate } from "react-router-dom";
import { Formik } from "formik";
import * as Yup from "yup";
import { useTranslation } from "react-i18next";
import { useAlert } from "../../../hooks/useAlert";
import type { MeterForReading } from "../types";
import { createReadingWithImage } from "../readingsService";

interface AddReadingModalProps {
  show: boolean;
  meter: MeterForReading | null;
  handleClose: (needsRefresh: boolean) => void;
  preloadedImage?: File | null;
}

const AddReadingModal = ({
  show,
  meter,
  handleClose,
  preloadedImage,
}: AddReadingModalProps) => {
  const { t } = useTranslation();
  const { success, handleError } = useAlert();
  const navigate = useNavigate();
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const location = useLocation();

  useEffect(() => {
    // Cleanup object URL when component unmounts or preview changes
    return () => {
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  // Define the schema inside the component to access `t` and `meter` props.
  // useMemo ensures the schema is not redefined on every render.
  const AddReadingSchema = useMemo(() => {
    if (!meter) return Yup.object(); // Return a basic schema if meter is not available yet

    return Yup.object().shape({
      new_reading: Yup.number()
        .min(0, t("readings.addReadingModal.yup.readingNegative"))
        .min(
          meter.previous_reading ?? 0,
          t("readings.addReadingModal.yup.readingTooLow", {
            value: meter.previous_reading?.toFixed(2) ?? "0",
          })
        )
        .required(t("readings.addReadingModal.yup.newReadingRequired")),
      imageFile: Yup.mixed<File>()
        .required(t("readings.addReadingModal.yup.photoRequired"))
        .nullable()
        .test(
          "fileSize",
          t("readings.addReadingModal.yup.fileTooLarge", { size: 10 }),
          (value) =>
            !value || (value instanceof File && value.size <= 10 * 1024 * 1024)
        )
        .test(
          "fileType",
          t("readings.addReadingModal.yup.unsupportedFormat"),
          (value) =>
            !value || (value instanceof File && value.type === "image/jpeg")
        ),
    });
  }, [t, meter]);

  if (!meter) return null;

  const handleModalExit = () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
      setImagePreview(null);
    }
  };

  return (
    <Modal
      show={show}
      onHide={() => handleClose(false)}
      onExited={handleModalExit}
      centered
    >
      <Formik
        initialValues={{
          new_reading: "",
          imageFile: null as File | null,
        }}
        validationSchema={AddReadingSchema}
        onSubmit={async (values, { setSubmitting }) => {
          if (!values.imageFile) return;
          try {
            await createReadingWithImage(
              meter.meter_id,
              Number(values.new_reading),
              values.imageFile
            );
            success(t("readings.addReadingModal.messages.readingAddedSuccess"));
            handleClose(true);
          } catch (error) {
            handleError(error);
          } finally {
            setSubmitting(false);
          }
        }}
      >
        {({
          values,
          errors,
          touched,
          handleChange,
          handleSubmit,
          isSubmitting,
          setFieldValue,
          resetForm,
        }) => {
          // Effect to handle the preloaded image from the camera flow
          useEffect(() => {
            if (preloadedImage && show) {
              setFieldValue("imageFile", preloadedImage);
              const previewUrl = URL.createObjectURL(preloadedImage);
              setImagePreview(previewUrl);
            }
          }, [preloadedImage, show, setFieldValue]);

          // Effect to reset form when modal is hidden or meter changes
          useEffect(() => {
            if (show) {
              resetForm({
                values: {
                  new_reading: location.state?.newReadingValue || "",
                  imageFile: preloadedImage ?? null,
                },
              });
            }
          }, [show, meter?.meter_id, resetForm, preloadedImage]);

          const handleFileChange = (
            event: React.ChangeEvent<HTMLInputElement>
          ) => {
            const file = event.currentTarget.files?.[0] || null;
            setFieldValue("imageFile", file);
            if (imagePreview) URL.revokeObjectURL(imagePreview);
            setImagePreview(file ? URL.createObjectURL(file) : null);
          };

          const clearImage = () => {
            setFieldValue("imageFile", null);
            if (imagePreview) URL.revokeObjectURL(imagePreview);
            setImagePreview(null);
            if (fileInputRef.current) {
              fileInputRef.current.value = "";
            }
          };

          return (
            <Form noValidate onSubmit={handleSubmit}>
              <Modal.Header closeButton>
                <Modal.Title>
                  {t("readings.addReadingModal.addReadingFor", {
                    customerName: meter.customer_full_name,
                  })}
                </Modal.Title>
              </Modal.Header>
              <Modal.Body>
                <FloatingLabel
                  label={t("readings.addReadingModal.previousReadingLabel")}
                  className="mb-3"
                >
                  <Form.Control
                    readOnly
                    disabled
                    value={
                      meter.previous_reading?.toLocaleString() ??
                      t("common.notAvailable")
                    }
                  />
                </FloatingLabel>

                <FloatingLabel
                  label={t("readings.addReadingModal.newReadingLabel")}
                  className="mb-3"
                >
                  <Form.Control
                    type="number"
                    name="new_reading"
                    placeholder={t(
                      "readings.addReadingModal.enterNewReadingPlaceholder"
                    )}
                    value={values.new_reading}
                    onChange={handleChange}
                    isInvalid={touched.new_reading && !!errors.new_reading}
                    autoFocus
                  />
                  <Form.Control.Feedback type="invalid">
                    {errors.new_reading}
                  </Form.Control.Feedback>
                </FloatingLabel>

                <Form.Group className="mb-3">
                  <Form.Label>
                    {t("readings.addReadingModal.readingPhotoRequired")}
                  </Form.Label>
                  {imagePreview ? (
                    <div className="text-center">
                      <Image
                        src={imagePreview}
                        thumbnail
                        fluid
                        style={{ maxHeight: "200px" }}
                      />
                      <div className="mt-2">
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={clearImage}
                        >
                          {t("common.changePhoto")}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="d-grid gap-2">
                      <Button
                        variant="outline-primary"
                        onClick={() =>
                          navigate(`/readings/take-photo/${meter.meter_id}`, {
                            state: {
                              backgroundLocation:
                                location.state?.backgroundLocation || location,
                              from: location.pathname,
                              meter,
                              newReadingValue: values.new_reading,
                            },
                          })
                        }
                      >
                        <i className="bi bi-camera mx-2"></i>
                        {t("common.takePhoto")}
                      </Button>
                      <Button
                        variant="outline-secondary"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <i className="bi bi-upload mx-2"></i>
                        {t("common.uploadPhoto")}
                      </Button>
                    </div>
                  )}
                  <Form.Control
                    type="file"
                    name="imageFile"
                    accept="image/jpeg"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    isInvalid={touched.imageFile && !!errors.imageFile}
                    className="d-none"
                  />
                  <Form.Control.Feedback
                    type="invalid"
                    className={
                      touched.imageFile && errors.imageFile ? "d-block" : ""
                    }
                  >
                    {errors.imageFile as string}
                  </Form.Control.Feedback>
                </Form.Group>
              </Modal.Body>
              <Modal.Footer>
                <Button variant="secondary" onClick={() => handleClose(false)}>
                  {t("common.cancel")}
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? t("common.saving") : t("common.saveReading")}
                </Button>
              </Modal.Footer>
            </Form>
          );
        }}
      </Formik>
    </Modal>
  );
};

export default AddReadingModal;
