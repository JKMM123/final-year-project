import {
  useState,
  useEffect,
  useMemo,
  useCallback,
  lazy,
  Suspense,
} from "react";
import { Card, Button, Table, Row, Col, Form, Badge } from "react-bootstrap";
import Select from "react-select";
import { debounce } from "lodash";
import { Trans, useTranslation } from "react-i18next"; // Import useTranslation
import type { Reading } from "../types";
import type { Area } from "../../areas/types";
import { getCollectedReadings } from "../readingsService";
import { useAlert } from "../../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../../components/common/SkeletonTable";
import { Pagination } from "../../../components/common/Pagination";
import { getDefaultMonth } from "../../../utils/dateHelpers";
import { ConfirmationModal } from "../../../components/common/ConfirmationModal";
import { deleteReading } from "../readingsService";

const VerifyReadingModal = lazy(() => import("../modals/VerifyReadingModal"));

interface CollectedReadingsViewProps {
  areas: Area[];
  onDateChange: (date: string) => void;
  currentMonth: string;
  refreshTrigger?: number; // 👈 new optional prop
}

export const CollectedReadingsView = ({
  areas,
  onDateChange,
  currentMonth,
  refreshTrigger,
}: CollectedReadingsViewProps) => {
  const { t, i18n } = useTranslation(); // Initialize the translation function
  const [readings, setReadings] = useState<Reading[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [readingToVerify, setReadingToVerify] = useState<Reading | null>(null);
  const [readingToDelete, setReadingToDelete] = useState<Reading | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [filters, setFilters] = useState({
    query: "",
    status: [] as string[],
    area_ids: [] as string[],
    reading_date: currentMonth,
  });

  const { handleError } = useAlert();

  const fetchReadings = useCallback(
    async (page: number, currentFilters: typeof filters) => {
      setIsLoading(true);
      try {
        const payload = {
          page,
          limit: 10,
          ...currentFilters,
          reading_date: currentFilters.reading_date,
        };
        const response = await getCollectedReadings(payload);
        setReadings(response.items);
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
    fetchReadings(currentPage, filters);
  }, [currentPage, filters, fetchReadings, refreshTrigger]);

  const debouncedSearch = useMemo(
    () =>
      debounce((query: string) => setFilters((p) => ({ ...p, query })), 500),
    []
  );

  const areaOptions = useMemo(
    () => areas.map((a) => ({ value: a.area_id, label: a.area_name })),
    [areas]
  );

  const statusOptions = useMemo(
    () => [
      { value: "pending", label: t("common.statuses.pending") },
      { value: "verified", label: t("common.statuses.verified") },
    ],
    [t]
  );

  const handleModalClose = (needsRefresh: boolean) => {
    setReadingToVerify(null);
    if (needsRefresh) {
      fetchReadings(currentPage, filters);
    }
  };

  const handleDelete = async () => {
    if (!readingToDelete) return;
    setIsDeleting(true);
    try {
      await deleteReading(readingToDelete.reading_id);
      setReadingToDelete(null);
      fetchReadings(currentPage, filters);
    } catch (err) {
      handleError(err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Card>
        <Card.Body>
          <Row className="mb-3 g-2">
            <Col md={3}>
              <Form.Control
                placeholder={t("readings.collectedView.searchPlaceholder")}
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </Col>
            <Col md={3}>
              <Select
                options={statusOptions}
                isClearable
                isSearchable={false}
                placeholder={t(
                  "readings.collectedView.statusFilterPlaceholder"
                )}
                onChange={(o) =>
                  setFilters((p) => ({ ...p, status: o ? [o.value] : [] }))
                }
              />
            </Col>
            <Col md={3}>
              <Select
                options={areaOptions}
                isClearable
                isSearchable={false}
                placeholder={t("readings.collectedView.areaFilterPlaceholder")}
                onChange={(o) =>
                  setFilters((p) => ({ ...p, area_ids: o ? [o.value] : [] }))
                }
              />
            </Col>
            <Col md={3}>
              <Form.Control
                type="month"
                value={filters.reading_date}
                onChange={(e) => {
                  const newMonth = e.target.value || getDefaultMonth();
                  setFilters((p) => ({
                    ...p,
                    reading_date: newMonth,
                  }));
                  onDateChange(newMonth);
                }}
                style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
              />
            </Col>
          </Row>
          {isLoading ? (
            <SkeletonTable cols={6} />
          ) : (
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>{t("readings.table.customer")}</th>
                  <th>{t("readings.table.area")}</th>
                  <th>{t("readings.table.previous")}</th>
                  <th>{t("readings.table.current")}</th>
                  <th>{t("readings.table.status")}</th>
                  <th>{t("readings.table.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {readings.length > 0 ? (
                  readings.map((r) => (
                    <tr key={r.reading_id}>
                      <td>{r.customer_full_name}</td>
                      <td>{r.area_name || t("common.notAvailable")}</td>
                      <td>{r.previous_reading.toLocaleString()}</td>
                      <td>{r.current_reading.toLocaleString()}</td>
                      <td>
                        <Badge
                          bg={r.status === "verified" ? "success" : "warning"}
                        >
                          {t(`common.statuses.${r.status}`)}
                        </Badge>
                      </td>
                      <td>
                        <Button
                          size="sm"
                          className="mx-1"
                          variant="outline-primary"
                          onClick={() => setReadingToVerify(r)}
                        >
                          {r.status === "pending"
                            ? t("common.actionsArray.verify")
                            : t("common.actionsArray.view")}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline-danger"
                          onClick={() => setReadingToDelete(r)}
                        >
                          {t("common.delete")}
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="text-center">
                      {t("readings.collectedView.noReadings")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>
      <Suspense fallback={<div>{t("common.loading")}</div>}>
        {readingToVerify && (
          <VerifyReadingModal
            show={!!readingToVerify}
            reading={readingToVerify}
            handleClose={handleModalClose}
          />
        )}
      </Suspense>
      <Suspense fallback={<div>{t("common.loading")}</div>}>
        {readingToDelete && (
          <ConfirmationModal
            show={!!readingToDelete}
            title={t("readings.deleteModal.title")}
            body={
              <Trans
                i18nKey="readings.deleteModal.body"
                values={{ customerName: readingToDelete.customer_full_name }}
                components={{ strong: <strong /> }}
              />
            }
            onConfirm={handleDelete}
            onHide={() => setReadingToDelete(null)}
            isConfirming={isDeleting}
            confirmText={t("common.delete")}
          />
        )}
      </Suspense>
    </>
  );
};
