import {
  useState,
  useEffect,
  useCallback,
  useMemo,
  lazy,
  Suspense,
} from "react";
import { useTranslation, Trans } from "react-i18next";
import { Card, Button, Table, Row, Col, Form, Dropdown } from "react-bootstrap";
import { debounce } from "lodash";
import Select from "react-select";
import type { Meter, MeterSearchPayload } from "./types";
import { getMeters, deleteMeter } from "./metersService";
import { getAreas } from "../areas/areasService";
import { getPackages } from "../packages/packagesService";
import type { Area } from "../areas/types";
import type { Package } from "../packages/types";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";

const MeterFormModal = lazy(() => import("./modals/MeterFormModal"));
const QrCodeModal = lazy(() => import("./modals/QrCodeModal"));
const MeterToolsModal = lazy(() =>
  import("./modals/MeterToolsModal").then((module) => ({
    default: module.MeterToolsModal,
  }))
);
const StatementModal = lazy(() =>
  import("./modals/StatementModal").then((module) => ({
    default: module.StatementModal,
  }))
);

const MetersPage = () => {
  const { t } = useTranslation();
  const [meters, setMeters] = useState<Meter[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  // Filter States
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<
    Omit<MeterSearchPayload, "page" | "limit">
  >({});
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Data for dropdowns
  const [areas, setAreas] = useState<Area[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);

  // Modal States
  const [showMeterModal, setShowMeterModal] = useState(false);
  const [selectedMeter, setSelectedMeter] = useState<Meter | null>(null); // null for Add, Meter object for Edit
  const [meterToDelete, setMeterToDelete] = useState<Meter | null>(null);
  const [meterForStatement, setMeterForStatement] = useState<Meter | null>(
    null
  );
  const [meterForQr, setMeterForQr] = useState<Meter | null>(null);
  const [showToolsModal, setShowToolsModal] = useState(false);
  const { success, handleError } = useAlert();

  // Translated options for react-select
  const statusOptions = useMemo(
    () => [
      { value: "active", label: t("meters.status.active") },
      { value: "inactive", label: t("meters.status.inactive") },
    ],
    [t]
  );

  const packageTypeOptions = useMemo(
    () => [
      { value: "fixed", label: t("meters.packageType.fixed") },
      { value: "usage", label: t("meters.packageType.usage") },
    ],
    [t]
  );

  const selectedPackageType = useMemo(
    () =>
      packageTypeOptions.find(
        (option) => option.value === (filters.package_type || "")
      ),
    [filters.package_type, packageTypeOptions]
  );

  const selectedStatus = useMemo(
    () =>
      statusOptions.find((option) => option.value === (filters.status || "")),
    [filters.status, statusOptions]
  );

  // ... (useMemo hooks for selected options, data fetching logic remains the same) ...
  const fetchMeters = useCallback(
    async (page: number, currentFilters: typeof filters) => {
      setIsLoading(true);
      try {
        const payload: MeterSearchPayload = {
          page,
          limit: 10,
          ...currentFilters,
        };
        const response = await getMeters(payload);
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
  }, [currentPage, filters, fetchMeters]);

  useEffect(() => {
    if (areas.length === 0) {
      getAreas({ page: 1, limit: 20 })
        .then((res) => setAreas(res.items))
        .catch(handleError);
    }
  }, [areas.length, handleError]);

  useEffect(() => {
    if (showAdvancedFilters && packages.length === 0) {
      getPackages({ page: 1, limit: 20 })
        .then((res) => setPackages(res.items))
        .catch(handleError);
    }
  }, [showAdvancedFilters, packages.length, handleError]);

  const debouncedSearch = useMemo(
    () =>
      debounce(
        (query: string) => setFilters((prev) => ({ ...prev, query })),
        500
      ),
    []
  );

  const handleFilterChange = (key: keyof typeof filters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleModalClose = (needsRefresh: boolean) => {
    setShowMeterModal(false);
    setSelectedMeter(null); // Optional: clear selection on close
    if (needsRefresh) {
      // Reset to page 1 with no filters for a clean refresh
      setCurrentPage(1);
      setFilters({});
      fetchMeters(1, {});
    }
  };

  // Function to open the statement modal
  const handleOpenStatementModal = (meter: Meter) => {
    setMeterForStatement(meter);
  };

  const handleDeleteMeter = async () => {
    if (!meterToDelete) return;
    setIsDeleting(true);
    try {
      await deleteMeter(meterToDelete.meter_id);
      success(
        t("meters.notifications.deleteSuccess", {
          customerName: meterToDelete.customer_full_name,
        })
      );
      setMeterToDelete(null);
      fetchMeters(currentPage, filters);
    } catch (err) {
      handleError(err);
    } finally {
      setIsDeleting(false);
    }
  };

  const areaOptions = areas.map((a) => ({
    value: a.area_id,
    label: a.area_name,
  }));
  const packageOptions = packages.map((p) => ({
    value: p.package_id,
    label: `${p.amperage}A`,
  }));

  // Helper functions to open the modal in the correct mode
  const handleOpenAddModal = () => {
    setSelectedMeter(null);
    setShowMeterModal(true);
  };

  const handleOpenEditModal = (meter: Meter) => {
    setSelectedMeter(meter);
    setShowMeterModal(true);
  };

  return (
    <>
      <Card>
        <Card.Header>
          <Row className="align-items-center">
            <Col md={5}>
              <Card.Title as="h5" className="mb-0">
                {t("meters.title")}
              </Card.Title>
            </Col>
            <Col md={7} className="d-flex justify-content-end gap-2 g-3">
              <Button variant="success" onClick={() => setShowToolsModal(true)}>
                <i className="bi bi-tools mx-2"></i>
                {t("meters.tools")}
              </Button>
              <Button variant="primary" onClick={handleOpenAddModal}>
                <i className="bi bi-plus-lg mx-2"></i>
                {t("meters.addMeter")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Row className="g-2 mb-3">
            <Col md={5}>
              <Form.Control
                placeholder={t("meters.searchPlaceholder")}
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </Col>
            <Col md={4}>
              <Select
                options={areaOptions}
                isClearable
                isSearchable={false}
                placeholder={t("meters.filter.area")}
                onChange={(option) =>
                  handleFilterChange("area_ids", option ? [option.value] : [])
                }
              />
            </Col>
            <Col md={3}>
              <Button
                variant="outline-secondary"
                className="w-100"
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              >
                <i className="bi bi-sliders mx-2"></i>
                {t("meters.filter.moreFilters")}
              </Button>
            </Col>
          </Row>

          {showAdvancedFilters && (
            <Card className="p-3 mb-3 bg-light">
              <Row className="g-2">
                <Col md={4}>
                  <Select
                    options={packageOptions}
                    isMulti
                    isSearchable={false}
                    placeholder={t("meters.filter.package")}
                    onChange={(options) =>
                      handleFilterChange(
                        "package_ids",
                        options.map((o) => o.value)
                      )
                    }
                  />
                </Col>
                <Col md={4}>
                  <Select
                    options={packageTypeOptions}
                    isSearchable={false}
                    placeholder={t("meters.filter.packageType")}
                    value={selectedPackageType}
                    onChange={(selectedOption) =>
                      handleFilterChange(
                        "package_type",
                        selectedOption?.value || ""
                      )
                    }
                  />
                </Col>
                <Col md={4}>
                  <Select
                    options={statusOptions}
                    placeholder={t("meters.filter.status")}
                    value={selectedStatus}
                    isSearchable={false}
                    onChange={(selectedOption) =>
                      handleFilterChange("status", selectedOption?.value || "")
                    }
                  />
                </Col>
              </Row>
            </Card>
          )}

          {isLoading ? (
            <SkeletonTable />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("meters.table.customerName")}</th>
                  <th>{t("meters.table.phone")}</th>
                  <th>{t("meters.table.address")}</th>
                  <th>{t("meters.table.amperage")}</th>
                  <th>{t("meters.table.area")}</th>
                  <th>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {meters.length > 0 ? (
                  meters.map((meter) => (
                    <tr
                      key={meter.meter_id}
                      onClick={() => handleOpenStatementModal(meter)}
                      style={{ cursor: "pointer" }}
                    >
                      <td>{meter.customer_full_name}</td>
                      <td>{meter.customer_phone_number}</td>
                      <td>{meter.address}</td>
                      <td>{meter.amperage}A</td>
                      <td>{meter.area_name}</td>
                      <td>
                        <Dropdown onClick={(e) => e.stopPropagation()}>
                          <Dropdown.Toggle
                            variant="outline-secondary"
                            size="sm"
                          >
                            <i className="bi bi-three-dots-vertical"></i>
                          </Dropdown.Toggle>
                          <Dropdown.Menu
                            renderOnMount
                            style={{ zIndex: "9000" }}
                            popperConfig={{
                              strategy: "fixed",
                              modifiers: [
                                {
                                  name: "preventOverflow",
                                  options: { boundary: "viewport" },
                                },
                                {
                                  name: "flip",
                                  options: {
                                    fallbackPlacements: ["right"],
                                  },
                                },
                                {
                                  name: "offset",
                                  options: { offset: [0, 6] },
                                },
                              ],
                            }}
                          >
                            <Dropdown.Item
                              onClick={() => handleOpenEditModal(meter)}
                            >
                              {t("meters.actions.edit")}
                            </Dropdown.Item>
                            <Dropdown.Item
                              onClick={() => setMeterToDelete(meter)}
                            >
                              {t("meters.actions.delete")}
                            </Dropdown.Item>
                            <Dropdown.Item
                              onClick={() => handleOpenStatementModal(meter)}
                            >
                              {t("meters.actions.viewStatement")}
                            </Dropdown.Item>
                            <Dropdown.Item onClick={() => setMeterForQr(meter)}>
                              {t("meters.actions.getQrCode")}
                            </Dropdown.Item>
                          </Dropdown.Menu>
                        </Dropdown>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="text-center">
                      {t("meters.noMetersFound")}
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

      <Suspense fallback={<div>{t("common.loading")}</div>}>
        {/* --- CHANGE 6: Render the single unified modal --- */}
        <MeterFormModal
          show={showMeterModal}
          meter={selectedMeter}
          handleClose={handleModalClose}
          areas={areas}
        />
        {meterForStatement && (
          <StatementModal
            show={!!meterForStatement}
            handleClose={() => setMeterForStatement(null)}
            meter={meterForStatement}
          />
        )}

        <MeterToolsModal
          show={showToolsModal}
          handleClose={() => setShowToolsModal(false)}
          onUploadSuccess={() => fetchMeters(1, filters)}
        />
        {meterForQr && (
          <QrCodeModal
            meterId={meterForQr.meter_id}
            show={!!meterForQr}
            handleClose={() => setMeterForQr(null)}
          />
        )}
      </Suspense>

      {meterToDelete && (
        <ConfirmationModal
          show={!!meterToDelete}
          title={t("meters.deleteModal.title")}
          body={
            <Trans
              i18nKey="meters.deleteModal.body"
              values={{ customerName: meterToDelete.customer_full_name }}
              components={{ strong: <strong /> }}
            />
          }
          onConfirm={handleDeleteMeter}
          onHide={() => setMeterToDelete(null)}
          isConfirming={isDeleting}
          confirmText={t("common.delete")}
        />
      )}
    </>
  );
};

export default MetersPage;
