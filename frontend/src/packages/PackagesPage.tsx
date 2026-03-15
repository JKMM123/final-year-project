import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import { useTranslation, Trans } from "react-i18next";
import {
  Card,
  Button,
  Table,
  Row,
  Col,
  Form,
  InputGroup,
  Alert,
} from "react-bootstrap";
import type { Package } from "./types";
import { getPackages, deletePackage } from "./packagesService";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";

const PackageModal = lazy(() => import("./modals/PackageModal"));
const RatesModal = lazy(() => import("./modals/RatesModal"));

const PackagesPage = () => {
  const { t } = useTranslation();
  const [packages, setPackages] = useState<Package[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [amperageSearch, setAmperageSearch] = useState("");

  const [showPackageModal, setShowPackageModal] = useState(false);
  const [selectedPkg, setSelectedPkg] = useState<Package | null>(null);
  const [showRatesModal, setShowRatesModal] = useState(false);
  const [pkgToDelete, setPkgToDelete] = useState<Package | null>(null);

  const { success, handleError } = useAlert();
  const [validationError, setValidationError] = useState<string | null>(null);

  const fetchPackages = useCallback(
    async (page: number, amperage: string) => {
      setIsLoading(true);
      setValidationError(null);
      try {
        const response = await getPackages({ page, limit: 10, amperage });
        setPackages(response.items);
        setPagination(response.pagination);
      } catch (err) {
        const message = handleError(err);
        setValidationError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [handleError]
  );

  useEffect(() => {
    fetchPackages(currentPage, amperageSearch);
  }, [currentPage, amperageSearch, fetchPackages]);

  const handlePackageModalClose = (needsRefresh: boolean) => {
    setShowPackageModal(false);
    setSelectedPkg(null); // Always clear the selected package on close
    if (needsRefresh) {
      fetchPackages(currentPage, amperageSearch);
    }
  };

  // --- UPDATED MODAL TRIGGERS ---
  const handleShowAddModal = () => {
    setSelectedPkg(null); // Ensure no package is selected for "Add" mode
    setShowPackageModal(true);
  };

  const handleShowEditModal = (pkg: Package) => {
    setSelectedPkg(pkg); // Set the package to edit
    setShowPackageModal(true);
  };

  const handleDeletePackage = async () => {
    if (!pkgToDelete) return;
    setIsDeleting(true);
    try {
      await deletePackage(pkgToDelete.package_id);
      success(
        t("packages.notifications.deleteSuccess", {
          amperage: pkgToDelete.amperage,
        })
      );
      setPkgToDelete(null);
      fetchPackages(currentPage, amperageSearch);
    } catch (err) {
      const message = handleError(err);
      setValidationError(message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Card>
        <Card.Header>
          <Row className="align-items-center">
            <Col md={5}>
              <Card.Title as="h5" className="mb-0">
                {t("packages.title")}
              </Card.Title>
            </Col>
            <Col md={7} className="d-flex justify-content-end gap-2 g-3">
              <Button variant="info" onClick={() => setShowRatesModal(true)}>
                {t("packages.viewRates")}
              </Button>
              <Button variant="primary" onClick={handleShowAddModal}>
                <i className="bi bi-plus-lg mx-2"></i>
                {t("packages.addPackage")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Row className="mb-3">
            <Col md={4}>
              <InputGroup>
                <Form.Control
                  type="number"
                  placeholder={t("packages.searchPlaceholder")}
                  value={amperageSearch}
                  onChange={(e) => setAmperageSearch(e.target.value)}
                />
                {amperageSearch && (
                  <Button
                    variant="outline-secondary"
                    onClick={() => setAmperageSearch("")}
                  >
                    {t("common.clear")}
                  </Button>
                )}
              </InputGroup>
            </Col>
          </Row>
          {validationError && <Alert variant="danger">{validationError}</Alert>}
          {isLoading ? (
            <SkeletonTable cols={5} />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("packages.table.amperage")}</th>
                  <th>{t("packages.table.activationFee")}</th>
                  <th>{t("packages.table.fixedFee")}</th>
                  <th>{t("packages.table.meters")}</th>
                  <th>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {packages.length > 0 ? (
                  packages.map((pkg) => (
                    <tr key={pkg.package_id}>
                      <td>{pkg.amperage} A</td>
                      <td>
                        {pkg.activation_fee.toLocaleString(undefined)} LBP
                      </td>
                      <td>{pkg.fixed_fee.toLocaleString(undefined)} LBP</td>
                      <td>{pkg.meters_count}</td>
                      <td>
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          className="mx-2"
                          onClick={() => handleShowEditModal(pkg)}
                        >
                          <i className="bi bi-pencil"></i>
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => setPkgToDelete(pkg)}
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="text-center">
                      {t("packages.noPackagesFound")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && packages.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>

      <Suspense fallback={<div>{t("common.loadingModal")}</div>}>
        {/* --- UNIFIED MODAL RENDERING --- */}
        {showPackageModal && (
          <PackageModal
            show={showPackageModal}
            pkg={selectedPkg}
            handleClose={handlePackageModalClose}
          />
        )}
        {showRatesModal && (
          <RatesModal
            show={showRatesModal}
            handleClose={() => setShowRatesModal(false)}
          />
        )}
      </Suspense>

      {pkgToDelete && (
        <ConfirmationModal
          show={!!pkgToDelete}
          title={t("packages.deleteModal.title")}
          body={
            <Trans
              i18nKey="packages.deleteModal.body"
              values={{ amperage: pkgToDelete.amperage }}
              components={{ strong: <strong /> }}
            />
          }
          onConfirm={handleDeletePackage}
          onHide={() => setPkgToDelete(null)}
          isConfirming={isDeleting}
          confirmText={t("packages.deleteModal.confirmText")}
        />
      )}
    </>
  );
};
export default PackagesPage;
