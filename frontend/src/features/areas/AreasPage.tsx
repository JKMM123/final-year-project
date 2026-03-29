import { useState, useEffect, useCallback, useMemo } from "react";
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
import { debounce } from "lodash";
import type { Area, AreaPayload } from "./types";
import { getAreas, updateArea, deleteArea } from "./areasService";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";
import { CreateAreaForm } from "./CreateAreaForm";
import { EditableAreaRow } from "./EditableAreaRow";

const AreasPage = () => {
  const { t } = useTranslation();
  const [areas, setAreas] = useState<Area[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [editingAreaId, setEditingAreaId] = useState<string | null>(null);
  const [areaToDelete, setAreaToDelete] = useState<Area | null>(null);

  const { success, handleError } = useAlert();
  const [validationError, setValidationError] = useState<string | null>(null);

  const fetchAreas = useCallback(
    async (page: number, query: string) => {
      setIsLoading(true);
      setEditingAreaId(null);
      try {
        const response = await getAreas({ page, limit: 10, query });
        setAreas(response.items);
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

  const debouncedFetch = useMemo(
    () =>
      debounce((query: string) => {
        setCurrentPage(1);
        fetchAreas(1, query);
      }, 500),
    [fetchAreas]
  );

  useEffect(() => {
    fetchAreas(currentPage, searchQuery);
  }, [currentPage, fetchAreas]);

  const handleSaveEdit = async (payload: AreaPayload) => {
    if (!editingAreaId) return;
    try {
      await updateArea(editingAreaId, payload);
      success(t("areas.notifications.updateSuccess"));
      fetchAreas(currentPage, searchQuery);
    } catch (err) {
      const message = handleError(err);
      setValidationError(message);
    }
  };

  const handleDeleteArea = async () => {
    if (!areaToDelete) return;
    setIsDeleting(true);
    try {
      await deleteArea(areaToDelete.area_id);
      success(
        t("areas.notifications.deleteSuccess", {
          areaName: areaToDelete.area_name,
        })
      );
      setAreaToDelete(null);
      fetchAreas(currentPage, searchQuery);
    } catch (err) {
      const message = handleError(err);
      setValidationError(message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreate(false);
    fetchAreas(1, "");
  };

  return (
    <>
      <Card>
        <Card.Header>
          <Row className="align-items-center">
            <Col md={5}>
              <Card.Title as="h5" className="mb-0">
                {t("areas.title")}
              </Card.Title>
            </Col>
            <Col md={7} className="d-flex justify-content-end">
              <Button
                variant="primary"
                onClick={() => setShowCreate(true)}
                disabled={showCreate}
              >
                <i className="bi bi-plus-lg mx-2"></i>
                {t("areas.addArea")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          {showCreate && (
            <CreateAreaForm
              onSuccess={handleCreateSuccess}
              onCancel={() => setShowCreate(false)}
            />
          )}

          <Row className="mb-3">
            <Col md={5}>
              <InputGroup>
                <Form.Control
                  placeholder={t("areas.searchPlaceholder")}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    debouncedFetch(e.target.value);
                  }}
                />
              </InputGroup>
            </Col>
          </Row>
          {validationError && <Alert variant="danger">{validationError}</Alert>}

          {isLoading ? (
            <SkeletonTable cols={4} />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("areas.table.name")}</th>
                  <th>{t("areas.table.elevation")}</th>
                  <th>{t("areas.table.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {areas.length > 0 ? (
                  areas.map((area) =>
                    editingAreaId === area.area_id ? (
                      <EditableAreaRow
                        key={area.area_id}
                        area={area}
                        onSave={handleSaveEdit}
                        onCancel={() => setEditingAreaId(null)}
                      />
                    ) : (
                      <tr key={area.area_id}>
                        <td>{area.area_name}</td>
                        <td>{area.elevation.toLocaleString(undefined)}m</td>
                        <td>
                          <Button
                            variant="outline-secondary"
                            size="sm"
                            className="mx-2"
                            onClick={() => setEditingAreaId(area.area_id)}
                          >
                            <i className="bi bi-pencil"></i>
                          </Button>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => setAreaToDelete(area)}
                          >
                            <i className="bi bi-trash"></i>
                          </Button>
                        </td>
                      </tr>
                    )
                  )
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center">
                      {t("areas.noAreasFound")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && areas.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>

      {areaToDelete && (
        <ConfirmationModal
          show={!!areaToDelete}
          title={t("areas.deleteModal.title")}
          body={
            <Trans
              i18nKey="areas.deleteModal.body"
              values={{ areaName: areaToDelete.area_name }}
              components={{ strong: <strong /> }}
            >
              Are you sure you want to delete <strong>{"{areaName}"}</strong>?
              This action cannot be undone.
            </Trans>
          }
          onConfirm={handleDeleteArea}
          onHide={() => setAreaToDelete(null)}
          isConfirming={isDeleting}
          confirmText={t("areas.deleteModal.confirmText")}
        />
      )}
    </>
  );
};

export default AreasPage;
