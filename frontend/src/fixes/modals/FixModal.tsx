// src/features/fixes/FixModal.tsx

import { useState, useEffect, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Modal,
  Form,
  Button,
  ListGroup,
  Spinner,
  Alert,
} from "react-bootstrap";
import { Formik } from "formik";
import * as Yup from "yup";
import { debounce } from "lodash";
import { NumericFormat } from "react-number-format";

import type { Fix, FixCreatePayload, FixUpdatePayload, Meter } from "../types";
import { createFix, updateFix, getMeters } from "../fixesService";
import { useAlert } from "../../../hooks/useAlert";

interface FixModalProps {
  show: boolean;
  onHide: () => void;
  onSuccess: () => void;
  fix?: Fix | null; // If provided, modal is in "edit" mode
}

const getTodayString = () => new Date().toISOString().split("T")[0];

const NumericFormControl = (props: any) => <Form.Control {...props} />;

export const FixModal = ({ show, onHide, onSuccess, fix }: FixModalProps) => {
  const { t, i18n } = useTranslation();
  const { success, handleError } = useAlert();
  const isEditMode = !!fix;

  // State for Meter Search (Create Mode Only)
  const [meterQuery, setMeterQuery] = useState("");
  const [meterResults, setMeterResults] = useState<Meter[]>([]);
  const [isSearchingMeters, setIsSearchingMeters] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedMeterName, setSelectedMeterName] = useState("");

  // When modal is hidden, reset create mode's specific state
  useEffect(() => {
    if (!show && !isEditMode) {
      setMeterQuery("");
      setMeterResults([]);
      setSelectedMeterName("");
      setHasSearched(false);
    }
  }, [show, isEditMode]);

  const initialValues = useMemo(() => {
    if (isEditMode && fix) {
      return {
        fix_date: fix.fix_date,
        description: fix.description,
        cost: fix.cost,
      };
    }
    return {
      meter_id: "",
      fix_date: getTodayString(),
      description: "",
      cost: "" as unknown as number,
    };
  }, [fix, isEditMode]);

  const validationSchema = useMemo(
    () =>
      Yup.object().shape({
        meter_id: isEditMode
          ? Yup.string()
          : Yup.string().required(t("fixes.validation.meterRequired")),
        fix_date: Yup.date().required(t("fixes.validation.dateRequired")),
        description: Yup.string().required(
          t("fixes.validation.descriptionRequired")
        ),
        cost: Yup.number()
          .typeError(t("fixes.validation.costType"))
          .positive(t("fixes.validation.costPositive"))
          .required(t("fixes.validation.costRequired")),
      }),
    [t, isEditMode]
  );

  const debouncedMeterSearch = useMemo(
    () =>
      debounce(async (query: string) => {
        if (query.trim().length < 1) {
          setMeterResults([]);
          setIsSearchingMeters(false);
          setHasSearched(false);
          return;
        }
        setIsSearchingMeters(true);
        setHasSearched(true);
        try {
          const response = await getMeters({ page: 1, limit: 6, query });
          setMeterResults(response.items);
        } catch (error) {
          console.error("Failed to search for meters:", error);
          handleError(t("fixes.searchError"));
          setMeterResults([]);
        } finally {
          setIsSearchingMeters(false);
        }
      }, 500),
    [handleError, t]
  );

  useEffect(() => {
    if (!isEditMode) {
      debouncedMeterSearch(meterQuery);
      return () => debouncedMeterSearch.cancel();
    }
  }, [meterQuery, debouncedMeterSearch, isEditMode]);

  const handleMeterSelect = useCallback(
    (meter: Meter, setFieldValue: Function) => {
      setFieldValue("meter_id", meter.meter_id);
      setSelectedMeterName(meter.customer_full_name);
      setMeterQuery("");
      setMeterResults([]);
      setHasSearched(false);
    },
    []
  );

  const inputValue = selectedMeterName || meterQuery;

  const spinnerStyle: React.CSSProperties = {
    position: "absolute",
    top: "10px",
    [i18n.dir() === "rtl" ? "left" : "right"]: "10px",
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting }) => {
          try {
            const payload = { ...values, cost: Number(values.cost) };
            if (isEditMode && fix) {
              await updateFix(fix.fix_id, payload as FixUpdatePayload);
              success(t("fixes.updateSuccess"));
            } else {
              await createFix(payload as FixCreatePayload);
              success(t("fixes.createSuccess"));
            }
            onSuccess(); // This also closes the modal via the parent
          } catch (error) {
            handleError(error);
          } finally {
            setSubmitting(false);
          }
        }}
        enableReinitialize // Important for edit mode to update initialValues
      >
        {({
          values,
          errors,
          touched,
          handleChange,
          handleSubmit,
          isSubmitting,
          setFieldValue,
        }) => (
          <Form onSubmit={handleSubmit}>
            <Modal.Header closeButton>
              <Modal.Title>
                {t(isEditMode ? "fixes.editTitle" : "fixes.addTitle")}
              </Modal.Title>
            </Modal.Header>

            <Modal.Body>
              {isEditMode && fix ? (
                <Form.Group className="mb-3">
                  <Form.Label>{t("fixes.customerNameLabel")}</Form.Label>
                  <Form.Control
                    type="text"
                    value={fix.customer_name}
                    disabled
                    readOnly
                  />
                </Form.Group>
              ) : (
                <Form.Group className="mb-3" controlId="meter_id">
                  <Form.Label>{t("fixes.customerMeterLabel")}</Form.Label>
                  <div style={{ position: "relative" }}>
                    <Form.Control
                      type="text"
                      placeholder={t("fixes.searchPlaceholder")}
                      value={inputValue}
                      onChange={(e) => {
                        setSelectedMeterName("");
                        setMeterQuery(e.target.value);
                        if (e.target.value === "") {
                          setFieldValue("meter_id", "");
                        }
                      }}
                      isInvalid={touched.meter_id && !!errors.meter_id}
                      autoComplete="off"
                    />
                    {isSearchingMeters && (
                      <Spinner
                        animation="border"
                        size="sm"
                        style={spinnerStyle}
                      />
                    )}
                    {(meterResults.length > 0 ||
                      (hasSearched && !isSearchingMeters)) && (
                      <ListGroup
                        style={{
                          position: "absolute",
                          zIndex: 1000,
                          width: "100%",
                        }}
                      >
                        {meterResults.length > 0 ? (
                          meterResults.map((meter) => (
                            <ListGroup.Item
                              key={meter.meter_id}
                              action
                              onClick={() =>
                                handleMeterSelect(meter, setFieldValue)
                              }
                            >
                              {meter.customer_full_name}
                            </ListGroup.Item>
                          ))
                        ) : (
                          <ListGroup.Item disabled>
                            {t("fixes.noCustomersFound")}
                          </ListGroup.Item>
                        )}
                      </ListGroup>
                    )}
                    <Form.Control.Feedback type="invalid">
                      {errors.meter_id as string}
                    </Form.Control.Feedback>
                  </div>
                  {selectedMeterName &&
                    !meterResults.length &&
                    !isSearchingMeters && (
                      <Alert variant="info" className="mt-2 py-1">
                        {t("fixes.selected")}:{" "}
                        <strong>{selectedMeterName}</strong>
                      </Alert>
                    )}
                </Form.Group>
              )}

              {/* Common Fields */}
              <Form.Group className="mb-3" controlId="fix_date">
                <Form.Label>{t("fixes.fixDateLabel")}</Form.Label>
                <Form.Control
                  type="date"
                  name="fix_date"
                  value={values.fix_date}
                  onChange={handleChange}
                  isInvalid={touched.fix_date && !!errors.fix_date}
                  style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.fix_date}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="description">
                <Form.Label>{t("fixes.descriptionLabel")}</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  name="description"
                  value={values.description}
                  onChange={handleChange}
                  isInvalid={touched.description && !!errors.description}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.description}
                </Form.Control.Feedback>
              </Form.Group>

              <Form.Group className="mb-3" controlId="cost">
                <Form.Label>{t("fixes.costLabel")}</Form.Label>
                <NumericFormat
                  customInput={NumericFormControl}
                  thousandSeparator
                  allowNegative={false}
                  name="cost"
                  placeholder={t("fixes.costPlaceholder")}
                  value={values.cost}
                  onValueChange={(val) =>
                    setFieldValue("cost", val.floatValue ?? "")
                  }
                  isInvalid={touched.cost && !!errors.cost}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.cost as string}
                </Form.Control.Feedback>
              </Form.Group>
            </Modal.Body>

            <Modal.Footer>
              <Button variant="secondary" onClick={onHide}>
                {t("common.cancel")}
              </Button>
              <Button variant="primary" type="submit" disabled={isSubmitting}>
                {isSubmitting
                  ? t(isEditMode ? "fixes.saving" : "fixes.creating")
                  : t(isEditMode ? "fixes.saveChanges" : "fixes.createFix")}
              </Button>
            </Modal.Footer>
          </Form>
        )}
      </Formik>
    </Modal>
  );
};
