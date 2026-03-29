import { useState, useEffect } from "react";
import {
  Modal,
  Button,
  Form,
  Spinner,
  Image,
  Alert,
  InputGroup,
  Card,
  Row,
  Col,
  ButtonGroup,
} from "react-bootstrap";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";

import { useAlert } from "../../../hooks/useAlert";
import type {
  Bill,
  Payment,
  CreatePaymentPayload,
  UpdatePaymentPayload,
} from "../types";
import {
  getBillById,
  getAllPaymentsForBill,
  createPayment,
  deletePayment,
  updatePayment,
} from "../billsService";
import { ConfirmationModal } from "../../../components/common/ConfirmationModal";

// --- Props for the Main Modal ---
interface UpdateBillModalProps {
  billId: string | null;
  customerName: string;
  show: boolean;
  handleClose: (needsRefresh: boolean) => void;
}

// --- Dynamic Zod Schema Creator (now with i18n support) ---
const createPaymentSchema = (maxAmount: number, t: TFunction) =>
  z.object({
    amount_usd: z
      .number()
      .refine((value) => value !== undefined && value !== null, {
        message: t("bills.updateBillModal.forms.payment.errors.amountRequired"),
      })
      .positive(t("bills.updateBillModal.forms.payment.errors.amountPositive"))
      .max(maxAmount, {
        message: t("bills.updateBillModal.forms.payment.errors.amountMax", {
          max: maxAmount.toFixed(2),
        }),
      }),
    payment_method: z.enum(["cash", "whish", "omt"]),
    payment_date: z
      .string()
      .min(1, t("bills.updateBillModal.forms.payment.errors.dateRequired")),
  });

type PaymentFormValues = z.infer<ReturnType<typeof createPaymentSchema>>;

// ====================================================================
// --- Child Components for Better Organization ---
// ====================================================================

// 1. Image Preview Modal
const ImagePreviewModal = ({
  show,
  onHide,
  imageUrl,
}: {
  show: boolean;
  onHide: () => void;
  imageUrl: string;
}) => {
  const { t } = useTranslation();
  return (
    <Modal show={show} onHide={onHide} size="xl" centered>
      <Modal.Header closeButton>
        <Modal.Title>{t("bills.imagePreviewModal.title")}</Modal.Title>
      </Modal.Header>
      <Modal.Body className="text-center">
        <Image src={imageUrl} fluid />
      </Modal.Body>
    </Modal>
  );
};

// 3. Payment Card with INLINE EDITING
const PaymentCard = ({
  payment,
  isEditing,
  onEdit,
  onCancelEdit,
  onDelete,
  onSave,
  validationMaxAmount,
}: {
  payment: Payment;
  isEditing: boolean;
  onEdit: (paymentId: string) => void;
  onCancelEdit: () => void;
  onDelete: (payment: Payment) => void;
  onSave: (paymentId: string, data: UpdatePaymentPayload) => Promise<void>;
  validationMaxAmount: number;
}) => {
  const { t } = useTranslation();
  const paymentMethods = ["cash", "whish", "omt"];
  const paymentSchema = createPaymentSchema(validationMaxAmount, t);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isValid, isDirty },
  } = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentSchema),
    mode: "onChange",
    defaultValues: {
      amount_usd: parseFloat(payment.amount_usd),
      payment_method: payment.payment_method,
      payment_date: payment.payment_date,
    },
  });

  const handleSave: SubmitHandler<PaymentFormValues> = async (data) => {
    await onSave(payment.payment_id, data);
  };

  if (isEditing) {
    return (
      <Card className="mb-3 border-primary shadow">
        <Card.Body>
          <Form noValidate onSubmit={handleSubmit(handleSave)}>
            <Row className="align-items-start">
              <Col xs={12} sm={4} className="mb-2 mb-sm-0">
                <InputGroup size="sm">
                  <InputGroup.Text>$</InputGroup.Text>
                  <Form.Control
                    type="number"
                    step="0.01"
                    isInvalid={!!errors.amount_usd}
                    {...register("amount_usd", { valueAsNumber: true })}
                  />
                </InputGroup>
                {errors.amount_usd && (
                  <Form.Text className="text-danger">
                    {errors.amount_usd.message}
                  </Form.Text>
                )}
              </Col>
              <Col xs={6} sm={3}>
                <Form.Select size="sm" {...register("payment_method")}>
                  {paymentMethods.map((method) => (
                    <option key={method} value={method}>
                      {t(`updateBillModal.forms.payment.methods.${method}`)}
                    </option>
                  ))}
                </Form.Select>
              </Col>
              <Col xs={6} sm={3}>
                <Form.Control
                  size="sm"
                  type="date"
                  {...register("payment_date")}
                />
              </Col>
              <Col xs={12} sm={2} className="text-end mt-2 mt-sm-0">
                <ButtonGroup size="sm">
                  <Button
                    type="submit"
                    variant="success"
                    disabled={isSubmitting || !isDirty || !isValid}
                  >
                    {isSubmitting ? <Spinner size="sm" /> : t("common.save")}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={onCancelEdit}
                    disabled={isSubmitting}
                  >
                    {t("common.cancel")}
                  </Button>
                </ButtonGroup>
              </Col>
            </Row>
          </Form>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className="mb-3">
      <Card.Body>
        <Row className="align-items-center">
          <Col xs={12} md={7}>
            <div className="d-flex align-items-center">
              <div className="me-3 fs-4">
                {payment.payment_method === "cash" && "💵"}
                {payment.payment_method === "whish" && "📱"}
                {payment.payment_method === "omt" && "🏦"}
              </div>
              <div>
                <span className="fw-bold fs-5">
                  ${parseFloat(payment.amount_usd).toFixed(2)}
                </span>
                <span className="text-muted mx-2">
                  {t("bills.updateBillModal.paymentCard.via")}
                </span>
                <span className="text-capitalize">
                  {t(
                    `bills.updateBillModal.forms.payment.methods.${payment.payment_method}`
                  )}
                </span>
                <small className="d-block text-muted">
                  {t("bills.updateBillModal.paymentCard.paidOn")}{" "}
                  {new Date(payment.payment_date).toLocaleDateString()}
                </small>
              </div>
            </div>
          </Col>
          <Col xs={12} md={5} className="text-md-end mt-2 mt-md-0">
            <ButtonGroup>
              <Button
                variant="outline-primary"
                size="sm"
                className="mx-1"
                onClick={() => onEdit(payment.payment_id)}
              >
                {t("common.edit")}
              </Button>
              <Button
                variant="outline-danger"
                size="sm"
                onClick={() => onDelete(payment)}
              >
                {t("common.delete")}
              </Button>
            </ButtonGroup>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

// 4. Add Payment Form Component
const AddPaymentForm = ({
  billId,
  remainingAmount,
  onPaymentAdded,
  onCancel,
}: {
  billId: string;
  remainingAmount: number;
  onPaymentAdded: () => void;
  onCancel: () => void;
}) => {
  const { success, handleError } = useAlert();
  const { t } = useTranslation();
  const paymentMethods = ["cash", "whish", "omt"];
  const paymentSchema = createPaymentSchema(remainingAmount, t);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting, isValid, isDirty },
  } = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentSchema),
    mode: "onChange",
    defaultValues: {
      payment_method: "cash",
      payment_date: new Date().toISOString().split("bills.T")[0],
    },
  });

  const onAddPaymentSubmit: SubmitHandler<PaymentFormValues> = async (data) => {
    const payload: CreatePaymentPayload = { bill_id: billId, ...data };
    try {
      await createPayment(payload);
      success(t("bills.updateBillModal.alerts.paymentAddedSuccess"));
      onPaymentAdded();
    } catch (err) {
      handleError(err);
    }
  };

  return (
    <Card className="bg-light mt-3">
      <Card.Body>
        <Form noValidate onSubmit={handleSubmit(onAddPaymentSubmit)}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h6>{t("bills.updateBillModal.addPaymentForm.title")}</h6>
            <Button variant="close" onClick={onCancel}></Button>
          </div>
          <Form.Group className="mb-3" controlId="amount_usd">
            <Form.Label>
              {t("bills.updateBillModal.forms.payment.amountLabel")}
            </Form.Label>
            <InputGroup>
              <Form.Control
                type="number"
                step="0.01"
                placeholder={t(
                  "bills.updateBillModal.forms.payment.amountPlaceholder"
                )}
                isInvalid={!!errors.amount_usd}
                {...register("amount_usd", { valueAsNumber: true })}
              />
              <Button
                variant="outline-secondary"
                onClick={() =>
                  setValue("amount_usd", remainingAmount, {
                    shouldValidate: true,
                    shouldDirty: true,
                  })
                }
              >
                {t("bills.updateBillModal.addPaymentForm.payFullBtn")}
              </Button>
              <Form.Control.Feedback type="invalid">
                {errors.amount_usd?.message}
              </Form.Control.Feedback>
            </InputGroup>
          </Form.Group>
          <Row>
            <Col md={6}>
              <Form.Group className="mb-3" controlId="payment_method">
                <Form.Label>
                  {t("bills.updateBillModal.forms.payment.methodLabel")}
                </Form.Label>
                <Form.Select
                  isInvalid={!!errors.payment_method}
                  {...register("payment_method")}
                >
                  {paymentMethods.map((method) => (
                    <option key={method} value={method}>
                      {t(
                        `bills.updateBillModal.forms.payment.methods.${method}`
                      )}
                    </option>
                  ))}
                </Form.Select>
                <Form.Control.Feedback type="invalid">
                  {errors.payment_method?.message}
                </Form.Control.Feedback>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3" controlId="payment_date">
                <Form.Label>
                  {t("bills.updateBillModal.forms.payment.dateLabel")}
                </Form.Label>
                <Form.Control
                  type="date"
                  isInvalid={!!errors.payment_date}
                  {...register("payment_date")}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.payment_date?.message}
                </Form.Control.Feedback>
              </Form.Group>
            </Col>
          </Row>
          <div className="d-flex justify-content-end gap-2">
            <Button variant="secondary" type="button" onClick={onCancel}>
              {t("common.cancel")}
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={isSubmitting || !isDirty || !isValid}
            >
              {isSubmitting
                ? t("bills.updateBillModal.addPaymentForm.addingBtn")
                : t("bills.updateBillModal.addPaymentForm.addPaymentBtn")}
            </Button>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};

// ====================================================================
// --- Main Modal Component ---
// ====================================================================
export const UpdateBillModal = ({
  billId,
  customerName,
  show,
  handleClose,
}: UpdateBillModalProps) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.dir() === "rtl";
  const { success, handleError } = useAlert();

  // --- State Management ---
  const [billDetails, setBillDetails] = useState<Bill | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState<boolean>(false);

  // --- UI State ---
  const [showAddPaymentForm, setShowAddPaymentForm] = useState<boolean>(false);
  const [editingPaymentId, setEditingPaymentId] = useState<string | null>(null);
  const [paymentToDelete, setPaymentToDelete] = useState<Payment | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // --- Derived State ---
  const amountDue = parseFloat(billDetails?.amount_due_usd?.toString() ?? "0");
  const totalPaid = parseFloat(billDetails?.total_paid_usd || "0");
  const remainingAmount = Math.max(0, +(amountDue - totalPaid).toFixed(2));

  // --- Data Fetching Logic ---
  const fetchData = async (currentBillId: string) => {
    if (!billDetails) setIsLoading(true);
    setError(null);
    try {
      const [billData, paymentsData] = await Promise.all([
        getBillById(currentBillId),
        getAllPaymentsForBill(currentBillId),
      ]);
      setBillDetails(billData);
      setPayments(paymentsData);
    } catch (err) {
      setError(t("bills.updateBillModal.updateBillModal.fetchError"));
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (show && billId) {
      fetchData(billId);
    } else {
      setBillDetails(null);
      setPayments([]);
      setEditingPaymentId(null);
      setPaymentToDelete(null);
      setShowAddPaymentForm(false);
    }
  }, [show, billId]);

  // --- Action Handlers ---

  const handlePaymentAdded = () => {
    setShowAddPaymentForm(false);
    if (billId) fetchData(billId);
  };

  const handleUpdatePayment = async (
    paymentId: string,
    data: UpdatePaymentPayload
  ) => {
    if (!billId) return;
    try {
      await updatePayment(paymentId, data);
      success(t("bills.updateBillModal.alerts.paymentUpdatedSuccess"));
      setEditingPaymentId(null);
      fetchData(billId);
    } catch (err) {
      handleError(err);
    }
  };

  const handleConfirmDelete = async () => {
    if (!paymentToDelete || !billId) return;
    setIsDeleting(true);
    try {
      await deletePayment(paymentToDelete.payment_id);
      success(t("bills.updateBillModal.alerts.paymentDeletedSuccess"));
      setPaymentToDelete(null);
      fetchData(billId);
    } catch (err) {
      handleError(err);
    } finally {
      setIsDeleting(false);
    }
  };

  // --- Main Render Logic ---
  const renderContent = () => {
    if (isLoading)
      return (
        <div className="text-center p-5">
          <Spinner animation="border" />
          <p className="mt-2">{t("common.loadingBill")}</p>
        </div>
      );
    if (error)
      return (
        <Modal.Body>
          <Alert variant="danger">{error}</Alert>
        </Modal.Body>
      );
    if (!billDetails) return null;

    return (
      <>
        <Modal.Body>
          {billDetails.bill_url && (
            <div className="mb-4 text-center">
              <Image
                src={billDetails.bill_url}
                thumbnail
                style={{ maxHeight: "150px", cursor: "pointer" }}
                onClick={() => setShowPreview(true)}
              />
            </div>
          )}

          <Card className="mb-3 shadow-sm">
            <Card.Header as="h5">
              {t("bills.updateBillModal.updateBillModal.summary.title")}
            </Card.Header>
            <Card.Body>
              <Row>
                <Col>
                  <strong>
                    {t(
                      "bills.updateBillModal.updateBillModal.summary.totalDue"
                    )}
                  </strong>
                </Col>
                <Col className="text-end">${amountDue.toFixed(2)}</Col>
              </Row>
              <Row>
                <Col>
                  <strong>
                    {t(
                      "bills.updateBillModal.updateBillModal.summary.totalPaid"
                    )}
                  </strong>
                </Col>
                <Col className="text-end">${totalPaid.toFixed(2)}</Col>
              </Row>
              <hr />
              <Row className="text-danger fw-bold fs-5">
                <Col>
                  {t(
                    "bills.updateBillModal.updateBillModal.summary.amountRemaining"
                  )}
                </Col>
                <Col className="text-end">${remainingAmount.toFixed(2)}</Col>
              </Row>
            </Card.Body>
          </Card>

          {!showAddPaymentForm && remainingAmount > 0 && (
            <div className="d-grid mb-3">
              <Button
                variant="success"
                onClick={() => setShowAddPaymentForm(true)}
              >
                + {t("bills.updateBillModal.updateBillModal.addNewPaymentBtn")}
              </Button>
            </div>
          )}
          {showAddPaymentForm && billId && (
            <AddPaymentForm
              billId={billId}
              remainingAmount={remainingAmount}
              onPaymentAdded={handlePaymentAdded}
              onCancel={() => setShowAddPaymentForm(false)}
            />
          )}

          <div className="mt-4">
            <h6>{t("bills.updateBillModal.updateBillModal.paymentHistory")}</h6>
            {payments.length > 0 ? (
              payments.map((p) => {
                const currentPaymentBeingEdited = payments.find(
                  (pay) => pay.payment_id === editingPaymentId
                );
                const maxAmount =
                  remainingAmount +
                  parseFloat(
                    currentPaymentBeingEdited?.amount_usd ?? p.amount_usd
                  );
                return (
                  <PaymentCard
                    key={p.payment_id}
                    payment={p}
                    isEditing={editingPaymentId === p.payment_id}
                    onEdit={(id) => {
                      setShowAddPaymentForm(false);
                      setEditingPaymentId(id);
                    }}
                    onCancelEdit={() => setEditingPaymentId(null)}
                    onDelete={setPaymentToDelete}
                    onSave={handleUpdatePayment}
                    validationMaxAmount={maxAmount}
                  />
                );
              })
            ) : (
              <Alert variant="info">
                {t("bills.updateBillModal.updateBillModal.noPayments")}
              </Alert>
            )}
          </div>
          {remainingAmount <= 0 && !showAddPaymentForm && (
            <Alert variant="success" className="text-center mt-4">
              {t("bills.updateBillModal.updateBillModal.fullyPaid")}
            </Alert>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => handleClose(true)}>
            {t("common.close")}
          </Button>
        </Modal.Footer>
      </>
    );
  };

  return (
    <>
      <Modal
        show={show}
        onHide={() => handleClose(true)}
        centered
        size="lg"
        backdrop={true}
        dir={isRTL ? "rtl" : "ltr"}
      >
        <Modal.Header closeButton>
          <Modal.Title>
            {t("bills.updateBillModal.updateBillModal.title", { customerName })}
          </Modal.Title>
        </Modal.Header>
        {renderContent()}
      </Modal>

      {billDetails?.bill_url && (
        <ImagePreviewModal
          show={showPreview}
          onHide={() => setShowPreview(false)}
          imageUrl={billDetails.bill_url}
        />
      )}

      <ConfirmationModal
        show={!!paymentToDelete}
        title={t("bills.updateBillModal.deleteConfirm.title")}
        body={
          paymentToDelete ? (
            <p>
              {t("bills.updateBillModal.deleteConfirm.body", {
                amount: parseFloat(paymentToDelete.amount_usd).toFixed(2),
              })}
            </p>
          ) : (
            ""
          )
        }
        onConfirm={handleConfirmDelete}
        onHide={() => setPaymentToDelete(null)}
        isConfirming={isDeleting}
        confirmText={t("common.delete")}
      />
    </>
  );
};
