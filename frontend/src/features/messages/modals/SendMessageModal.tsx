import type { FC } from "react";
import { useState, useMemo, useEffect } from "react";
import {
  Modal,
  Button,
  Form,
  Row,
  Col,
  Spinner,
  OverlayTrigger,
  Tooltip,
  Alert,
  ListGroup,
  Badge,
} from "react-bootstrap";
import { useForm, Controller } from "react-hook-form";
import type { Control, FieldErrors } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import AsyncSelect from "react-select/async";
import Select from "react-select";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import debounce from "lodash/debounce";
import { format, parseISO } from "date-fns";
import { formatInTimeZone } from "date-fns-tz";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import type { SendMessagePayload, SelectOption } from "../types";
import {
  getTemplates,
  getMeters,
  getAreas,
  getPackages,
  sendMessage,
  getSessionStatus,
} from "../messagesService";
import { useAlert } from "../../../hooks/useAlert";

const TIMEZONE = "Asia/Beirut";

interface SendMessageModalProps {
  show: boolean;
  handleClose: () => void;
}

// Zod schema is now a hook to access translations
// It's enhanced with specific paths for step-based validation
const useSendMessageSchema = () => {
  const { t } = useTranslation();

  const optionSchema = z.object({
    value: z.string(),
    label: z.string(),
  });

  const billFiltersSchema = z
    .object({
      payment_status: optionSchema.nullable().optional(),
      due_date: z.string().nullable().optional(),
      payment_method: z.array(optionSchema),
      overdue_only: z.boolean(),
    })
    .refine(
      (data) => {
        const isFilterUsed =
          data.payment_status ||
          data.payment_method.length > 0 ||
          data.overdue_only;
        if (isFilterUsed) {
          return !!data.due_date;
        }
        return true;
      },
      {
        message: t(
          "messages.sendMessageModal.validation.dueDateRequiredWithFilter"
        ),
        path: ["due_date"],
      }
    );

  return z
    .object({
      // Step 1
      template_id: optionSchema.nullable().optional(),
      message: z.string().optional(),
      // Step 2
      broadcast: z.boolean(),
      customer_ids: z.array(optionSchema),
      meter_filters: z
        .object({
          area_ids: z.array(optionSchema),
          package_ids: z.array(optionSchema),
          meter_status: optionSchema.nullable().optional(),
          package_type: optionSchema.nullable().optional(),
        })
        .optional(),
      bill_filters: billFiltersSchema.optional(),
      // Step 3
      send_immediately: z.boolean(),
      scheduled_at: z.string().nullable().optional(),
    })
    .superRefine((data, ctx) => {
      // Step 1: Content validation
      const hasTemplate = !!data.template_id;
      const hasMessage = !!data.message?.trim();
      if (!hasTemplate && !hasMessage) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("messages.sendMessageModal.validation.contentRequired"),
          path: ["messageContent"], // Custom path for step 1
        });
      }
      if (hasTemplate && hasMessage) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("messages.sendMessageModal.validation.contentExclusive"),
          path: ["messageContent"], // Custom path for step 1
        });
      }

      // Step 2: Audience validation
      const hasCustomers = data.customer_ids.length > 0;
      const hasFilters =
        (data.meter_filters &&
          (data.meter_filters.area_ids.length > 0 ||
            data.meter_filters.package_ids.length > 0 ||
            data.meter_filters.meter_status ||
            data.meter_filters.package_type)) ||
        (data.bill_filters &&
          (data.bill_filters.payment_status ||
            data.bill_filters.payment_method.length > 0 ||
            data.bill_filters.overdue_only ||
            data.bill_filters.due_date));
      const audienceOptionsCount = [
        data.broadcast,
        hasCustomers,
        hasFilters,
      ].filter(Boolean).length;
      if (audienceOptionsCount === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("messages.sendMessageModal.validation.audienceRequired"),
          path: ["audience"], // Custom path for step 2
        });
      }
      if (audienceOptionsCount > 1) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("messages.sendMessageModal.validation.audienceExclusive"),
          path: ["audience"], // Custom path for step 2
        });
      }

      // Step 3: Schedule validation
      if (!data.send_immediately && !data.scheduled_at) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: t("messages.sendMessageModal.validation.scheduleRequired"),
          path: ["schedule"], // Custom path for step 3
        });
      }
    });
};

type FormValues = z.infer<ReturnType<typeof useSendMessageSchema>>;
type StepProps = {
  control: Control<FormValues>;
  errors: FieldErrors<FormValues>;
  values: FormValues;
  isFilterSectionDisabled?: boolean;
  setValue?: (name: any, value: any) => void;
};

// --- Helper Components & Functions ---

// Helper to remove empty/null values from payload before sending
const cleanPayload = (obj: any): any => {
  return Object.entries(obj).reduce((acc, [key, value]) => {
    if (
      value === null ||
      value === undefined ||
      value === "" ||
      (typeof value === "boolean" && value === false)
    ) {
      return acc;
    }
    if (Array.isArray(value) && value.length === 0) return acc;

    if (typeof value === "object" && !Array.isArray(value) && value !== null) {
      const cleanedChild = cleanPayload(value);
      if (Object.keys(cleanedChild).length > 0) {
        acc[key] = cleanedChild;
      }
    } else {
      acc[key] = value;
    }
    return acc;
  }, {} as any);
};

const InfoTooltip: FC<{ text: string }> = ({ text }) => (
  <OverlayTrigger placement="top" overlay={<Tooltip>{text}</Tooltip>}>
    <i className="bi bi-info-circle mx-2 text-secondary"></i>
  </OverlayTrigger>
);

const getErrorMessagesForPaths = (
  errors: FieldErrors<FormValues>,
  paths: string[]
): string[] => {
  const messages = new Set<string>();
  for (const path of paths) {
    const error = path.includes(".")
      ? path.split(".").reduce((o: any, i) => o?.[i], errors)
      : errors[path as keyof typeof errors];

    if (error?.message && typeof error.message === "string") {
      messages.add(error.message);
    }
  }
  return Array.from(messages);
};

// --- Debounced Loaders for AsyncSelect (unchanged) ---
const loadTemplateOptions = debounce(
  (inputValue: string, callback: (options: SelectOption[]) => void) => {
    getTemplates({ page: 1, limit: 10, query: inputValue }).then(
      ({ items }) => {
        callback(items.map((t) => ({ value: t.template_id, label: t.name })));
      }
    );
  },
  500
);
const loadCustomerOptions = debounce(
  (inputValue: string, callback: (options: SelectOption[]) => void) => {
    getMeters({ page: 1, limit: 10, query: inputValue }).then(({ items }) => {
      callback(
        items.map((t) => ({ value: t.meter_id, label: t.customer_full_name }))
      );
    });
  },
  500
);
const loadAreaOptions = debounce(
  (inputValue: string, callback: (options: SelectOption[]) => void) => {
    getAreas({ page: 1, limit: 10, query: inputValue }).then(({ items }) => {
      callback(items.map((t) => ({ value: t.area_id, label: t.area_name })));
    });
  },
  500
);
const loadPackageOptions = debounce(
  (inputValue: string, callback: (options: SelectOption[]) => void) => {
    getPackages({ page: 1, limit: 10, amperage: inputValue }).then(
      ({ items }) => {
        callback(
          items.map((t) => ({
            value: t.package_id,
            label: `${t.amperage}A`, // Keep number in english always
          }))
        );
      }
    );
  },
  500
);

// --- Step 1: Message Content Component ---
const Step1MessageContent: FC<StepProps> = ({ control, values }) => {
  const { t } = useTranslation();
  return (
    <>
      <Form.Group className="mb-3">
        <Form.Label>
          {t("messages.sendMessageModal.step1.templateLabel")}
          <InfoTooltip
            text={t("messages.sendMessageModal.step1.templateTooltip")}
          />
        </Form.Label>
        <Controller
          name="template_id"
          control={control}
          render={({ field }) => (
            <AsyncSelect
              {...field}
              isClearable
              cacheOptions
              defaultOptions
              loadOptions={loadTemplateOptions}
              isDisabled={!!values.message}
              placeholder={t("common.selectPlaceholder")}
            />
          )}
        />
      </Form.Group>
      <div className="text-center my-2">{t("common.orSeparator")}</div>
      <Form.Group>
        <Form.Label>
          {t("messages.sendMessageModal.step1.customMessageLabel")}
          <InfoTooltip
            text={t("messages.sendMessageModal.step1.customMessageTooltip")}
          />
        </Form.Label>
        <Controller
          name="message"
          control={control}
          render={({ field }) => (
            <Form.Control
              {...field}
              as="textarea"
              rows={3}
              disabled={!!values.template_id}
            />
          )}
        />
      </Form.Group>
    </>
  );
};

// --- Step 2: Target Audience Component ---
const Step2TargetAudience: FC<StepProps> = ({ control, values, setValue }) => {
  const { t } = useTranslation();

  const hasActiveFilters =
    (values.meter_filters &&
      (values.meter_filters.area_ids.length > 0 ||
        values.meter_filters.package_ids.length > 0 ||
        values.meter_filters.meter_status ||
        values.meter_filters.package_type)) ||
    (values.bill_filters &&
      (values.bill_filters.payment_status ||
        values.bill_filters.payment_method.length > 0 ||
        values.bill_filters.overdue_only ||
        values.bill_filters.due_date));

  const isAudienceSectionDisabled = !!hasActiveFilters;
  const isFilterSectionDisabled =
    values.broadcast || values.customer_ids.length > 0;

  // Static options (memoized for i18n)
  const meterStatusOptions = useMemo(
    () => [
      {
        value: "active",
        label: t("messages.sendMessageModal.options.meterStatusActive"),
      },
      {
        value: "inactive",
        label: t("messages.sendMessageModal.options.meterStatusInactive"),
      },
    ],
    [t]
  );
  const packageTypeOptions = useMemo(
    () => [
      {
        value: "usage",
        label: t("messages.sendMessageModal.options.packageTypeUsage"),
      },
      {
        value: "fixed",
        label: t("messages.sendMessageModal.options.packageTypeFixed"),
      },
    ],
    [t]
  );
  const paymentStatusOptions = useMemo(
    () => [
      {
        value: "paid",
        label: t("messages.sendMessageModal.options.paymentStatusPaid"),
      },
      {
        value: "unpaid",
        label: t("messages.sendMessageModal.options.paymentStatusUnpaid"),
      },
      {
        value: "partially_paid",
        label: t(
          "messages.sendMessageModal.options.paymentStatusPartiallyPaid"
        ),
      },
    ],
    [t]
  );
  const paymentMethodOptions = useMemo(
    () => [
      {
        value: "cash",
        label: t("messages.sendMessageModal.options.paymentMethodCash"),
      },
      { value: "omt", label: "OMT" },
      { value: "wish", label: "WISH" },
    ],
    [t]
  );

  return (
    <>
      {isAudienceSectionDisabled && (
        <Alert variant="warning">
          {t("messages.sendMessageModal.alerts.clearFiltersForAudience")}
        </Alert>
      )}
      <fieldset
        disabled={isAudienceSectionDisabled}
        className="border p-3 rounded mb-3"
      >
        <legend className="float-none w-auto px-2 fs-6">
          {t("messages.sendMessageModal.step2.audienceSelection")}
        </legend>
        <Form.Group className="mb-3">
          <Controller
            name="broadcast"
            control={control}
            render={({ field }) => (
              <Form.Check
                type="switch"
                label={
                  <>
                    {t("messages.sendMessageModal.step2.broadcastLabel")}
                    <InfoTooltip
                      text={t(
                        "messages.sendMessageModal.step2.broadcastTooltip"
                      )}
                    />
                  </>
                }
                checked={field.value}
                onChange={(e) => {
                  field.onChange(e.target.checked);
                  if (e.target.checked && setValue)
                    setValue("customer_ids", []);
                }}
                disabled={
                  isAudienceSectionDisabled || values.customer_ids.length > 0
                }
              />
            )}
          />
        </Form.Group>
        <div className="text-center my-2">{t("common.orSeparator")}</div>
        <Form.Group>
          <Form.Label>
            {t("messages.sendMessageModal.step2.specificCustomersLabel")}
            <InfoTooltip
              text={t(
                "messages.sendMessageModal.step2.specificCustomersTooltip"
              )}
            />
          </Form.Label>
          <Controller
            name="customer_ids"
            control={control}
            render={({ field }) => (
              <AsyncSelect
                {...field}
                isMulti
                cacheOptions
                loadOptions={loadCustomerOptions}
                defaultOptions
                isDisabled={values.broadcast || isAudienceSectionDisabled}
                placeholder={t("common.searchAndSelectPlaceholder")}
              />
            )}
          />
        </Form.Group>
      </fieldset>

      <div className="text-center my-3 fw-bold">
        {t("messages.sendMessageModal.advancedFilterSeparator")}
      </div>

      {isFilterSectionDisabled && (
        <Alert variant="warning">
          {t("messages.sendMessageModal.alerts.clearAudienceForFilters")}
        </Alert>
      )}
      <fieldset
        disabled={isFilterSectionDisabled}
        className="border p-3 rounded"
      >
        <legend className="float-none w-auto px-2 fs-6">
          {t("messages.sendMessageModal.step3.header")}
        </legend>
        <h5>{t("messages.sendMessageModal.step3.meterFiltersHeader")}</h5>
        <Row>
          <Col md={6} className="mb-3">
            <Form.Label>
              {t("messages.sendMessageModal.step3.areasLabel")}
            </Form.Label>
            <Controller
              name="meter_filters.area_ids"
              control={control}
              render={({ field }) => (
                <AsyncSelect
                  {...field}
                  isMulti
                  cacheOptions
                  loadOptions={loadAreaOptions}
                  defaultOptions
                  isDisabled={isFilterSectionDisabled}
                  placeholder={t("common.searchAndSelectPlaceholder")}
                />
              )}
            />
          </Col>
          <Col md={6} className="mb-3">
            <Form.Label>
              {t("messages.sendMessageModal.step3.packagesLabel")}
            </Form.Label>
            <Controller
              name="meter_filters.package_ids"
              control={control}
              render={({ field }) => (
                <AsyncSelect
                  {...field}
                  isMulti
                  cacheOptions
                  loadOptions={loadPackageOptions}
                  defaultOptions
                  isDisabled={isFilterSectionDisabled}
                  placeholder={t("common.searchAndSelectPlaceholder")}
                />
              )}
            />
          </Col>
          <Col md={6} className="mb-3">
            <Form.Label>
              {t("messages.sendMessageModal.step3.meterStatusLabel")}
            </Form.Label>
            <Controller
              name="meter_filters.meter_status"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  options={meterStatusOptions}
                  isClearable
                  isSearchable={false}
                  isDisabled={isFilterSectionDisabled}
                  placeholder={t("common.selectPlaceholder")}
                />
              )}
            />
          </Col>
          <Col md={6} className="mb-3">
            <Form.Label>
              {t("messages.sendMessageModal.step3.packageTypeLabel")}
            </Form.Label>
            <Controller
              name="meter_filters.package_type"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  options={packageTypeOptions}
                  isClearable
                  isSearchable={false}
                  isDisabled={isFilterSectionDisabled}
                  placeholder={t("common.selectPlaceholder")}
                />
              )}
            />
          </Col>
        </Row>
        <hr />
        <h5>{t("messages.sendMessageModal.step3.billFiltersHeader")}</h5>
        <Row>
          <Col md={6} className="mb-3">
            <Form.Label>
              {t("messages.sendMessageModal.step3.paymentStatusLabel")}
            </Form.Label>
            <Controller
              name="bill_filters.payment_status"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  options={paymentStatusOptions}
                  isClearable
                  isDisabled={isFilterSectionDisabled}
                  isSearchable={false}
                  placeholder={t("common.selectPlaceholder")}
                />
              )}
            />
          </Col>
          <Col md={6} className="mb-3">
            <Form.Label>
              {t("messages.sendMessageModal.step3.dueDateLabel")}
            </Form.Label>
            <Controller
              name="bill_filters.due_date"
              control={control}
              render={({ field, fieldState }) => (
                <DatePicker
                  selected={field.value ? new Date(field.value) : null}
                  onChange={(date: Date | null) =>
                    field.onChange(
                      date
                        ? `${date.getFullYear()}-${String(
                            date.getMonth() + 1
                          ).padStart(2, "0")}`
                        : null
                    )
                  }
                  placeholderText={t(
                    "messages.sendMessageModal.placeholders.selectDate"
                  )}
                  dateFormat="MM/yyyy"
                  showMonthYearPicker
                  className={`form-control ${
                    fieldState.error ? "is-invalid" : ""
                  }`}
                  isClearable
                />
              )}
            />
          </Col>
          {values.bill_filters?.payment_status?.value === "paid" && (
            <Col md={6} className="mb-3">
              <Form.Label>
                {t("messages.sendMessageModal.step3.paymentMethodLabel")}
              </Form.Label>
              <Controller
                name="bill_filters.payment_method"
                control={control}
                render={({ field }) => (
                  <Select
                    {...field}
                    options={paymentMethodOptions}
                    isMulti
                    isClearable
                    isSearchable={false}
                    isDisabled={isFilterSectionDisabled}
                    placeholder={t("common.selectPlaceholder")}
                  />
                )}
              />
            </Col>
          )}
          <Col md={12}>
            <Controller
              name="bill_filters.overdue_only"
              control={control}
              render={({ field }) => (
                <Form.Check
                  type="switch"
                  label={
                    <>
                      {t("messages.sendMessageModal.step3.overdueOnlyLabel")}
                      <InfoTooltip
                        text={t(
                          "messages.sendMessageModal.step3.overdueOnlyTooltip"
                        )}
                      />
                    </>
                  }
                  checked={field.value}
                  onChange={field.onChange}
                />
              )}
            />
          </Col>
        </Row>
      </fieldset>
    </>
  );
};

// --- Step 3: Scheduling Component ---
const Step3Scheduling: FC<StepProps> = ({ control, values, setValue }) => {
  const { t } = useTranslation();
  return (
    <>
      <Form.Group className="mb-3">
        <Controller
          name="send_immediately"
          control={control}
          render={({ field }) => (
            <Form.Check
              type="switch"
              label={
                <>
                  {t("messages.sendMessageModal.step4.sendImmediatelyLabel")}
                  <InfoTooltip
                    text={t(
                      "messages.sendMessageModal.step4.sendImmediatelyTooltip"
                    )}
                  />
                </>
              }
              checked={field.value}
              disabled={!!values.scheduled_at}
              onChange={(e) => {
                field.onChange(e.target.checked);
                if (e.target.checked && setValue)
                  setValue("scheduled_at", null);
              }}
            />
          )}
        />
      </Form.Group>
      <div className="text-center my-2">{t("common.orSeparator")}</div>
      <Form.Group>
        <Form.Label>
          {t("messages.sendMessageModal.step4.scheduleLaterLabel")}
          <InfoTooltip
            text={t("messages.sendMessageModal.step4.scheduleLaterTooltip")}
          />
        </Form.Label>
        <Controller
          name="scheduled_at"
          control={control}
          render={({ field }) => (
            <DatePicker
              selected={field.value ? new Date(field.value) : null}
              onChange={(date: Date | null) => {
                const beirutTime = date
                  ? formatInTimeZone(date, TIMEZONE, "yyyy-MM-dd'T'HH:mm:ssXXX")
                  : null;
                field.onChange(beirutTime);
              }}
              showTimeSelect
              timeFormat="HH:mm"
              timeIntervals={15}
              timeCaption={t(
                "messages.sendMessageModal.placeholders.timeCaption"
              )}
              isClearable
              placeholderText={t(
                "messages.sendMessageModal.placeholders.selectDateTime"
              )}
              dateFormat="MMMM d, yy h:mm aa"
              disabled={values.send_immediately}
              className="form-control"
            />
          )}
        />
      </Form.Group>
    </>
  );
};

// --- Step 4: Summary View Component ---
const Step4Summary: FC<{ values: FormValues }> = ({ values }) => {
  const { t } = useTranslation();
  const {
    template_id,
    message,
    broadcast,
    customer_ids,
    meter_filters,
    bill_filters,
    send_immediately,
    scheduled_at,
  } = values;

  const renderListGroupItem = (label: string, value: React.ReactNode) =>
    value ? (
      <ListGroup.Item className="d-flex justify-content-between align-items-start">
        <div className="ms-2 me-auto">
          <div className="fw-bold">{label}</div>
          {value}
        </div>
      </ListGroup.Item>
    ) : null;

  const renderFilterPills = (
    filters: (SelectOption | string | null | undefined)[]
  ) => (
    <div className="d-flex flex-wrap gap-1 mt-1">
      {filters
        .filter((f) => f)
        .map((filter, index) => (
          <Badge key={index} pill bg="secondary">
            {typeof filter === "string" ? filter : filter?.label}
          </Badge>
        ))}
    </div>
  );

  return (
    <ListGroup>
      {renderListGroupItem(
        t("messages.sendMessageModal.summary.content"),
        template_id ? `Template: ${template_id.label}` : message
      )}
      {renderListGroupItem(
        t("messages.sendMessageModal.summary.audience"),
        broadcast
          ? t("messages.sendMessageModal.summary.allCustomers")
          : customer_ids.length > 0
          ? renderFilterPills(customer_ids)
          : t("messages.sendMessageModal.summary.filteredCustomers")
      )}
      {(meter_filters || bill_filters) && (
        <ListGroup.Item>
          <div className="fw-bold">
            {t("messages.sendMessageModal.summary.activeFilters")}
          </div>
          {meter_filters?.area_ids && meter_filters.area_ids.length > 0 && (
            <div>
              <strong>
                {t("messages.sendMessageModal.step3.areasLabel")}:
              </strong>{" "}
              {renderFilterPills(meter_filters.area_ids)}
            </div>
          )}
          {meter_filters?.package_ids &&
            meter_filters.package_ids.length > 0 && (
              <div>
                <strong>
                  {t("messages.sendMessageModal.step3.packagesLabel")}:
                </strong>{" "}
                {renderFilterPills(meter_filters.package_ids)}
              </div>
            )}
          {meter_filters?.meter_status && (
            <div>
              <strong>
                {t("messages.sendMessageModal.step3.meterStatusLabel")}:
              </strong>{" "}
              {meter_filters.meter_status.label}
            </div>
          )}
          {meter_filters?.package_type && (
            <div>
              <strong>
                {t("messages.sendMessageModal.step3.packageTypeLabel")}:
              </strong>{" "}
              {meter_filters.package_type.label}
            </div>
          )}
          {bill_filters?.payment_status && (
            <div>
              <strong>
                {t("messages.sendMessageModal.step3.paymentStatusLabel")}:
              </strong>{" "}
              {bill_filters.payment_status.label}
            </div>
          )}
          {bill_filters?.due_date && (
            <div>
              <strong>
                {t("messages.sendMessageModal.step3.dueDateLabel")}:
              </strong>{" "}
              {bill_filters.due_date}
            </div>
          )}
          {bill_filters?.payment_method &&
            bill_filters.payment_method.length > 0 && (
              <div>
                <strong>
                  {t("messages.sendMessageModal.step3.paymentMethodLabel")}:
                </strong>{" "}
                {renderFilterPills(bill_filters.payment_method)}
              </div>
            )}
          {bill_filters?.overdue_only && (
            <div>
              <strong>
                {t("messages.sendMessageModal.step3.overdueOnlyLabel")}:
              </strong>{" "}
              {t("common.yes")}
            </div>
          )}
        </ListGroup.Item>
      )}
      {renderListGroupItem(
        t("messages.sendMessageModal.summary.schedule"),
        send_immediately
          ? t("messages.sendMessageModal.summary.immediately")
          : scheduled_at
          ? format(parseISO(scheduled_at), "PPP p")
          : ""
      )}
    </ListGroup>
  );
};

// --- Main Modal Component ---
export const SendMessageModal: FC<SendMessageModalProps> = ({
  show,
  handleClose,
}) => {
  const { t } = useTranslation();
  const { success, handleError } = useAlert();
  const navigate = useNavigate();
  const sendMessageSchema = useSendMessageSchema();
  const [step, setStep] = useState(1);

  const [isCheckingStatus, setIsCheckingStatus] = useState(true);
  const [sessionStatus, setSessionStatus] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
    trigger,
  } = useForm<FormValues>({
    resolver: zodResolver(sendMessageSchema),
    mode: "onBlur", // Use onBlur or onChange for live feedback
    defaultValues: {
      template_id: null,
      message: "",
      broadcast: false,
      customer_ids: [],
      meter_filters: {
        area_ids: [],
        package_ids: [],
        meter_status: null,
        package_type: null,
      },
      bill_filters: {
        payment_status: null,
        due_date: null,
        payment_method: [],
        overdue_only: false,
      },
      scheduled_at: null,
      send_immediately: true,
    },
  });

  const values = watch();

  useEffect(() => {
    const checkSession = async () => {
      setIsCheckingStatus(true);
      try {
        const response = await getSessionStatus();
        if (response) {
          setSessionStatus(response);
        } else {
          setSessionStatus("disconnected");
        }
      } catch (error) {
        // Any error (like 404) means the session is not connected
        setSessionStatus("disconnected");
        console.error("Failed to get session status:", error);
      } finally {
        setIsCheckingStatus(false);
      }
    };

    if (show) {
      checkSession();
    } else {
      // Reset state when modal closes
      setSessionStatus(null);
      setIsCheckingStatus(true);
    }
  }, [show]);

  const stepTitles = [
    t("messages.sendMessageModal.step1.header"),
    t("messages.sendMessageModal.step2.header"),
    t("messages.sendMessageModal.step3.header"),
    t("messages.sendMessageModal.summary.header"),
  ];

  const stepErrorPaths: { [key: number]: string[] } = {
    1: ["template_id", "message", "messageContent"],
    2: [
      "broadcast",
      "customer_ids",
      "meter_filters.area_ids",
      "bill_filters.due_date",
      "audience",
    ],
    3: ["send_immediately", "scheduled_at", "schedule"],
  };

  const errorMessages = getErrorMessagesForPaths(
    errors,
    stepErrorPaths[step] || []
  );

  const handleModalClose = () => {
    reset();
    setStep(1);
    handleClose();
  };

  const handleNext = async () => {
    const fieldsToValidate = stepErrorPaths[step] as (keyof FormValues)[];
    const isValid = await trigger(fieldsToValidate);
    if (isValid) {
      setStep((prev) => prev + 1);
    }
  };

  const handleBack = () => setStep((prev) => prev - 1);

  const onSubmit = async (data: FormValues) => {
    try {
      const apiPayload: SendMessagePayload = {
        template_id: data.template_id?.value,
        message: data.message,
        broadcast: data.broadcast,
        customer_ids: data.customer_ids.map((c) => c.value),
        meter_filters: {
          area_ids: data.meter_filters?.area_ids.map((a) => a.value),
          package_ids: data.meter_filters?.package_ids.map((p) => p.value),
          meter_status: data.meter_filters?.meter_status?.value as any,
          package_type: data.meter_filters?.package_type?.value as any,
        },
        bill_filters: {
          payment_status: data.bill_filters?.payment_status?.value as any,
          due_date: data.bill_filters?.due_date,
          payment_method: data.bill_filters?.payment_method.map(
            (p) => p.value as any
          ),
          overdue_only: data.bill_filters?.overdue_only,
        },
        scheduled_at: data.scheduled_at ?? undefined,
        send_immediately: data.send_immediately,
      };

      const payload = cleanPayload(apiPayload);
      // Ensure booleans are always present if they are part of the core logic
      payload.send_immediately = data.send_immediately;
      payload.broadcast = data.broadcast;
      if (data.bill_filters) {
        payload.bill_filters = payload.bill_filters;

        if (data.bill_filters.overdue_only) {
          payload.bill_filters.overdue_only = true;
        }
      }

      await sendMessage(payload);
      success(t("messages.sendMessageModal.alerts.success"));
      handleModalClose();
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <Modal show={show} onHide={handleModalClose} size="lg" backdrop="static">
      <Form noValidate onSubmit={handleSubmit(onSubmit)}>
        <Modal.Header closeButton>
          <Modal.Title>
            {t("messages.sendMessageModal.title")} - {stepTitles[step - 1]}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ minHeight: "400px" }}>
          {isCheckingStatus ? (
            <div className="d-flex justify-content-center align-items-center h-100">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading...</span>
              </Spinner>
            </div>
          ) : sessionStatus === "connected" ? (
            <>
              {/* All the existing step content goes here */}
              {step === 1 && (
                <Step1MessageContent
                  control={control}
                  errors={errors}
                  values={values}
                />
              )}
              {step === 2 && (
                <Step2TargetAudience
                  control={control}
                  errors={errors}
                  values={values}
                  setValue={setValue}
                />
              )}
              {step === 3 && (
                <Step3Scheduling
                  control={control}
                  errors={errors}
                  values={values}
                  setValue={setValue}
                />
              )}
              {step === 4 && <Step4Summary values={values} />}

              {errorMessages.length > 0 && (
                <Alert variant="danger" className="mt-4">
                  <ul className="mb-0 ps-3">
                    {errorMessages.map((msg, i) => (
                      <li key={i}>{msg}</li>
                    ))}
                  </ul>
                </Alert>
              )}
            </>
          ) : (
            <Alert variant="warning" className="text-center">
              <Alert.Heading>
                <i className="bi bi-exclamation-triangle-fill me-2"></i>
                {t("messages.sendMessageModal.session.notConnectedTitle")}
              </Alert.Heading>
              <p>
                {t("messages.sendMessageModal.session.notConnectedMessage")}
              </p>
              <hr />
              <Button
                variant="primary"
                onClick={() => {
                  navigate("/manage-phone-number");
                  handleModalClose();
                }}
              >
                {t("messages.sendMessageModal.session.connectButton")}
              </Button>
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleModalClose}>
            {t("common.cancel")}
          </Button>
          {sessionStatus === "connected" && (
            <>
              {step > 1 && (
                <Button variant="outline-primary" onClick={handleBack}>
                  {t("common.back")}
                </Button>
              )}
              {step < 4 && (
                <Button variant="primary" onClick={handleNext}>
                  {t("common.next")}
                </Button>
              )}
              {step === 4 && (
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Spinner
                        as="span"
                        animation="border"
                        size="sm"
                        role="status"
                        className="me-1"
                      />
                      {t("common.sending")}
                    </>
                  ) : (
                    t("messages.sendMessageModal.sendMessageButton")
                  )}
                </Button>
              )}
            </>
          )}
        </Modal.Footer>
      </Form>
    </Modal>
  );
};
