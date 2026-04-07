import { useEffect, useMemo, useState, type FC } from "react";
import {
  Modal,
  Button,
  Form,
  Col,
  Row,
  OverlayTrigger,
  Tooltip,
} from "react-bootstrap";
import { Formik, type FormikErrors, type FormikTouched } from "formik";
import * as Yup from "yup";
import Select from "react-select";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { useAlert } from "../../../hooks/useAlert";
import type { Meter, MeterCreatePayload, MeterUpdatePayload } from "../types";
import type { Area } from "../../areas/types";
import type { Package } from "../../packages/types";
import { createMeter, updateMeter } from "../metersService";
import { getPackages } from "../../packages/packagesService";
import { useNavigate } from "react-router-dom";

// Helper component for tooltips, now using i18n
const InfoTooltip: FC<{ text: string }> = ({ text }) => (
  <OverlayTrigger placement="top" overlay={<Tooltip>{text}</Tooltip>}>
    {/* Using margin-start for RTL compatibility */}
    <i className="bi bi-info-circle ms-1 text-secondary"></i>
  </OverlayTrigger>
);

interface MeterFormModalProps {
  meter: Meter | null; // If null, it's "Add" mode; otherwise, "Edit" mode.
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
  areas: Area[];
}

// Moved Yup schemas into functions to pass the `t` function for translations
const getAddMeterSchema = (t: TFunction) =>
  Yup.object().shape({
    customer_full_name: Yup.string().required(
      t("common.validations.required", {
        field: t("meters.customerFullName"),
      })
    ),
    customer_phone_number: Yup.string()
      .matches(/^[0-9]+$/, t("common.validations.digitsOnly"))
      .min(8, t("common.validations.minLength", { min: 8 }))
      .required(
        t("common.validations.required", {
          field: t("meters.customerPhoneNumber"),
        })
      ),
    initial_reading: Yup.number()
      .typeError(t("common.validations.mustBeNumber"))
      .min(0, t("common.validations.noNegative"))
      .when("package_type", {
        is: "usage",
        then: (schema) =>
          schema.required(
            t("common.validations.required", {
              field: t("meters.initialReading"),
            })
          ),
        otherwise: (schema) => schema.notRequired(),
      }),
    address: Yup.string().required(
      t("common.validations.required", { field: t("meters.address") })
    ),
    area_id: Yup.string().required(
      t("common.validations.required", { field: t("meters.area") })
    ),
    package_id: Yup.string().required(
      t("common.validations.required", { field: t("meters.package") })
    ),
    package_type: Yup.string()
      .oneOf(["usage", "fixed"])
      .required(
        t("common.validations.required", {
          field: t("meters.packageType"),
        })
      ),
  });

const getEditMeterSchema = (t: TFunction) =>
  Yup.object().shape({
    customer_full_name: Yup.string().required(
      t("common.validations.required", {
        field: t("meters.customerFullName"),
      })
    ),
    customer_phone_number: Yup.string()
      .matches(/^[0-9]+$/, t("common.validations.digitsOnly"))
      .min(8, t("common.validations.minLength", { min: 8 }))
      .required(
        t("common.validations.required", {
          field: t("meters.customerPhoneNumber"),
        })
      ),
    address: Yup.string().required(
      t("common.validations.required", { field: t("meters.address") })
    ),
    area_id: Yup.string().required(
      t("common.validations.required", { field: t("meters.area") })
    ),
    package_id: Yup.string().required(
      t("common.validations.required", { field: t("meters.package") })
    ),
    package_type: Yup.string()
      .oneOf(["usage", "fixed"])
      .required(
        t("common.validations.required", {
          field: t("meters.packageType"),
        })
      ),
    status: Yup.string()
      .oneOf(["active", "inactive"])
      .required(
        t("common.validations.required", {
          field: t("meters.status"),
        })
      ),
    initial_reading: Yup.number().optional(),
  });

const MeterFormModal = ({
  meter,
  show,
  handleClose,
  areas,
}: MeterFormModalProps) => {
  const { t, i18n } = useTranslation();
  const { success, handleError } = useAlert();

  const [packages, setPackages] = useState<Package[]>([]);
  const [isPackagesLoading, setIsPackagesLoading] = useState(false);
  const navigate = useNavigate();

  const isEditMode = !!meter;

  const areaOptions = useMemo(
    () => areas.map((a) => ({ value: a.area_id, label: a.area_name })),
    [areas]
  );

  const packageOptions = useMemo(
    () =>
      packages.map((p) => ({
        value: p.package_id,
        label: t("meters.amperagePackage", { amperage: p.amperage }),
      })),
    [packages, t]
  );

  useEffect(() => {
    if (show) {
      setIsPackagesLoading(true);
      getPackages({ page: 1, limit: 20 })
        .then((res) => setPackages(res.items))
        .catch(handleError)
        .finally(() => setIsPackagesLoading(false));
    }
  }, [show, handleError]);

  const initialValues = useMemo<MeterCreatePayload | MeterUpdatePayload>(() => {
    if (isEditMode && meter) {
      return {
        customer_full_name: meter.customer_full_name,
        customer_phone_number: meter.customer_phone_number,
        address: meter.address,
        area_id: meter.area_id,
        package_id: meter.package_id,
        package_type: meter.package_type as "usage" | "fixed",
        status: meter.status as "active" | "inactive",
        initial_reading: meter.initial_reading,
      };
    }
    return {
      customer_full_name: "",
      customer_phone_number: "",
      address: "",
      area_id: "",
      package_id: "",
      package_type: "usage",
      initial_reading: undefined,
    };
  }, [meter, isEditMode]);

  const validationSchema = useMemo(
    () => (isEditMode ? getEditMeterSchema(t) : getAddMeterSchema(t)),
    [isEditMode, t]
  );

  if (isEditMode && !meter) return null;

  return (
    <Modal show={show} onHide={() => handleClose(false)} centered size="lg">
      <Formik<MeterCreatePayload | MeterUpdatePayload>
        initialValues={initialValues}
        validationSchema={validationSchema}
        enableReinitialize // Important for edit mode when `meter` changes
        onSubmit={async (values, { setSubmitting }) => {
          try {
            if (isEditMode) {
              const payload = { ...values } as MeterUpdatePayload;
              if (payload.package_type === "fixed") {
                delete payload.initial_reading;
              }
              await updateMeter(meter!.meter_id, payload);
              success(t("messages.meterUpdated"));
            } else {
              const payload = { ...values } as MeterCreatePayload;
              if (payload.package_type === "fixed") {
                payload.initial_reading = undefined;
              } else {
                payload.initial_reading = Number(values.initial_reading);
              }
              await createMeter(payload);
              success(t("messages.meterCreated"));
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
          handleChange,
          handleSubmit,
          setFieldValue,
          isSubmitting,
          dirty,
          isValid,
        }) => (
          <Form onSubmit={handleSubmit}>
            <Modal.Header closeButton>
              <Modal.Title>
                {isEditMode
                  ? t("meters.editMeterTitle")
                  : t("meters.addMeterTitle")}
              </Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <Row>
                <Col md={6} className="mb-3">
                  <Form.Label>{t("meters.customerFullName")}</Form.Label>
                  <Form.Control
                    type="text"
                    name="customer_full_name"
                    value={values.customer_full_name}
                    onChange={handleChange}
                    isInvalid={
                      touched.customer_full_name && !!errors.customer_full_name
                    }
                    placeholder={t("meters.customerFullNamePlaceholder")}
                  />
                  <Form.Control.Feedback type="invalid">
                    {errors.customer_full_name}
                  </Form.Control.Feedback>
                </Col>
                <Col md={6} className="mb-3">
                  <Form.Label>{t("meters.customerPhoneNumber")}</Form.Label>
                  <Form.Control
                    type="tel"
                    name="customer_phone_number"
                    value={values.customer_phone_number}
                    onChange={handleChange}
                    isInvalid={
                      touched.customer_phone_number &&
                      !!errors.customer_phone_number
                    }
                    style={{
                      textAlign: i18n.dir() === "rtl" ? "right" : "left",
                    }}
                    placeholder={t("meters.customerPhoneNumberPlaceholder")}
                  />
                  <Form.Control.Feedback type="invalid">
                    {errors.customer_phone_number}
                  </Form.Control.Feedback>
                </Col>
              </Row>
              <Row>
                <Col md={isEditMode ? 6 : 12} className="mb-3">
                  <Form.Label>{t("meters.address")}</Form.Label>
                  <Form.Control
                    type="text"
                    name="address"
                    value={values.address}
                    onChange={handleChange}
                    isInvalid={touched.address && !!errors.address}
                    placeholder={t("meters.addressPlaceholder")}
                  />
                  <Form.Control.Feedback type="invalid">
                    {errors.address}
                  </Form.Control.Feedback>
                </Col>
                {isEditMode && (
                  <Col md={6} className="mb-3">
                    <Form.Label>{t("meters.statusWord")}</Form.Label>
                    <Form.Select
                      name="status"
                      value={
                        isEditMode ? (values as MeterUpdatePayload).status : ""
                      }
                      onChange={handleChange}
                      isInvalid={
                        isEditMode
                          ? (touched as FormikTouched<MeterUpdatePayload>)
                              .status &&
                            !!(errors as FormikErrors<MeterUpdatePayload>)
                              .status
                          : false
                      }
                    >
                      <option value="active">{t("meters.statusActive")}</option>
                      <option value="inactive">
                        {t("meters.statusInactive")}
                      </option>
                    </Form.Select>
                  </Col>
                )}
              </Row>
              <Row>
                <Col md={6} className="mb-3">
                  <Form.Group>
                    <Form.Label>{t("meters.area")}</Form.Label>
                    <Select
                      options={areaOptions}
                      placeholder={t("common.select")}
                      isSearchable={false}
                      value={
                        areaOptions.find((o) => o.value === values.area_id) ||
                        null
                      }
                      onChange={(option) =>
                        setFieldValue("area_id", option?.value || "")
                      }
                      menuPortalTarget={document.body}
                      styles={{
                        menuPortal: (base) => ({ ...base, zIndex: 3061 }),
                      }}
                      noOptionsMessage={() => (
                        <div
                          style={{
                            padding: "8px",
                            textAlign: "center",
                            color: "#555",
                          }}
                        >
                          <div>{t("areas.noAreasFound")}</div>
                          <Button
                            variant="link"
                            onMouseDown={(e) => {
                              e.preventDefault(); // prevent menu from closing before click
                              navigate("/areas");
                            }}
                          >
                            {t("areas.goToAreasPage")}
                          </Button>
                        </div>
                      )}
                    />

                    {touched.area_id && errors.area_id && (
                      <div className="invalid-feedback d-block">
                        {errors.area_id}
                      </div>
                    )}
                  </Form.Group>
                </Col>
                <Col md={6} className="mb-3">
                  <Form.Group>
                    <Form.Label>{t("meters.package")}</Form.Label>
                    <Select
                      options={packageOptions}
                      isSearchable={false}
                      placeholder={t("common.select")}
                      value={
                        packageOptions.find(
                          (o) => o.value === values.package_id
                        ) || null
                      }
                      onChange={(option) =>
                        setFieldValue("package_id", option?.value || "")
                      }
                      isLoading={isPackagesLoading}
                      isDisabled={isPackagesLoading}
                      menuPortalTarget={document.body}
                      styles={{
                        menuPortal: (base) => ({ ...base, zIndex: 3061 }),
                      }}
                      noOptionsMessage={() => (
                        <div
                          style={{
                            padding: "8px",
                            textAlign: "center",
                            color: "#555",
                          }}
                        >
                          <div>{t("packages.noPackagesFound")}</div>
                          <Button
                            variant="link"
                            onMouseDown={(e) => {
                              e.preventDefault();
                              navigate("/packages");
                            }}
                          >
                            {t("packages.goToPackagesPage")}
                          </Button>
                        </div>
                      )}
                    />
                    {touched.package_id && errors.package_id && (
                      <div className="invalid-feedback d-block">
                        {errors.package_id}
                      </div>
                    )}
                  </Form.Group>
                </Col>
              </Row>
              <Row>
                <Col md={6} className="mb-3">
                  <Form.Label>
                    {t("meters.packageTypeWord")}
                    <InfoTooltip text={t("meters.packageTypeTooltip")} />
                  </Form.Label>
                  <Form.Select
                    name="package_type"
                    value={values.package_type}
                    onChange={handleChange}
                    isInvalid={touched.package_type && !!errors.package_type}
                  >
                    <option value="usage">
                      {t("meters.packageTypeUsage")}
                    </option>
                    <option value="fixed">
                      {t("meters.packageTypeFixed")}
                    </option>
                  </Form.Select>
                  <Form.Control.Feedback type="invalid">
                    {errors.package_type}
                  </Form.Control.Feedback>
                </Col>
                {values.package_type === "usage" && (
                  <Col md={6} className="mb-3">
                    <Form.Label>{t("meters.initialReadingKwh")}</Form.Label>
                    <Form.Control
                      type="number"
                      name="initial_reading"
                      value={values.initial_reading ?? ""}
                      onChange={(e) => {
                        const txt = e.target.value;
                        setFieldValue(
                          "initial_reading",
                          txt === "" ? undefined : Number(txt)
                        );
                      }}
                      isInvalid={
                        touched.initial_reading && !!errors.initial_reading
                      }
                      readOnly={isEditMode && meter.package_type === "usage"}
                      disabled={isEditMode && meter.package_type === "usage"}
                      placeholder={t("meters.initialReadingPlaceholder")}
                      // Keep number input LTR
                    />
                    <Form.Control.Feedback type="invalid">
                      {errors.initial_reading}
                    </Form.Control.Feedback>
                  </Col>
                )}
              </Row>
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
                  ? t(isEditMode ? "common.saving" : "common.creating")
                  : t(isEditMode ? "common.saveChanges" : "meters.createMeter")}
              </Button>
            </Modal.Footer>
          </Form>
        )}
      </Formik>
    </Modal>
  );
};

export default MeterFormModal;
