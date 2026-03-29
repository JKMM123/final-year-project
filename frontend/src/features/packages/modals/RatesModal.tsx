// src/features/packages/components/ViewRatesModal.tsx
import { useEffect, useState, useMemo, useCallback } from "react";
import { Modal, Button, Table, Spinner, Alert, Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAlert } from "../../../hooks/useAlert";
import type { MonthlyRate } from "../types";
import { getRatesByYear } from "../packagesService";

interface ViewRatesModalProps {
  show: boolean;
  handleClose: () => void;
}

const ViewRatesModal = ({ show, handleClose }: ViewRatesModalProps) => {
  const { t } = useTranslation();
  const { handleError } = useAlert();
  const navigate = useNavigate();

  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [rates, setRates] = useState<MonthlyRate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generate a list of years for the dropdown (e.g., current year +/- 5 years)
  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = currentYear + 5; i >= currentYear - 5; i--) {
      years.push(i);
    }
    return years;
  }, []);

  const fetchRates = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedRates = await getRatesByYear(selectedYear);
      setRates(fetchedRates);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.message || t("rates.viewModal.fetchError");
      setError(errorMessage);
      handleError(errorMessage); // Optionally show a toast notification
    } finally {
      setIsLoading(false);
    }
  }, [selectedYear, t, handleError]);

  useEffect(() => {
    if (show) {
      fetchRates();
    }
  }, [show, fetchRates]);

  const handleNavigate = () => {
    handleClose(); // Close the modal first
    navigate("/bills"); // Then navigate
  };

  // Helper to format numbers with thousand separators
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="d-flex justify-content-center align-items-center p-5">
          <Spinner animation="border" />
        </div>
      );
    }
    if (error) {
      return <Alert variant="danger">{error}</Alert>;
    }
    if (rates.length === 0) {
      return <Alert variant="info">{t("rates.viewModal.noRates")}</Alert>;
    }
    return (
      <Table striped bordered hover responsive size="sm">
        <thead>
          <tr>
            <th>{t("rates.viewModal.table.month")}</th>
            <th>{t("rates.viewModal.table.mountainRate")}</th>
            <th>{t("rates.viewModal.table.coastalRate")}</th>
            <th>{t("rates.viewModal.table.dollarRate")}</th>
          </tr>
        </thead>
        <tbody>
          {rates.map((rate) => (
            <tr key={rate.rate_id}>
              <td>{t(`months.${rate.rate_month.toLowerCase()}`)}</td>
              <td>{formatNumber(rate.mountain_kwh_rate)}</td>
              <td>{formatNumber(rate.coastal_kwh_rate)}</td>
              <td>{formatNumber(rate.dollar_rate)}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  };

  return (
    <Modal show={show} onHide={handleClose} centered size="lg">
      <Modal.Header closeButton>
        <Modal.Title>{t("rates.viewModal.title")}</Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ maxHeight: "60vh", overflowY: "auto" }}>
        <Form.Group controlId="yearSelector" className="mb-3">
          <Form.Label>{t("rates.viewModal.yearLabel")}</Form.Label>
          <Form.Select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
          >
            {yearOptions.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        {renderContent()}
      </Modal.Body>
      <Modal.Footer className="d-flex justify-content-between align-items-center">
        <small className="text-muted">
          {t("rates.viewModal.footerMessage.part1")}{" "}
          <span
            className="text-primary"
            onClick={handleNavigate}
            style={{ cursor: "pointer", textDecoration: "underline" }}
          >
            {t("rates.viewModal.footerMessage.link")}
          </span>
          .
        </small>
        <Button variant="secondary" onClick={handleClose}>
          {t("common.close")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ViewRatesModal;
