import { Form, Button } from "react-bootstrap";
import { Formik } from "formik";
import * as Yup from "yup";
import type { Area, AreaPayload } from "./types";

interface EditableAreaRowProps {
  area: Area;
  onSave: (payload: AreaPayload) => Promise<void>;
  onCancel: () => void;
}

const EditAreaSchema = Yup.object().shape({
  area_name: Yup.string()
    .matches(
      /^[\u0600-\u06FFa-zA-Z\s]*$/,
      "Only Arabic, English letters and spaces are allowed"
    )
    .required("Area name is required"),
  elevation: Yup.number()
    .positive("Must be a positive number")
    .required("Elevation is required"),
});

export const EditableAreaRow = ({
  area,
  onSave,
  onCancel,
}: EditableAreaRowProps) => {
  return (
    <Formik<AreaPayload>
      initialValues={{ area_name: area.area_name, elevation: area.elevation }}
      validationSchema={EditAreaSchema}
      onSubmit={async (values, { setSubmitting }) => {
        await onSave(values);
        setSubmitting(false);
      }}
    >
      {({
        values,
        errors,
        handleChange,
        handleSubmit,
        isSubmitting,
        dirty,
        isValid,
      }) => (
        <tr className="table-info">
          <td>
            <Form.Control
              type="text"
              size="sm"
              name="area_name"
              value={values.area_name}
              onChange={handleChange}
              isInvalid={!!errors.area_name}
            />
          </td>
          <td>
            <Form.Control
              type="number"
              size="sm"
              name="elevation"
              value={values.elevation}
              onChange={handleChange}
              isInvalid={!!errors.elevation}
            />
          </td>
          <td>
            <div className="d-flex gap-2">
              <Button
                size="sm"
                variant="success"
                onClick={() => handleSubmit()}
                disabled={!dirty || !isValid || isSubmitting}
              >
                <i className="bi bi-check-lg"></i>
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                <i className="bi bi-x-lg"></i>
              </Button>
            </div>
          </td>
        </tr>
      )}
    </Formik>
  );
};
