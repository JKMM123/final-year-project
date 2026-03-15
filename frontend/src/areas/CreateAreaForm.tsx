import { useMemo } from "react";
import {
  Form,
  Button,
  Row,
  Col,
  InputGroup,
  OverlayTrigger,
  Tooltip,
} from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { Formik } from "formik";
import * as Yup from "yup";
import { useAlert } from "../../hooks/useAlert";
import type { AreaPayload } from "./types";
import { createArea } from "./areasService";

interface CreateAreaFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export const CreateAreaForm = ({
  onSuccess,
  onCancel,
}: CreateAreaFormProps) => {
  const { t } = useTranslation();
  const { success, handleError } = useAlert();

  // Define the schema inside the component to access the `t` function
  const CreateAreaSchema = useMemo(() => {
    return Yup.object().shape({
      area_name: Yup.string()
        .matches(
          /^[\u0600-\u06FFa-zA-Z\s]*$/,
          t("areas.validation.namePattern")
        )
        .required(t("areas.validation.nameRequired")),

      elevation: Yup.number()
        .transform((value, originalValue) =>
          originalValue === "" ? undefined : value
        )
        .typeError(t("areas.validation.elevationNumber"))
        .positive(t("areas.validation.elevationPositive"))
        .required(t("areas.validation.elevationRequired")),
    });
  }, [t]);

  return (
    <Formik<AreaPayload>
      initialValues={{ area_name: "", elevation: "" as unknown as number }}
      validationSchema={CreateAreaSchema}
      onSubmit={async (values, { setSubmitting, resetForm }) => {
        try {
          await createArea({ ...values, elevation: Number(values.elevation) });
          success(t("areas.notifications.createSuccess"));
          resetForm();
          onSuccess();
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
      }) => (
        <Form
          onSubmit={handleSubmit}
          className="p-3 border bg-light rounded mb-3"
        >
          <Row className="align-items-start g-3">
            <Col md={5}>
              <Form.Control
                type="text"
                name="area_name"
                placeholder={t("areas.createForm.placeholders.name")}
                value={values.area_name}
                onChange={handleChange}
                isInvalid={touched.area_name && !!errors.area_name}
              />
              <Form.Control.Feedback type="invalid">
                {errors.area_name}
              </Form.Control.Feedback>
            </Col>
            <Col md={4}>
              <InputGroup>
                <Form.Control
                  type="number"
                  name="elevation"
                  placeholder={t("areas.createForm.placeholders.elevation")}
                  value={values.elevation}
                  onChange={handleChange}
                  isInvalid={touched.elevation && !!errors.elevation}
                />
                <OverlayTrigger
                  placement="top"
                  overlay={
                    <Tooltip>{t("areas.createForm.elevationTooltip")}</Tooltip>
                  }
                >
                  <Button
                    variant="outline-secondary"
                    className="px-2 py-0 d-flex align-items-center"
                  >
                    <i className="bi bi-info-circle"></i>
                  </Button>
                </OverlayTrigger>
                <Form.Control.Feedback type="invalid">
                  {errors.elevation}
                </Form.Control.Feedback>
              </InputGroup>
            </Col>
            <Col md={3} className="d-flex justify-content-end gap-2">
              <Button
                variant="secondary"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                {t("common.cancel")}
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? t("common.creating") : t("common.create")}
              </Button>
            </Col>
          </Row>
        </Form>
      )}
    </Formik>
  );
};
