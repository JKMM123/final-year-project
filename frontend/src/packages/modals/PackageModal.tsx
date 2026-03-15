import {
  Modal,
  Button,
  Form,
  Alert,
  OverlayTrigger,
  Tooltip,
} from "react-bootstrap";
import { useState, type FC } from "react";
import { useTranslation } from "react-i18next";
import { Formik } from "formik";
import * as Yup from "yup";
import { NumericFormat } from "react-number-format";

import { useAlert } from "../../../hooks/useAlert";
import type { Package, PackagePayload, PackageFormValues } from "../types";
import { createPackage, updatePackage } from "../packagesService";

interface PackageModalProps {
  pkg: Package | null; // If pkg is provided, it's an edit modal. If null, it's an add modal.
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
}

const InfoTooltip: FC<{ text: string }> = ({ text }) => (
  <OverlayTrigger placement="top" overlay={<Tooltip>{text}</Tooltip>}>
    <i className="bi bi-info-circle mx-2 text-secondary"></i>
  </OverlayTrigger>
);

// A single schema for both Add and Edit, with translated validation messages
const getPackageSchema = (t: (key: string) => string) =>
  Yup.object().shape({
    amperage: Yup.number()
      .positive(t("packages.validation.positive"))
      .required(t("packages.validation.amperageRequired")),
    activation_fee: Yup.number()
      .min(0, t("packages.validation.negative"))
      .required(t("packages.validation.activationFeeRequired")),
    fixed_fee: Yup.number()
      .min(0, t("packages.validation.negative"))
      .required(t("packages.validation.fixedFeeRequired")),
  });

const PackageModal = ({ pkg, show, handleClose }: PackageModalProps) => {
  const { t } = useTranslation();
  const { success, handleError } = useAlert();
  const [validationError, setValidationError] = useState<string | null>(null);

  const isEditMode = !!pkg;
  const NumericFormControl = (props: any) => <Form.Control {...props} />;

  const initialValues: PackageFormValues = {
    amperage: isEditMode ? pkg.amperage : "",
    activation_fee: isEditMode ? pkg.activation_fee : "",
    fixed_fee: isEditMode ? pkg.fixed_fee : "",
  };

  return (
    <Modal show={show} onHide={() => handleClose(false)} centered>
      <Formik<PackageFormValues>
        initialValues={initialValues}
        validationSchema={getPackageSchema(t)}
        enableReinitialize // Important for re-populating form when a different item is edited
        onSubmit={async (values, { setSubmitting }) => {
          setValidationError(null);
          try {
            const payload: PackagePayload = {
              amperage: Number(values.amperage),
              activation_fee: Number(values.activation_fee),
              fixed_fee: Number(values.fixed_fee),
            };

            if (isEditMode && pkg) {
              await updatePackage(pkg.package_id, payload);
              success(t("packages.messages.packageUpdatedSuccess"));
            } else {
              await createPackage(payload);
              success(t("packages.messages.packageCreatedSuccess"));
            }
            handleClose(true);
          } catch (error: any) {
            const fieldErrors = error.response?.data?.fieldErrors;
            const errorMessage =
              Array.isArray(fieldErrors) && fieldErrors.length > 0
                ? `${fieldErrors[0].field || "Field"} ${
                    fieldErrors[0].message || "Invalid"
                  }`
                : error.response?.data?.message ||
                  (isEditMode
                    ? t("packages.messages.packageUpdateFailed")
                    : t("packages.messages.packageCreateFailed"));

            setValidationError(errorMessage);
            handleError(errorMessage);
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
          dirty,
          isValid,
        }) => (
          <Form onSubmit={handleSubmit}>
            <Modal.Header closeButton>
              <Modal.Title>
                {isEditMode
                  ? t("packages.editTitle", { amperage: pkg.amperage })
                  : t("packages.addTitle")}
              </Modal.Title>
            </Modal.Header>
            <Modal.Body>
              {validationError && (
                <Alert variant="danger">{validationError}</Alert>
              )}

              <Form.Group className="mb-3" controlId="amperage">
                <Form.Label>
                  {t("packages.amperageLabel")}
                  <InfoTooltip text={t("packages.tooltips.amperage")} />
                </Form.Label>
                <Form.Control
                  type="number"
                  name="amperage"
                  placeholder={t("packages.enterAmperage")}
                  value={values.amperage ?? ""}
                  onChange={handleChange}
                  isInvalid={touched.amperage && !!errors.amperage}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.amperage}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="activation_fee">
                <Form.Label>
                  {t("packages.activationFeeLabel")}
                  <InfoTooltip text={t("packages.tooltips.activation_fee")} />
                </Form.Label>
                <NumericFormat
                  customInput={NumericFormControl}
                  thousandSeparator
                  allowNegative={false}
                  name="activation_fee"
                  placeholder={t("packages.enterActivationFee")}
                  value={values.activation_fee ?? ""}
                  onValueChange={(val: any) =>
                    setFieldValue("activation_fee", val.floatValue ?? "")
                  }
                  isInvalid={touched.activation_fee && !!errors.activation_fee}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.activation_fee}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="fixed_fee">
                <Form.Label>
                  {t("packages.fixedFeeLabel")}
                  <InfoTooltip text={t("packages.tooltips.fixed_fee")} />
                </Form.Label>
                <NumericFormat
                  customInput={NumericFormControl}
                  thousandSeparator
                  allowNegative={false}
                  name="fixed_fee"
                  placeholder={t("packages.enterFixedFee")}
                  value={values.fixed_fee ?? ""}
                  onValueChange={(val: any) =>
                    setFieldValue("fixed_fee", val.floatValue ?? "")
                  }
                  isInvalid={touched.fixed_fee && !!errors.fixed_fee}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.fixed_fee}
                </Form.Control.Feedback>
              </Form.Group>
            </Modal.Body>

            <Modal.Footer>
              <Button variant="secondary" onClick={() => handleClose(false)}>
                {t("common.cancel")}
              </Button>
              <Button
                variant="primary"
                type="submit"
                disabled={
                  isEditMode ? !dirty || !isValid || isSubmitting : isSubmitting
                }
              >
                {isSubmitting
                  ? t("common.saving")
                  : isEditMode
                  ? t("common.saveChanges")
                  : t("packages.createPackage")}
              </Button>
            </Modal.Footer>
          </Form>
        )}
      </Formik>
    </Modal>
  );
};
export default PackageModal;
