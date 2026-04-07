// src/pages/Messages/MessagesPage.tsx

import {
  useState,
  useEffect,
  useCallback,
  useMemo,
  lazy,
  Suspense,
} from "react";
import { Card, Button, Table, Row, Col, Form } from "react-bootstrap";
import { debounce } from "lodash";
import { useTranslation, Trans } from "react-i18next";
import { useNavigate } from "react-router-dom";

import type { Template, TemplateSearchPayload } from "./types";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";
import {
  getTemplates,
  deleteTemplate,
  getSessionStatus,
} from "./messagesService";

// Lazy load the modal for better performance
const TemplateModal = lazy(() =>
  import("./modals/TemplateModal").then((module) => ({
    default: module.TemplateModal,
  }))
);

const SendMessageModal = lazy(() =>
  import("./modals/SendMessageModal").then((module) => ({
    default: module.SendMessageModal,
  }))
);

const MessagesPage = () => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.dir() === "rtl";

  const [templates, setTemplates] = useState<Template[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<
    Omit<TemplateSearchPayload, "page" | "limit">
  >({});

  // Modal States
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateToEdit, setTemplateToEdit] = useState<Template | null>(null);
  const [templateToDelete, setTemplateToDelete] = useState<Template | null>(
    null
  );
  const [showSendMessageModal, setShowSendMessageModal] = useState(false);
  const { success, handleError } = useAlert();
  const [sessionStatus, setSessionStatus] = useState<
    "connected" | "disconnected" | null
  >(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  const fetchTemplates = useCallback(
    async (page: number, currentFilters: typeof filters) => {
      setIsLoading(true);
      try {
        const payload = { page, limit: 10, ...currentFilters };
        const response = await getTemplates(payload);
        setTemplates(response.items);
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
    fetchTemplates(currentPage, filters);
  }, [currentPage, filters, fetchTemplates]);

  const debouncedSearch = useMemo(
    () =>
      debounce((query: string) => {
        setCurrentPage(1); // Reset to first page on new search
        setFilters({ query });
      }, 500),
    []
  );

  // Fetch session status when page opens
  useEffect(() => {
    const fetchSessionStatus = async () => {
      setIsCheckingSession(true);
      const status = await getSessionStatus();
      setSessionStatus(status === "connected" ? "connected" : "disconnected");
      setIsCheckingSession(false);
    };
    fetchSessionStatus();
  }, []);

  // Handler for button click
  const handleManageWhatsApp = () => {
    navigate("/manage-phone-number");
  };

  const handleModalClose = (needsRefresh: boolean) => {
    setShowTemplateModal(false);
    setTemplateToEdit(null);
    if (needsRefresh) {
      fetchTemplates(1, {}); // Refresh from page 1
      setFilters({});
    }
  };

  const handleOpenEditModal = (template: Template) => {
    setTemplateToEdit(template);
    setShowTemplateModal(true);
  };

  const handleOpenCreateModal = () => {
    setTemplateToEdit(null); // Ensure we are in create mode
    setShowTemplateModal(true);
  };

  const handleOpenSendMessageModal = () => {
    setShowSendMessageModal(true);
  };

  const handleDeleteTemplate = async () => {
    if (!templateToDelete) return;
    setIsDeleting(true);
    try {
      await deleteTemplate(templateToDelete.template_id);
      success(t("messages.deleteSuccess", { name: templateToDelete.name }));
      setTemplateToDelete(null);
      fetchTemplates(currentPage, filters); // Refresh current page
    } catch (err) {
      handleError(err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className={`mb-2 text-${isRTL ? "start" : "end"}`}>
        <Button
          variant={
            isCheckingSession
              ? "secondary"
              : sessionStatus === "connected"
              ? "success"
              : "secondary"
          }
          disabled={isCheckingSession}
          onClick={handleManageWhatsApp}
        >
          {isCheckingSession
            ? t("messages.loadingSessionStatus")
            : sessionStatus === "connected"
            ? t("messages.whatsappConnected")
            : t("messages.connectWhatsapp")}
        </Button>
      </div>

      <Card>
        <Card.Header>
          <Row className="align-items-center">
            <Col md={5}>
              <Card.Title as="h5" className="mb-0">
                {t("messages.messageTemplates")}
              </Card.Title>
            </Col>
            <Col
              md={7}
              className="d-flex justify-content-end gap-2 g-3 flex-column flex-md-row"
            >
              <Button variant="success" onClick={handleOpenSendMessageModal}>
                <i className="bi bi-send mx-2"></i>
                {t("messages.sendMessage")}
              </Button>
              <Button variant="primary" onClick={handleOpenCreateModal}>
                <i className="bi bi-plus-lg mx-2"></i>
                {t("messages.createTemplate")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Row className="g-2 mb-3">
            <Col md={4}>
              <Form.Control
                placeholder={t("messages.searchByNamePlaceholder")}
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </Col>
          </Row>
          {isLoading ? (
            <SkeletonTable cols={3} />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("common.name")}</th>
                  <th>{t("messages.messagePreview")}</th>
                  <th style={{ width: "100px" }}>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {templates.length > 0 ? (
                  templates.map((template) => (
                    <tr key={template.template_id}>
                      <td>{template.name}</td>
                      <td
                        className="text-truncate"
                        style={{ maxWidth: "400px" }}
                      >
                        {template.message}
                      </td>
                      <td>
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          className="mx-2"
                          onClick={() => handleOpenEditModal(template)}
                        >
                          <i className="bi bi-pencil"></i>
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => setTemplateToDelete(template)}
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="text-center">
                      {t("messages.noTemplatesFound")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && templates.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>

      <Suspense fallback={<div>{t("common.loading")}</div>}>
        <TemplateModal
          show={showTemplateModal}
          template={templateToEdit}
          handleClose={handleModalClose}
        />
        <SendMessageModal
          show={showSendMessageModal}
          handleClose={() => setShowSendMessageModal(false)}
        />
      </Suspense>

      {templateToDelete && (
        <ConfirmationModal
          show={!!templateToDelete}
          title={t("messages.deleteTemplateTitle")}
          body={
            <Trans
              i18nKey="messages.deleteConfirmation"
              components={{ strong: <strong /> }}
            >
              Are you sure you want to delete the template{" "}
              <strong>"{templateToDelete.name}"</strong>? This action cannot be
              undone.
            </Trans>
          }
          onConfirm={handleDeleteTemplate}
          onHide={() => setTemplateToDelete(null)}
          isConfirming={isDeleting}
        />
      )}
    </>
  );
};

export default MessagesPage;
