import { Form, FloatingLabel } from "react-bootstrap";
import { useField } from "formik"; // Assuming Formik for form handling

interface InputProps {
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  [x: string]: any; // for other props
}

// Example using Formik's useField hook
export const Input = ({ label, ...props }: InputProps) => {
  const [field, meta] = useField(props.name);
  return (
    <FloatingLabel
      controlId={props.id || props.name}
      label={label}
      className="mb-3"
    >
      <Form.Control
        {...field}
        {...props}
        isInvalid={meta.touched && !!meta.error}
        isValid={meta.touched && !meta.error}
      />
      <Form.Control.Feedback type="invalid">{meta.error}</Form.Control.Feedback>
    </FloatingLabel>
  );
};
