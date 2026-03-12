// src/features/users/components/UserModal.tsx

import { Modal, Button, Form, Alert } from "react-bootstrap";
import { useState, useMemo } from "react";
import { Formik } from "formik";
import * as Yup from "yup";
import { useTranslation } from "react-i18next";
import Select from "react-select";

import { useAlert } from "../../../hooks/useAlert";
import type { User, UserPayload } from "../types";
import { createUser, updateUser } from "../usersService";

// This validation schema is now a function that accepts the `t` function
// to provide translated error messages.
const getUserValidationSchema = (t: (key: string) => string) =>
  Yup.object().shape({
    username: Yup.string()
      .min(3, t("users.validation.usernameTooShort"))
      .required(t("users.validation.usernameRequired")),
    phone_number: Yup.string()
      .matches(/^[0-9]+$/, t("users.validation.phoneOnlyDigits"))
      .min(8, t("users.validation.phoneMinDigits"))
      .required(t("users.validation.phoneRequired")),
    role: Yup.string()
      .oneOf(["user", "admin"])
      .required(t("users.validation.roleRequired")),
  });

interface UserModalProps {
  user: User | null; // If user is null, it's an "Add" modal. Otherwise, "Edit".
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
}

const UserModal = ({ user, show, handleClose }: UserModalProps) => {
  const { t, i18n } = useTranslation();
  const { success, handleError } = useAlert();
  const [validationError, setValidationError] = useState<string | null>(null);

  const isEditMode = !!user;

  // useMemo ensures the schema is not recreated on every render, only when language changes.
  const UserSchema = useMemo(() => getUserValidationSchema(t), [t]);

  // Translate role options
  const roleOptions = useMemo(
    () => [
      { value: "admin", label: t("users.roles.admin") },
      { value: "user", label: t("users.roles.user") },
    ],
    [t]
  );

  const initialValues: UserPayload = {
    username: user?.username || "",
    phone_number: user?.phone_number || "",
    role: user?.role || "user",
  };

  return (
    <Modal show={show} onHide={() => handleClose(false)} centered>
      <Formik<UserPayload>
        initialValues={initialValues}
        validationSchema={UserSchema}
        onSubmit={async (values, { setSubmitting }) => {
          setValidationError(null);
          try {
            if (isEditMode && user) {
              await updateUser(user.user_id, values);
              success(t("users.messages.userUpdatedSuccess"));
            } else {
              await createUser(values);
              success(t("users.messages.userCreatedSuccess"));
            }
            handleClose(true); // Close modal and trigger a refresh
          } catch (error: any) {
            const fieldErrors = error.response?.data?.fieldErrors;
            const errorMessage =
              Array.isArray(fieldErrors) && fieldErrors.length > 0
                ? `${fieldErrors[0].field || t("common.field")} ${
                    fieldErrors[0].message || t("common.invalid")
                  }`
                : error.response?.data?.message ||
                  (isEditMode
                    ? t("users.messages.userUpdateFailed")
                    : t("users.messages.userCreateFailed"));
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
          dirty, // useful for edit mode
          isValid, // useful for edit mode
        }) => (
          <Form noValidate onSubmit={handleSubmit}>
            <Modal.Header closeButton>
              <Modal.Title>
                {isEditMode
                  ? t("users.editUserTitle", { username: user.username })
                  : t("users.addUserTitle")}
              </Modal.Title>
            </Modal.Header>

            <Modal.Body>
              {validationError && (
                <Alert variant="danger">{validationError}</Alert>
              )}

              <Form.Group className="mb-3" controlId="username">
                <Form.Label>{t("users.usernameLabel")}</Form.Label>
                <Form.Control
                  type="text"
                  name="username"
                  placeholder={t("users.usernamePlaceholder")}
                  value={values.username}
                  onChange={handleChange}
                  isInvalid={touched.username && !!errors.username}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.username}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="phone_number">
                <Form.Label>{t("users.phoneNumberLabel")}</Form.Label>
                <Form.Control
                  type="tel" // Use "tel" for phone numbers
                  name="phone_number"
                  placeholder={t("users.phoneNumberPlaceholder")}
                  value={values.phone_number}
                  onChange={handleChange}
                  isInvalid={touched.phone_number && !!errors.phone_number}
                  style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.phone_number}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="role">
                <Form.Label>{t("users.roleLabel")}</Form.Label>
                <Select
                  name="role"
                  options={roleOptions}
                  isSearchable={false}
                  placeholder={t("users.rolePlaceholder")}
                  value={
                    roleOptions.find(
                      (option) => option.value === values.role
                    ) || null
                  }
                  onChange={(option) =>
                    handleChange({
                      target: {
                        name: "role",
                        value: option ? option.value : "",
                      },
                    })
                  }
                  className={touched.role && errors.role ? "is-invalid" : ""}
                  // Add this for better screen reader support
                  aria-invalid={touched.role && !!errors.role}
                  aria-errormessage="role-error"
                />
                {touched.role && errors.role && (
                  <div id="role-error" className="invalid-feedback d-block">
                    {errors.role}
                  </div>
                )}
              </Form.Group>
            </Modal.Body>

            <Modal.Footer>
              <Button variant="secondary" onClick={() => handleClose(false)}>
                {t("common.cancel")}
              </Button>
              <Button
                variant="primary"
                type="submit"
                disabled={isSubmitting || (isEditMode && (!dirty || !isValid))}
              >
                {isSubmitting
                  ? t("common.saving")
                  : isEditMode
                  ? t("common.saveChanges")
                  : t("users.createUser")}
              </Button>
            </Modal.Footer>
          </Form>
        )}
      </Formik>
    </Modal>
  );
};

export default UserModal;
