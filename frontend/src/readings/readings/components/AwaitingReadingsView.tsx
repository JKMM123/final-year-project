// AwaitingReadingsView.tsx

import { useState, useEffect, useMemo, useCallback } from "react";
import { Card, Button, Table, Row, Col, Form } from "react-bootstrap";
import Select from "react-select";
import { debounce } from "lodash";
import { useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { MeterForReading } from "../types";
import type { Area } from "../../areas/types";
import { getMetersAwaitingReading } from "../readingsService";
import { useAlert } from "../../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../../components/common/SkeletonTable";
import { Pagination } from "../../../components/common/Pagination";
import { getDefaultMonth } from "../../../utils/dateHelpers";
interface AwaitingReadingsViewProps {
  areas: Area[];
  refreshSummary: () => void;
  currentMonth: string;
  onDateChange: (date: string) => void;
  refreshTrigger?: number; // 👈 optional prop
}

export const AwaitingReadingsView = ({
  areas,
  currentMonth,
  onDateChange,
  refreshTrigger,
}: AwaitingReadingsViewProps) => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [meters, setMeters] = useState<MeterForReading[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  const [filters, setFilters] = useState({
    query: "",
    area_ids: [] as string[],
    reading_date: currentMonth,
  });
  const { handleError } = useAlert();

  const fetchMeters = useCallback(
    async (page: number, currentFilters: typeof filters) => {
      setIsLoading(true);
      try {
        const response = await getMetersAwaitingReading({
          page,
          limit: 10,
          ...currentFilters,
          status: ["awaiting_reading"],
        });
        setMeters(response.items);
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
    fetchMeters(currentPage, filters);
  }, [currentPage, filters, fetchMeters, refreshTrigger]);

  useEffect(() => {
    const handleRefetch = () => {
      fetchMeters(currentPage, filters);
    };

    window.addEventListener("refetch-awaiting-readings", handleRefetch);
    return () => {
      window.removeEventListener("refetch-awaiting-readings", handleRefetch);
    };
  }, [currentPage, filters, fetchMeters]);

  const debouncedSearch = useMemo(
    () =>
      debounce(
        (query: string) => setFilters((prev) => ({ ...prev, query })),
        500
      ),
    []
  );

  const areaOptions = useMemo(
    () => areas.map((a) => ({ value: a.area_id, label: a.area_name })),
    [areas]
  );

  return (
    <>
      <Card>
        <Card.Body>
          <Row className="mb-3 g-2">
            <Col md={4}>
              <Form.Control
                placeholder={t(
                  "readings.awaitingView.searchByCustomerNamePlaceholder"
                )}
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </Col>
            <Col md={4}>
              <Select
                options={areaOptions}
                isClearable
                isSearchable={false}
                placeholder={t("readings.awaitingView.filterByAreaPlaceholder")}
                onChange={(option) =>
                  setFilters((prev) => ({
                    ...prev,
                    area_ids: option ? [option.value] : [],
                  }))
                }
              />
            </Col>
            <Col md={4}>
              <Form.Control
                type="month"
                value={filters.reading_date}
                onChange={(e) => {
                  const newMonth = e.target.value || getDefaultMonth();
                  setFilters((prev) => ({ ...prev, reading_date: newMonth }));
                  onDateChange(newMonth);
                }}
                style={{ textAlign: i18n.dir() === "rtl" ? "right" : "left" }}
              />
            </Col>
          </Row>
          {isLoading ? (
            <SkeletonTable cols={4} />
          ) : (
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>{t("readings.awaitingView.customerName")}</th>
                  <th>{t("readings.awaitingView.area")}</th>
                  <th>{t("readings.awaitingView.previousReading")}</th>
                  <th>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {meters.length > 0 ? (
                  meters.map((meter) => (
                    <tr key={meter.meter_id}>
                      <td>{meter.customer_full_name}</td>
                      <td>{meter.area_name}</td>
                      <td>
                        {meter.previous_reading?.toFixed(2) ??
                          t("common.notAvailable")}{" "}
                        kWh
                      </td>
                      <td className="d-flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline-secondary"
                          onClick={() =>
                            navigate(
                              `/readings/add-reading/${meter.meter_id}`,
                              {
                                state: { backgroundLocation: location, meter },
                              }
                            )
                          }
                          title={t("readings.awaitingView.manualEntry")}
                        >
                          <i className="bi bi-keyboard"></i>
                          <span className="mx-1">
                            {t("readings.awaitingView.addReading")}
                          </span>
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center">
                      {t("readings.awaitingView.noMetersAwaiting")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && meters.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>
    </>
  );
};

export default AwaitingReadingsView;
