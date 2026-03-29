// src/pages/Bills/BillsPage.tsx

import {
  useState,
  useEffect,
  useCallback,
  useMemo,
  lazy,
  Suspense,
} from "react";
import {
  Card,
  Button,
  Table,
  Row,
  Col,
  Form,
  Badge,
  Spinner,
} from "react-bootstrap";
import Select from "react-select";
import { debounce } from "lodash";
import { useTranslation } from "react-i18next";

import type { Bill, BillSearchPayload, BillStatus } from "./types";
import { getBills, deleteBill } from "./billsService";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";
import { useTask } from "../../context/TaskContext";
import { getDefaultMonth } from "../../utils/dateHelpers";

const GenerateBillsModal = lazy(() =>
  import("./modals/GenerateBillsModal").then((module) => ({
    default: module.GenerateBillsModal,
  }))
);

const UpdateBillModal = lazy(() =>
  import("./modals/UpdateBillModal").then((module) => ({
    default: module.UpdateBillModal,
  }))
);

const DownloadBillsModal = lazy(() =>
  import("./modals/DownloadBillsModal").then((module) => ({
    default: module.DownloadBillsModal,
  }))
);

const BillsPage = () => {
  const { t, i18n } = useTranslation();
  const [bills, setBills] = useState<Bill[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const { taskId, taskStatus, clearTask } = useTask();

  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<
    Omit<BillSearchPayload, "page" | "limit">
  >({
    due_date: getDefaultMonth(),
  });

  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [billToUpdate, setBillToUpdate] = useState<Bill | null>(null);
  const [billToDelete, setBillToDelete] = useState<Bill | null>(null);
  const [showDownloadModal, setShowDownloadModal] = useState(false);

  const { success, handleError } = useAlert();

  const fetchBills = useCallback(
    async (page: number, currentFilters: typeof filters) => {
      setIsLoading(true);
      try {
        const payload = { page, limit: 10, ...currentFilters };
        const response = await getBills(payload);
        setBills(response.items);
        setPagination(response.pagination);
      } catch (err) {
        handleError(err);
      } finally {
        setIsLoading(false);
      }
    },
    [handleError]
  );

  useEffect(() => {
    fetchBills(currentPage, filters);
  }, [currentPage, filters, fetchBills]);

  const debouncedSearch = useMemo(
    () =>
      debounce((query: string) => setFilters((p) => ({ ...p, query })), 500),
    []
  );

  const handleModalClose = (needsRefresh: boolean) => {
    setShowGenerateModal(false);
    setBillToUpdate(null);
    if (needsRefresh) {
      fetchBills(currentPage, filters);
    }
  };

  const handleDeleteBill = async () => {
    if (!billToDelete) return;
    setIsDeleting(true);
    try {
      await deleteBill(billToDelete.bill_id);
      success(t("bills.deleteSuccess"));
      setBillToDelete(null);
      fetchBills(currentPage, filters);
    } catch (err) {
      handleError(err);
    } finally {
      setIsDeleting(false);
    }
  };

  const getStatusBadgeVariant = (status: BillStatus) => {
    switch (status) {
      case "paid":
        return "success";
      case "partially_paid":
        return "warning";
      case "unpaid":
        return "danger";
      default:
        return "secondary";
    }
  };

  const statusOptions = useMemo(
    () => [
      { value: "paid", label: t("bills.statuses.paid") },
      { value: "unpaid", label: t("bills.statuses.unpaid") },
      { value: "partially_paid", label: t("bills.statuses.partially_paid") },
    ],
    [t]
  );

  const paymentMethodOptions = useMemo(
    () => [
      { value: "cash", label: t("bills.paymentMethods.cash") },
      { value: "whish", label: t("bills.paymentMethods.whish") },
      { value: "omt", label: t("bills.paymentMethods.omt") },
    ],
    [t]
  );

  const handleDownloadFile = () => {
    if (taskStatus?.result?.download_url) {
      window.open(taskStatus.result.download_url, "_blank");
      clearTask();
    }
  };

  const renderDownloadStatusButton = () => {
    if (!taskId) return null;

    if (taskStatus?.status === "PENDING") {
      return (
        <Button variant="outline-primary" disabled className="me-2">
          <Spinner
            as="span"
            animation="border"
            size="sm"
            role="status"
            aria-hidden="true"
            className="me-2"
          />
          {t("bills.downloadInProgress")}
        </Button>
      );
    }

    if (taskStatus?.status === "SUCCESS") {
      return (
        <Button variant="success" onClick={handleDownloadFile} className="me-2">
          <i className="bi bi-check-circle-fill me-2"></i>
          {t("bills.downloadReadyFile")}
        </Button>
      );
    }
    return null;
  };

  return (
    <>
      <Card>
        <Card.Header>
          <Row className="align-items-center">
            <Col md={5}>
              <Card.Title as="h5" className="mb-0">
                {t("bills.title")}
              </Card.Title>
            </Col>
            <Col
              md={7}
              className="d-flex justify-content-end gap-2 g-3 flex-column flex-md-row"
            >
              {renderDownloadStatusButton()}

              <Button
                variant="primary"
                onClick={() => setShowDownloadModal(true)}
              >
                <i className="bi bi-download mx-2"></i>
                {t("bills.downloadBills")}
              </Button>
              <Button
                variant="danger"
                onClick={() => setShowGenerateModal(true)}
              >
                <i className="bi bi-lightning-charge-fill mx-2"></i>
                {t("bills.generateBills")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Row className="g-2 mb-3">
            <Col md={3}>
              <Form.Control
                type="month"
                style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
                value={filters.due_date?.substring(0, 7) || ""}
                onChange={(e) => {
                  if (!e.target.value) {
                    // If user clicks "clear", reset to default month instead of empty
                    setFilters((p) => ({
                      ...p,
                      due_date: getDefaultMonth(),
                    }));
                    return;
                  }

                  const [year, month] = e.target.value.split("-");
                  setFilters((p) => ({
                    ...p,
                    due_date: `${year}-${month}`,
                  }));
                }}
              />
            </Col>
            <Col md={3}>
              <Form.Control
                placeholder={t("bills.searchByCustomerPlaceholder")}
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </Col>
            <Col md={3}>
              <Select
                options={statusOptions}
                isClearable
                isSearchable={false}
                placeholder={t("bills.filterByStatusPlaceholder")}
                onChange={(opt) =>
                  setFilters((p) => ({
                    ...p,
                    status: opt ? [opt.value] : [],
                  }))
                }
              />
            </Col>
            <Col md={3}>
              <Select
                options={paymentMethodOptions}
                isMulti
                isSearchable={false}
                isClearable
                placeholder={t("bills.paymentMethodPlaceholder")}
                onChange={(opts) =>
                  setFilters((p) => ({
                    ...p,
                    payment_method: opts.map((o) => o.value),
                  }))
                }
              />
            </Col>
          </Row>
          {isLoading ? (
            <SkeletonTable cols={5} />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("bills.customer")}</th>
                  <th>{t("bills.amountLbp")}</th>
                  <th>{t("bills.amountUsd")}</th>
                  <th>{t("bills.status")}</th>
                  <th>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {bills.length > 0 ? (
                  bills.map((bill) => (
                    <tr key={bill.bill_id}>
                      <td>
                        {bill.customer_full_name || t("common.notAvailable")}
                      </td>
                      <td>
                        {Number(bill.amount_due_lbp).toLocaleString("en-US")}{" "}
                        LBP
                      </td>
                      <td>
                        $
                        {Number(bill.amount_due_usd).toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td>
                        <Badge bg={getStatusBadgeVariant(bill.status)}>
                          {t(`bills.statuses.${bill.status}`)}
                        </Badge>
                      </td>

                      <td>
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          className="mx-2"
                          onClick={() => setBillToUpdate(bill)}
                        >
                          <i className="bi bi-pencil"></i>
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => setBillToDelete(bill)}
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="text-center">
                      {t("bills.noBillsAvailable")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && bills.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>

      <Suspense fallback={<div>{t("common.loading")}</div>}>
        <GenerateBillsModal
          show={showGenerateModal}
          handleClose={handleModalClose}
        />
        {billToUpdate && (
          <UpdateBillModal
            show={!!billToUpdate}
            billId={billToUpdate.bill_id}
            customerName={
              billToUpdate.customer_full_name || t("common.notAvailable")
            }
            handleClose={handleModalClose}
          />
        )}
        <DownloadBillsModal
          show={showDownloadModal}
          handleClose={() => setShowDownloadModal(false)}
        />
      </Suspense>

      {billToDelete && (
        <ConfirmationModal
          show={!!billToDelete}
          title={t("bills.deleteBillTitle")}
          body={<p>{t("bills.deleteConfirmation")}</p>}
          onConfirm={handleDeleteBill}
          onHide={() => setBillToDelete(null)}
          isConfirming={isDeleting}
        />
      )}
    </>
  );
};

export default BillsPage;
