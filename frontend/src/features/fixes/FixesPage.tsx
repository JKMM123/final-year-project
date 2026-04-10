import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  lazy,
  Suspense,
} from "react";
import { useTranslation, Trans } from "react-i18next";
import {
  Card,
  Button,
  Table,
  Row,
  Col,
  Form,
  InputGroup,
  Spinner,
} from "react-bootstrap";
import { debounce } from "lodash";
import type { Fix } from "./types";
import { getFixes, deleteFix } from "./fixesService";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";

const FixModal = lazy(() =>
  import("./modals/FixModal").then((module) => ({
    default: module.FixModal,
  }))
);

const getCurrentMonthString = () => new Date().toISOString().slice(0, 7);

const FixesPage = () => {
  const { t } = useTranslation();
  const [fixes, setFixes] = useState<Fix[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonthString());

  // A single state to control modal visibility
  const [showFixModal, setShowFixModal] = useState(false);
  // State to hold the fix being edited. If null, modal is in "create" mode.
  const [fixToEdit, setFixToEdit] = useState<Fix | null>(null);
  // State for the delete confirmation modal
  const [fixToDelete, setFixToDelete] = useState<Fix | null>(null);

  const { success, handleError } = useAlert();

  const fetchFixes = useCallback(
    async (page: number, query: string, month: string) => {
      setIsLoading(true);
      try {
        const fix_date = `${month}-01`;
        const response = await getFixes({ page, limit: 10, query, fix_date });
        setFixes(response.items);
        setPagination(response.pagination);
      } catch (err: any) {
        handleError(err);
      } finally {
        setIsLoading(false);
      }
    },
    [handleError]
  );

  const debouncedFetch = useMemo(
    () =>
      debounce((query: string, month: string) => {
        setCurrentPage(1);
        fetchFixes(1, query, month);
      }, 500),
    [fetchFixes]
  );

  useEffect(() => {
    fetchFixes(currentPage, searchQuery, selectedMonth);
  }, [currentPage, selectedMonth, fetchFixes]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedFetch(query, selectedMonth);
  };

  const handleMonthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let month = e.target.value;
    if (!month) {
      month = getCurrentMonthString();
    }
    setSelectedMonth(month);
    setCurrentPage(1);
  };

  const handleDeleteFix = async () => {
    if (!fixToDelete) return;
    setIsDeleting(true);
    try {
      await deleteFix(fixToDelete.fix_id);
      success(
        t("fixes.notifications.deleteSuccess", {
          customerName: fixToDelete.customer_name,
        })
      );
      setFixToDelete(null);
      const newPage =
        fixes.length === 1 && currentPage > 1 ? currentPage - 1 : currentPage;
      setCurrentPage(newPage);
      fetchFixes(newPage, searchQuery, selectedMonth);
    } catch (err) {
      handleError(err);
    } finally {
      setIsDeleting(false);
    }
  };

  // Opens the modal in "Create" mode
  const handleShowCreateModal = () => {
    setFixToEdit(null); // Ensure no fix data is passed
    setShowFixModal(true);
  };

  // Opens the modal in "Edit" mode
  const handleShowEditModal = (fix: Fix) => {
    setFixToEdit(fix);
    setShowFixModal(true);
  };

  // Hides the modal and resets the edit state
  const handleHideModal = () => {
    setShowFixModal(false);
    setFixToEdit(null);
  };

  // Handles successful creation or update
  const handleModalSuccess = () => {
    handleHideModal();
    // Refresh data to show changes
    fetchFixes(1, "", selectedMonth);
    setCurrentPage(1);
    setSearchQuery("");
  };

  return (
    <>
      <Card>
        <Card.Header>
          <Row className="align-items-center justify-content-between g-2">
            <Col md={5}>
              <Card.Title as="h5" className="mb-1">
                {t("fixes.title")}
              </Card.Title>
            </Col>
            <Col md={7} className="d-flex justify-content-end">
              <Button variant="primary" onClick={handleShowCreateModal}>
                <i className="bi bi-plus-lg mx-2"></i>
                {t("fixes.addFix")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Row className="mb-3 g-2">
            <Col md={5}>
              <InputGroup>
                <Form.Control
                  placeholder={t("fixes.searchPlaceholder")}
                  value={searchQuery}
                  onChange={handleSearchChange}
                />
              </InputGroup>
            </Col>
            <Col md={4}>
              <InputGroup>
                <InputGroup.Text>{t("common.month")}</InputGroup.Text>
                <Form.Control
                  type="month"
                  value={selectedMonth}
                  onChange={handleMonthChange}
                />
              </InputGroup>
            </Col>
          </Row>

          {isLoading ? (
            <SkeletonTable cols={4} />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("fixes.table.customerName")}</th>
                  <th>{t("fixes.table.fixDate")}</th>
                  <th>{t("fixes.table.cost")} $</th>
                  <th>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {fixes.length > 0 ? (
                  fixes.map((fix) => (
                    <tr key={fix.fix_id}>
                      <td>{fix.customer_name}</td>
                      <td>{fix.fix_date}</td>
                      <td>${fix.cost.toLocaleString(undefined)}</td>
                      <td>
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          className="me-2"
                          onClick={() => handleShowEditModal(fix)}
                        >
                          <i className="bi bi-pencil"></i>
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => setFixToDelete(fix)}
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center">
                      {t("fixes.noFixesFound")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && fixes.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>

      {/* Lazy-loaded component MUST be wrapped in Suspense */}
      <Suspense fallback={<Spinner animation="border" />}>
        <FixModal
          show={showFixModal}
          onHide={handleHideModal}
          onSuccess={handleModalSuccess}
          fix={fixToEdit}
        />
      </Suspense>

      {fixToDelete && (
        <ConfirmationModal
          show={!!fixToDelete}
          title={t("fixes.deleteModal.title")}
          body={
            <Trans
              i18nKey="fixes.deleteModal.body"
              values={{
                customerName: fixToDelete.customer_name,
                fixDate: fixToDelete.fix_date,
              }}
              components={{ strong: <strong /> }}
            />
          }
          onConfirm={handleDeleteFix}
          onHide={() => setFixToDelete(null)}
          isConfirming={isDeleting}
          confirmText={t("fixes.deleteModal.confirmText")}
        />
      )}
    </>
  );
};

export default FixesPage;
