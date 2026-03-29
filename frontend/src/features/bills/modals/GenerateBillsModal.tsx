// src/features/bills/components/GenerateBillsModal.tsx

import { useState, useEffect, type FC } from "react";
import {
  Modal,
  Button,
  Spinner,
  Alert,
  Form,
  Tooltip,
  OverlayTrigger,
  Row,
  Col,
  Card,
  ListGroup,
} from "react-bootstrap";
import { AxiosError } from "axios";
import { useTranslation, Trans } from "react-i18next";
import { useFormik } from "formik";
import * as Yup from "yup";
import { useAlert } from "../../../hooks/useAlert";
import {
  generateBills,
  getRateByMonth,
  createRate,
  updateRate,
} from "../billsService";
import type {
  Rate,
  UpdateRatePayload,
  ApiErrorResponse,
  GenerateBillsApiResponse,
  GenerationMetrics,
} from "../types";
import { getDefaultMonth } from "../../../utils/dateHelpers";
import { isEqual } from "lodash";
import { NumericFormat } from "react-number-format";

const InfoTooltip: FC<{ text: string }> = ({ text }) => (
  <OverlayTrigger placement="top" overlay={<Tooltip>{text}</Tooltip>}>
    <i className="bi bi-info-circle mx-2 text-secondary"></i>
  </OverlayTrigger>
);

const NumericFormControl = (props: any) => <Form.Control {...props} />;
NumericFormControl.displayName = "NumericFormControl";

// --- New Metrics Card Component ---
const MetricsCard: FC<{ metrics: GenerationMetrics }> = ({ metrics }) => {
  const { t } = useTranslation();
  const metricItems = [
    {
      label: t("bills.generateBillsModal.metrics.totalActive"),
      value: metrics.total_active_meters,
    },
    {
      label: t("bills.generateBillsModal.metrics.billsCreated"),
      value: metrics.bills_created,
      variant: "success",
    },
    {
      label: t("bills.generateBillsModal.metrics.alreadyExist"),
      value: metrics.bills_already_exist,
    },
    {
      label: t("bills.generateBillsModal.metrics.missingReadings"),
      value: metrics.meters_without_readings,
      variant: metrics.meters_without_readings > 0 ? "danger" : undefined,
    },
    {
      label: t("bills.generateBillsModal.metrics.unverifiedReadings"),
      value: metrics.unverified_readings,
      variant: metrics.unverified_readings > 0 ? "warning" : undefined,
    },
    {
      label: t("bills.generateBillsModal.metrics.skippedMeters"),
      value: metrics.skipped_meters,
    },
  ];

  return (
    <Card className="my-4 bg-light">
      <Card.Header>{t("bills.generateBillsModal.metrics.title")}</Card.Header>
      <ListGroup variant="flush">
        {metricItems.map((item) => (
          <ListGroup.Item
            key={item.label}
            className="d-flex justify-content-between align-items-center"
          >
            {item.label}
            <span
              className={`badge bg-${item.variant || "secondary"} rounded-pill`}
            >
              {item.value}
            </span>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Card>
  );
};

interface GenerateBillsModalProps {
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
}

type ModalStep = "rates" | "generate" | "results";

const initialFormState: UpdateRatePayload = {
  mountain_kwh_rate: 0,
  coastal_kwh_rate: 0,
  dollar_rate: 0,
  fixed_sub_rate: 0,
  fixed_sub_hours: 0,
};

export const GenerateBillsModal = ({
  show,
  handleClose,
}: GenerateBillsModalProps) => {
  const { t, i18n } = useTranslation();
  const { success, handleError } = useAlert();

  // Modal State
  const [step, setStep] = useState<ModalStep>("rates");
  const [billingMonth, setBillingMonth] = useState<string>(getDefaultMonth());

  // Data State
  const [isFetchingRates, setIsFetchingRates] = useState(true);
  const [ratesData, setRatesData] = useState<Rate | null>(null);
  const [initialRates, setInitialRates] =
    useState<UpdateRatePayload>(initialFormState);

  // Generation Step State
  const [isLoadingGeneration, setIsLoadingGeneration] = useState(false);
  const [generationResult, setGenerationResult] =
    useState<GenerateBillsApiResponse | null>(null);
  const [forceMissing, setForceMissing] = useState(false);
  const [forceUnverified, setForceUnverified] = useState(false);

  const validationSchema = Yup.object().shape({
    mountain_kwh_rate: Yup.number()
      .min(0, t("bills.generateBillsModal.validation.minZero"))
      .required(t("bills.generateBillsModal.validation.required")),
    coastal_kwh_rate: Yup.number()
      .min(0, t("bills.generateBillsModal.validation.minZero"))
      .required(t("bills.generateBillsModal.validation.required")),
    dollar_rate: Yup.number()
      .positive(t("bills.generateBillsModal.validation.positive"))
      .required(t("bills.generateBillsModal.validation.required")),
    fixed_sub_rate: Yup.number()
      .min(0, t("bills.generateBillsModal.validation.minZero"))
      .required(t("bills.generateBillsModal.validation.required")),
    fixed_sub_hours: Yup.number()
      .min(0, t("bills.generateBillsModal.validation.minZero"))
      .required(t("bills.generateBillsModal.validation.required")),
  });

  const formik = useFormik({
    initialValues: initialFormState,
    validationSchema,
    enableReinitialize: true,
    onSubmit: async (values) => {
      try {
        let finalRatesData = ratesData;
        if (ratesData) {
          if (!isEqual(values, initialRates)) {
            const response = await updateRate(ratesData.rate_id, values);
            finalRatesData = response.data;
            success(t("bills.generateBillsModal.messages.ratesUpdated"));
          }
        } else {
          const payload = { ...values, effective_date: billingMonth };
          const response = await createRate(payload);
          finalRatesData = response.data;
          success(t("bills.generateBillsModal.messages.ratesCreated"));
        }
        setRatesData(finalRatesData);
        setStep("generate");
      } catch (error) {
        handleError(error);
      }
    },
  });

  useEffect(() => {
    if (show) {
      fetchRatesForMonth(billingMonth);
    }
  }, [show, billingMonth]);

  const fetchRatesForMonth = async (month: string) => {
    // ... This function remains unchanged from your original code
    setIsFetchingRates(true);
    setRatesData(null);
    try {
      const response = await getRateByMonth(month);
      const fetchedRates = response.data;
      setRatesData(fetchedRates);
      const currentValues = {
        mountain_kwh_rate: fetchedRates.mountain_kwh_rate,
        coastal_kwh_rate: fetchedRates.coastal_kwh_rate,
        dollar_rate: fetchedRates.dollar_rate,
        fixed_sub_rate: fetchedRates.fixed_sub_rate,
        fixed_sub_hours: fetchedRates.fixed_sub_hours,
      };
      formik.setValues(currentValues);
      setInitialRates(currentValues);
    } catch (error) {
      const axiosError = error as AxiosError<ApiErrorResponse>;
      if (
        axiosError.response?.status === 400 ||
        axiosError.response?.status === 404
      ) {
        setRatesData(null);
        formik.setValues(initialFormState);
        setInitialRates(initialFormState);
      } else {
        handleError(t("bills.generateBillsModal.errors.fetchRatesError"));
        handleClose(false);
      }
    } finally {
      setIsFetchingRates(false);
    }
  };

  const handleGenerate = async (
    shouldForceMissing = forceMissing,
    shouldForceUnverified = forceUnverified
  ) => {
    if (!ratesData) {
      handleError(t("bills.generateBillsModal.errors.noRateIdError"));
      return;
    }
    setIsLoadingGeneration(true);
    setGenerationResult(null);

    try {
      const response = await generateBills(
        billingMonth,
        ratesData.rate_id,
        shouldForceMissing,
        shouldForceUnverified
      );
      setGenerationResult(response);
      setStep("results");
    } catch (error) {
      handleError(error);
      // If API fails with a non-200, we might want to go back a step
      setStep("generate");
    } finally {
      setIsLoadingGeneration(false);
    }
  };

  const handleForceMissing = () => {
    setForceMissing(true);
    handleGenerate(true, forceUnverified);
  };

  const handleForceUnverified = () => {
    setForceUnverified(true);
    handleGenerate(forceMissing, true);
  };

  const onModalExit = () => {
    setStep("rates");
    setBillingMonth(getDefaultMonth());
    setRatesData(null);
    formik.resetForm();
    setInitialRates(initialFormState);
    setIsFetchingRates(true);
    setIsLoadingGeneration(false);
    setGenerationResult(null);
    setForceMissing(false);
    setForceUnverified(false);
  };

  // --- RENDER FUNCTIONS ---

  const renderRatesStep = () => {
    // ... This function remains unchanged from your original code
    if (isFetchingRates)
      return (
        <div className="text-center p-5">
          <Spinner animation="border" />
        </div>
      );
    return (
      <Form noValidate onSubmit={formik.handleSubmit}>
        <Row>
          <Col xs={12} md={6}>
            <Form.Group className="mb-3" controlId="billingMonth">
              <Form.Label>
                {t("bills.generateBillsModal.rates.selectMonthLabel")}
              </Form.Label>
              <Form.Control
                type="month"
                value={billingMonth}
                onChange={(e) => setBillingMonth(e.target.value)}
                disabled={formik.isSubmitting}
                style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
              />
            </Form.Group>
          </Col>
          <Col xs={12} md={6}>
            <Form.Group className="mb-3">
              <Form.Label>
                {t("bills.generateBillsModal.rates.mountainKwhRate")}
                <InfoTooltip
                  text={t("bills.generateBillsModal.tooltips.mountainKwhRate")}
                />
              </Form.Label>
              <NumericFormat
                customInput={NumericFormControl}
                name="mountain_kwh_rate"
                thousandSeparator
                allowNegative={false}
                value={formik.values.mountain_kwh_rate}
                onValueChange={(values) =>
                  formik.setFieldValue(
                    "mountain_kwh_rate",
                    values.floatValue ?? 0
                  )
                }
                onBlur={formik.handleBlur}
                disabled={formik.isSubmitting}
                isInvalid={
                  formik.touched.mountain_kwh_rate &&
                  !!formik.errors.mountain_kwh_rate
                }
              />
              <Form.Control.Feedback type="invalid">
                {formik.errors.mountain_kwh_rate}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        <Row>
          <Col xs={12} md={6}>
            <Form.Group className="mb-3">
              <Form.Label>
                {t("bills.generateBillsModal.rates.coastalKwhRate")}
                <InfoTooltip
                  text={t("bills.generateBillsModal.tooltips.coastalKwhRate")}
                />
              </Form.Label>
              <NumericFormat
                customInput={NumericFormControl}
                name="coastal_kwh_rate"
                thousandSeparator
                allowNegative={false}
                value={formik.values.coastal_kwh_rate}
                onValueChange={(values) =>
                  formik.setFieldValue(
                    "coastal_kwh_rate",
                    values.floatValue ?? 0
                  )
                }
                onBlur={formik.handleBlur}
                disabled={formik.isSubmitting}
                isInvalid={
                  formik.touched.coastal_kwh_rate &&
                  !!formik.errors.coastal_kwh_rate
                }
              />
              <Form.Control.Feedback type="invalid">
                {formik.errors.coastal_kwh_rate}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          <Col xs={12} md={6}>
            <Form.Group className="mb-4">
              <Form.Label>
                {t("bills.generateBillsModal.rates.dollarRate")}
                <InfoTooltip
                  text={t("bills.generateBillsModal.tooltips.dollarRate")}
                />
              </Form.Label>
              <NumericFormat
                customInput={NumericFormControl}
                name="dollar_rate"
                thousandSeparator
                allowNegative={false}
                value={formik.values.dollar_rate}
                onValueChange={(values) =>
                  formik.setFieldValue("dollar_rate", values.floatValue ?? 0)
                }
                onBlur={formik.handleBlur}
                disabled={formik.isSubmitting}
                isInvalid={
                  formik.touched.dollar_rate && !!formik.errors.dollar_rate
                }
              />
              <Form.Control.Feedback type="invalid">
                {formik.errors.dollar_rate}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        <Row>
          <Col xs={12} md={6}>
            <Form.Group className="mb-4">
              <Form.Label>
                {t("bills.generateBillsModal.rates.fixedSubRate")}
                <InfoTooltip
                  text={t("bills.generateBillsModal.tooltips.fixedSubRate")}
                />
              </Form.Label>
              <NumericFormat
                customInput={NumericFormControl}
                name="fixed_sub_rate"
                thousandSeparator
                allowNegative={false}
                value={formik.values.fixed_sub_rate}
                onValueChange={(values) =>
                  formik.setFieldValue("fixed_sub_rate", values.floatValue ?? 0)
                }
                onBlur={formik.handleBlur}
                disabled={formik.isSubmitting}
                isInvalid={
                  formik.touched.fixed_sub_rate &&
                  !!formik.errors.fixed_sub_rate
                }
              />
              <Form.Control.Feedback type="invalid">
                {formik.errors.fixed_sub_rate}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          <Col xs={12} md={6}>
            <Form.Group className="mb-4">
              <Form.Label>
                {t("bills.generateBillsModal.rates.fixedSubHours")}
                <InfoTooltip
                  text={t("bills.generateBillsModal.tooltips.fixedSubHours")}
                />
              </Form.Label>
              <NumericFormat
                customInput={NumericFormControl}
                name="fixed_sub_hours"
                thousandSeparator
                allowNegative={false}
                value={formik.values.fixed_sub_hours}
                onValueChange={(values) =>
                  formik.setFieldValue(
                    "fixed_sub_hours",
                    values.floatValue ?? 0
                  )
                }
                onBlur={formik.handleBlur}
                disabled={formik.isSubmitting}
                isInvalid={
                  formik.touched.fixed_sub_hours &&
                  !!formik.errors.fixed_sub_hours
                }
              />
              <Form.Control.Feedback type="invalid">
                {formik.errors.fixed_sub_hours}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="secondary"
            onClick={() => handleClose(true)}
            disabled={formik.isSubmitting}
          >
            {t("common.cancel")}
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={formik.isSubmitting}
          >
            {formik.isSubmitting ? (
              <Spinner as="span" size="sm" />
            ) : (
              t("common.next")
            )}
          </Button>
        </div>
      </Form>
    );
  };

  const renderGenerateStep = () => (
    <>
      <p>
        <Trans
          i18nKey="bills.generateBillsModal.initialInfoText"
          values={{ month: billingMonth }}
        />
      </p>
      <p>{t("bills.generateBillsModal.confirmProceed")}</p>
      <div className="d-flex justify-content-between gap-2">
        <Button
          variant="outline-secondary"
          onClick={() => setStep("rates")}
          disabled={isLoadingGeneration}
        >
          {t("common.back")}
        </Button>
        <div className="d-flex justify-content-end gap-2">
          <Button
            variant="primary"
            onClick={() => handleGenerate()}
            disabled={isLoadingGeneration}
          >
            {isLoadingGeneration ? (
              <Spinner as="span" size="sm" />
            ) : (
              t("bills.generateBillsModal.startGeneration")
            )}
          </Button>
        </div>
      </div>
    </>
  );

  const renderResultsStep = () => {
    if (isLoadingGeneration) {
      return (
        <div className="text-center p-5">
          <Spinner animation="border" />{" "}
          <p className="mt-2">{t("common.loading")}</p>
        </div>
      );
    }
    if (!generationResult) {
      return <Alert variant="danger">{t("common.errors.unknown")}</Alert>;
    }

    const { data } = generationResult;
    const { metrics } = data;

    const isSuccess = !!data.task_id && metrics.bills_created > 0;
    if (isSuccess) {
      // SCENARIO 1: Full Success
      return (
        <>
          <Alert variant="success">
            <Alert.Heading>
              {t("bills.generateBillsModal.results.successTitle")}
            </Alert.Heading>
            {generationResult.message}
          </Alert>
          <MetricsCard metrics={metrics} />
          <div className="d-flex justify-content-end">
            <Button variant="primary" onClick={() => handleClose(true)}>
              {t("common.finish")}
            </Button>
          </div>
        </>
      );
    }

    const hasMissing = metrics.meters_without_readings > 0;
    if (hasMissing && !forceMissing) {
      // SCENARIO 2: Missing readings found, offer to force
      return (
        <>
          <Alert variant="warning">
            <Alert.Heading>
              {t("bills.generateBillsModal.results.missingTitle")}
            </Alert.Heading>
            {generationResult.message}
          </Alert>
          <MetricsCard metrics={metrics} />
          <p>
            <Trans
              i18nKey="bills.generateBillsModal.results.missingPrompt"
              components={{ strong: <strong /> }}
            />
          </p>
          <div className="d-flex justify-content-between align-items-center mt-3">
            <Button
              variant="outline-secondary"
              onClick={() => setStep("generate")}
            >
              {t("common.back")}
            </Button>
            <div className="d-flex gap-2">
              <Button variant="secondary" onClick={() => handleClose(true)}>
                {t("common.cancel")}
              </Button>
              <Button variant="warning" onClick={handleForceMissing}>
                {t("bills.generateBillsModal.forceMissing")}
              </Button>
            </div>
          </div>
        </>
      );
    }

    const hasUnverified = metrics.unverified_readings > 0;
    const canForceUnverified =
      metrics.verified_readings > metrics.bills_already_exist;
    if (hasUnverified) {
      if (canForceUnverified && !forceUnverified) {
        // SCENARIO 3: Unverified readings found, offer to force
        return (
          <>
            <Alert variant="warning">
              <Alert.Heading>
                {t("bills.generateBillsModal.results.unverifiedTitle")}
              </Alert.Heading>
              {generationResult.message}
            </Alert>
            <MetricsCard metrics={metrics} />
            <p>
              <Trans
                i18nKey="bills.generateBillsModal.results.unverifiedPrompt"
                components={{ strong: <strong /> }}
              />
            </p>
            <small className="d-block mb-3">
              {t("bills.generateBillsModal.unverifiedNote")}
            </small>
            <div className="d-flex justify-content-between align-items-center mt-3">
              <Button
                variant="outline-secondary"
                onClick={() => setStep("generate")}
              >
                {t("common.back")}
              </Button>
              <div className="d-flex gap-2">
                <Button variant="secondary" onClick={() => handleClose(true)}>
                  {t("common.cancel")}
                </Button>
                <Button variant="warning" onClick={handleForceUnverified}>
                  {t("bills.generateBillsModal.forceUnverified")}
                </Button>
              </div>
            </div>
          </>
        );
      } else {
        // SCENARIO 4: Unverified readings, but cannot force (or already tried)
        return (
          <>
            <Alert variant="danger">
              <Alert.Heading>
                {t("bills.generateBillsModal.results.cannotProceedTitle")}
              </Alert.Heading>
              {generationResult.message}
            </Alert>
            <MetricsCard metrics={metrics} />
            <p>
              <Trans
                i18nKey="bills.generateBillsModal.results.cannotProceedPrompt"
                components={{ strong: <strong /> }}
              />
            </p>
            <div className="d-flex justify-content-between align-items-center mt-3">
              <Button
                variant="outline-secondary"
                onClick={() => setStep("generate")}
              >
                {t("common.back")}
              </Button>
              <div className="d-flex gap-2">
                <Button variant="secondary" onClick={() => handleClose(false)}>
                  {t("common.cancel")}
                </Button>
                <Button
                  href="/readings"
                  variant="primary"
                  onClick={() => handleClose(true)}
                >
                  {t("bills.generateBillsModal.goToReadings")}
                </Button>
              </div>
            </div>
          </>
        );
      }
    }

    // Fallback: No bills created for other reasons (e.g., all exist already)
    return (
      <>
        <Alert variant="info">
          <Alert.Heading>
            {t("bills.generateBillsModal.results.noNewBillsTitle")}
          </Alert.Heading>
          {generationResult.message}
        </Alert>
        <MetricsCard metrics={metrics} />
        <div className="d-flex justify-content-end">
          <Button variant="primary" onClick={() => handleClose(true)}>
            {t("common.close")}
          </Button>
        </div>
      </>
    );
  };

  const renderContent = () => {
    switch (step) {
      case "rates":
        return renderRatesStep();
      case "generate":
        return renderGenerateStep();
      case "results":
        return renderResultsStep();
      default:
        return renderRatesStep();
    }
  };

  const getTitle = () => {
    switch (step) {
      case "rates":
        return t("bills.generateBillsModal.titles.rates");
      case "generate":
        return t("bills.generateBillsModal.titles.generate");
      case "results":
        return t("bills.generateBillsModal.titles.results");
      default:
        return t("bills.generateBillsModal.titles.generate");
    }
  };

  const anyLoading = formik.isSubmitting || isLoadingGeneration;

  return (
    <Modal
      show={show}
      onHide={() => !anyLoading && handleClose(true)}
      centered
      onExited={onModalExit}
      backdrop={anyLoading ? "static" : true}
      size="lg"
    >
      <Modal.Header closeButton={!anyLoading}>
        <Modal.Title>{getTitle()}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{renderContent()}</Modal.Body>
    </Modal>
  );
};
