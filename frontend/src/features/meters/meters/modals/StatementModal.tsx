import { useState, useEffect, useCallback, useRef } from "react";
import {
  Modal,
  Button,
  Row,
  Col,
  Table,
  Spinner,
  Alert,
  Form,
  Card,
} from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useAlert } from "../../../hooks/useAlert";
import type { StatementData } from "../types";
import type { Meter } from "../types";
import { formatCurrency, formatNumber } from "../../../utils/formatters";
import html2canvas from "html2canvas";
import { getStatement } from "../metersService";

import { lazy, Suspense } from "react";
const UpdateBillModal = lazy(() =>
  import("../../bills/modals/UpdateBillModal").then((module) => ({
    default: module.UpdateBillModal,
  }))
);
const PayAllUnpaidBillsModal = lazy(() =>
  import("./PayAllUnpaidBillsModal").then((module) => ({
    default: module.PayAllUnpaidBillsModal,
  }))
);

interface StatementModalProps {
  show: boolean;
  handleClose: () => void;
  meter: Meter | null;
}

export const StatementModal = ({
  show,
  handleClose,
  meter,
}: StatementModalProps) => {
  const { t } = useTranslation();
  const { handleError } = useAlert();
  const printRef = useRef<HTMLDivElement>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [statementData, setStatementData] = useState<StatementData | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [isPrinting, setIsPrinting] = useState(false);

  // You would manage the payment modal state here
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedBillId, setSelectedBillId] = useState<string | null>(null);

  const [showPayAllModal, setShowPayAllModal] = useState(false);

  const fetchStatement = useCallback(async () => {
    if (!meter) return;

    setIsLoading(true);
    setError(null);
    try {
      const data = await getStatement(meter.meter_id, selectedYear);
      setStatementData(data);
    } catch (err) {
      setError(t("meters.statementModal.errors.fetchFailed"));
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  }, [meter, selectedYear, handleError, t]);

  useEffect(() => {
    if (show) {
      fetchStatement();
    } else {
      // Reset state on close
      setStatementData(null);
      setSelectedYear(new Date().getFullYear());
    }
  }, [show, fetchStatement]);

  const handlePrint = async () => {
    const element = printRef.current;
    if (!element) return;

    setIsPrinting(true);
    try {
      const canvas = await html2canvas(element, {
        scale: 2, // Higher scale for better quality
      });
      const data = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = data;
      link.download = `statement-${meter?.customer_full_name}-${selectedYear}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      handleError(err);
    } finally {
      setIsPrinting(false);
    }
  };

  const generateYearOptions = () => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = currentYear; i >= 2024; i--) {
      years.push(
        <option key={i} value={i}>
          {i}
        </option>
      );
    }
    return years;
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="text-center p-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">{t("common.loading")}</span>
          </Spinner>
        </div>
      );
    }

    if (error) {
      return <Alert variant="danger">{error}</Alert>;
    }

    if (!statementData) {
      return (
        <Alert variant="info">
          {t("meters.statementModal.noDataAvailable")}
        </Alert>
      );
    }

    const { meter_info, year_summary, months } = statementData;

    return (
      <div ref={printRef} className="p-3 bg-white">
        {/* Customer Info for Print View */}
        <div className="d-none d-print-block mb-3">
          <h4>
            {t("meters.statementModal.title")} - {selectedYear}
          </h4>
          <p>
            <strong>{t("meters.statementModal.customer")}:</strong>{" "}
            {meter_info.customer_name}
          </p>
          <p>
            <strong>{t("meters.statementModal.phone")}:</strong>{" "}
            {meter_info.customer_phone}
          </p>
        </div>

        <Card className="mb-4">
          <Card.Header as="h5">
            {t("meters.statementModal.yearSummaryTitle")}
          </Card.Header>
          <Card.Body>
            <Row>
              <Col>
                <strong>{t("meters.statementModal.totalBilled")}:</strong>{" "}
                {formatCurrency(year_summary.total_billed_usd, "USD")}
              </Col>
            </Row>
            <Row>
              <Col>
                <strong>{t("meters.statementModal.totalPaid")}:</strong>{" "}
                {formatCurrency(year_summary.total_paid_usd, "USD")}
              </Col>
            </Row>
            <Row>
              <Col>
                <strong>{t("meters.statementModal.totalUnpaid")}:</strong>{" "}
                <span className="text-danger">
                  {formatCurrency(year_summary.total_unpaid_usd, "USD")}
                </span>
              </Col>
            </Row>
            <Row>
              <Col>
                <strong>{t("meters.statementModal.totalFixes")}:</strong>{" "}
                {formatCurrency(year_summary.total_fixes_cost, "USD")}
              </Col>
            </Row>
            <Row>
              <Col>
                <strong>{t("meters.statementModal.completionRate")}:</strong>{" "}
                {year_summary.payment_completion_rate.toFixed(2)}%
              </Col>
            </Row>
          </Card.Body>
        </Card>

        <h5 className="mb-3">{t("meters.statementModal.monthlyBreakdown")}</h5>
        <Table responsive striped bordered hover size="sm">
          <thead>
            <tr>
              <th>{t("meters.statementModal.month")}</th>
              <th>{t("meters.statementModal.amountUsd")}</th>
              <th>{t("meters.statementModal.unpaidUsd")}</th>
              <th>{t("meters.statementModal.prevReading")}</th>
              <th>{t("meters.statementModal.currentReading")}</th>
              <th>{t("meters.statementModal.usage")}</th>
              <th>{t("meters.statementModal.kwhRate")}</th>
              <th>{t("meters.statementModal.dollarRate")}</th>
              <th>{t("meters.statementModal.activationFee")}</th>
              <th>{t("meters.statementModal.fixes")}</th>
              <th>{t("meters.statementModal.status")}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {months.map((month) => (
              <tr key={month.month}>
                <td>{t(`months.${month.month_name.toLowerCase()}`)}</td>
                {month.bill_exists ? (
                  <>
                    <td>{formatCurrency(month.amount_due_usd, "USD")}</td>
                    <td>{formatCurrency(month.unpaid_usd, "USD")}</td>
                    <td>{formatNumber(month.previous_reading)}</td>
                    <td>{formatNumber(month.current_reading)}</td>
                    <td>{month.usage}</td>
                    <td>{formatCurrency(month.kwh_rate, "LBP")}</td>
                    <td>{formatCurrency(month.dollar_rate, "LBP")}</td>
                    <td>{formatCurrency(month.activation_fee, "LBP")}</td>
                    <td>{month.fixes_cost.toFixed(2)} $</td>
                    <td>
                      <span
                        className={`badge bg-${
                          month.status === "paid"
                            ? "success"
                            : month.status === "unpaid"
                            ? "danger"
                            : "warning"
                        }`}
                      >
                        {t(`meters.statementModal.billStatus.${month.status}`)}
                      </span>
                    </td>
                    <td>
                      {month.status !== "paid" && (
                        <Button
                          variant="success"
                          onClick={() => {
                            setSelectedBillId(month.bill_id);
                            setShowPaymentModal(true);
                          }}
                          disabled={isLoading || !!error || !month.bill_id}
                        >
                          {t("meters.statementModal.payBill")}
                        </Button>
                      )}
                    </td>
                  </>
                ) : (
                  <td colSpan={11} className="text-center text-muted">
                    {t("meters.statementModal.noBillExists")}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    );
  };

  return (
    <>
      <Modal show={show} onHide={handleClose} size="xl" centered>
        <Modal.Header closeButton>
          <Modal.Title as="h5">{t("meters.statementModal.title")}</Modal.Title>
        </Modal.Header>
        <Modal.Body className="bg-light">
          <Row className="align-items-center mb-3 p-3 bg-white rounded-2">
            <Col md={8}>
              <div>
                <strong>{t("meters.statementModal.customer")}: </strong>
                {statementData?.meter_info.customer_name ||
                  meter?.customer_full_name}
              </div>
              <div>
                <strong>{t("meters.statementModal.phone")}: </strong>
                {statementData?.meter_info.customer_phone ||
                  meter?.customer_phone_number}
              </div>
            </Col>
            <Col md={4}>
              <Form.Group controlId="yearSelect">
                <Form.Label className="fw-bold">
                  {t("meters.statementModal.selectYear")}
                </Form.Label>
                <Form.Select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(Number(e.target.value))}
                  disabled={isLoading}
                >
                  {generateYearOptions()}
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>
          {renderContent()}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            {t("common.close")}
          </Button>
          <Button
            variant="info"
            onClick={() => {
              setShowPayAllModal(true);
            }}
            disabled={isLoading || !!error}
          >
            {t("meters.statementModal.payBills")}
          </Button>
          <Button
            variant="success"
            onClick={handlePrint}
            disabled={isLoading || isPrinting || !!error}
          >
            {isPrinting ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                />{" "}
                {t("meters.statementModal.printing")}
              </>
            ) : (
              t("meters.statementModal.printStatement")
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Example of how you'd render the Payment Modal */}
      <Suspense fallback={<div>Loading...</div>}>
        {meter && (
          <UpdateBillModal
            show={showPaymentModal}
            handleClose={() => {
              setShowPaymentModal(false);
              setSelectedBillId(null);
              fetchStatement();
            }}
            billId={selectedBillId}
            customerName={meter.customer_full_name}
          />
        )}
        {meter && (
          <PayAllUnpaidBillsModal
            show={showPayAllModal}
            handleClose={() => setShowPayAllModal(false)}
            meterId={meter.meter_id}
            onSuccess={() => {
              setShowPayAllModal(false); // Close the modal
              fetchStatement(); // And refresh the statement data
            }}
          />
        )}
      </Suspense>
    </>
  );
};
