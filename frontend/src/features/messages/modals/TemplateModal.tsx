// src/pages/Messages/modals/TemplateModal.tsx

import { useRef, useMemo } from "react";
import { Modal, Button, Form, Badge } from "react-bootstrap";
import { Formik } from "formik";
import * as Yup from "yup";
import { useTranslation } from "react-i18next";
import { useAlert } from "../../../hooks/useAlert";
import type { Template, CreateTemplatePayload } from "../types";
import { createTemplate, updateTemplate } from "../messagesService";
import "./TemplateModal.css";

interface TemplateModalProps {
  template: Template | null;
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
}

export const TemplateModal = ({
  template,
  show,
  handleClose,
}: TemplateModalProps) => {
  const { t } = useTranslation();
  const { success, handleError } = useAlert();
  const isEditMode = !!template;
  const messageInputRef = useRef<HTMLTextAreaElement>(null);

  // Use useMemo to avoid re-creating the object on every render
  const placeholders = useMemo(
    () => ({
      [t("messages.placeholders.customerData")]: [
        "{{customer_full_name}}",
        "{{customer_phone_number}}",
        "{{address}}",
        "{{area_name}}",
      ],
      [t("messages.placeholders.billData")]: [
        "{{amount_due_lbp}}",
        "{{amount_due_usd}}",
        "{{due_date}}",
      ],
      [t("messages.placeholders.meterData")]: [
        "{{amperage}}",
        "{{fixed_fee}}",
        "{{activation_fee}}",
      ],
    }),
    [t]
  );

  // Moved schema inside the component to use the `t` function
  const TemplateSchema = useMemo(
    () =>
      Yup.object().shape({
        name: Yup.string().required(
          t("messages.validation.templateNameRequired")
        ),
        message: Yup.string().required(
          t("messages.validation.messageRequired")
        ),
      }),
    [t]
  );

  const handlePlaceholderClick = (
    text: string,
    setFieldValue: (field: string, value: any) => void
  ) => {
    const textarea = messageInputRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const currentValue = textarea.value;

    const newValue =
      currentValue.substring(0, start) + text + currentValue.substring(end);

    setFieldValue("message", newValue);

    // Move cursor to after the inserted text
    requestAnimationFrame(() => {
      textarea.selectionStart = textarea.selectionEnd = start + text.length;
      textarea.focus();
    });
  };

  return (
    <Modal show={show} onHide={() => handleClose(false)} size="lg" centered>
      <Formik<CreateTemplatePayload>
        enableReinitialize
        initialValues={{
          name: template?.name || "",
          message: template?.message || "",
        }}
        validationSchema={TemplateSchema}
        onSubmit={async (values, { setSubmitting }) => {
          try {
            if (isEditMode && template) {
              await updateTemplate(template.template_id, values);
              success(t("messages.alerts.templateUpdated"));
            } else {
              await createTemplate(values);
              success(t("messages.alerts.templateCreated"));
            }
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
          handleSubmit,
          handleChange,
          handleBlur,
          setFieldValue,
          isSubmitting,
          isValid,
          dirty,
        }) => (
          <Form noValidate onSubmit={handleSubmit}>
            <Modal.Header closeButton>
              <Modal.Title>
                {isEditMode
                  ? t("messages.modals.editTemplate")
                  : t("messages.modals.createNewTemplate")}
              </Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <Form.Group className="mb-4">
                <Form.Label>
                  {t("messages.modals.templateNameLabel")}
                </Form.Label>
                <Form.Control
                  type="text"
                  name="name"
                  value={values.name}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  isInvalid={touched.name && !!errors.name}
                  placeholder={t("messages.modals.templateNamePlaceholder")}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.name}
                </Form.Control.Feedback>
              </Form.Group>

              <div className="mb-3">
                <strong>{t("messages.modals.placeholdersTitle")}</strong> (
                {t("messages.modals.dragInstruction")})
                <div className="placeholder-container">
                  {Object.entries(placeholders).map(([category, items]) => (
                    <div key={category} className="mt-2">
                      <p className="mb-1 small text-muted">{category}</p>
                      <div className="d-flex flex-wrap gap-2">
                        {items.map((item) => (
                          <Badge
                            key={item}
                            pill
                            bg="primary"
                            className="placeholder-badge"
                            style={{
                              fontSize: "0.95rem",
                              padding: "0.4em 0.5em",
                              cursor: "pointer",
                              userSelect: "none",
                            }}
                            onClick={() =>
                              handlePlaceholderClick(item, setFieldValue)
                            }
                          >
                            {item}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <Form.Group>
                <Form.Label>{t("messages.modals.messageLabel")}</Form.Label>
                <div className="message-editor">
                  <div
                    className="message-highlighter"
                    dangerouslySetInnerHTML={{
                      __html:
                        values.message.replace(
                          /({{.*?}})/g,
                          "<strong>$1</strong>"
                        ) + "<br/>",
                    }}
                  />
                  <Form.Control
                    as="textarea"
                    ref={messageInputRef}
                    name="message"
                    rows={6}
                    value={values.message}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    onScroll={(e) => {
                      const target = e.currentTarget;
                      const highlighter =
                        target.previousElementSibling as HTMLDivElement;
                      if (highlighter) {
                        highlighter.scrollTop = target.scrollTop;
                        highlighter.scrollLeft = target.scrollLeft;
                      }
                    }}
                    isInvalid={touched.message && !!errors.message}
                    placeholder={t("messages.modals.messagePlaceholder")}
                    spellCheck={false}
                    className="message-textarea"
                  />
                </div>
                <Form.Control.Feedback type="invalid">
                  {errors.message}
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
                disabled={isSubmitting || !isValid || (isEditMode && !dirty)}
              >
                {isSubmitting
                  ? t("common.saving")
                  : isEditMode
                  ? t("common.saveChanges")
                  : t("messages.modals.createTemplateButton")}
              </Button>
            </Modal.Footer>
          </Form>
        )}
      </Formik>
    </Modal>
  );
};
