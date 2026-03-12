// src/features/users/pages/UsersPage.tsx

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
  InputGroup,
  Alert,
} from "react-bootstrap";
import { debounce } from "lodash";
import { useTranslation, Trans } from "react-i18next";
import Select from "react-select";

import type { User } from "./types";
import { getUsers, deleteUser } from "./usersService";
import { useAlert } from "../../hooks/useAlert";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";
import { SkeletonTable } from "../../components/common/SkeletonTable";
import { Pagination } from "../../components/common/Pagination";
import { ConfirmationModal } from "../../components/common/ConfirmationModal";

// --- CHANGE 1: Import the single UserModal ---

const UserModal = lazy(() => import("./modals/UserModal")); // ADDED

const UsersPage = () => {
  const { t } = useTranslation();

  const roleFilterOptions = useMemo(
    () => [
      { value: "", label: t("usersPage.roles.all") },
      { value: "user", label: t("usersPage.roles.user") },
      { value: "admin", label: t("usersPage.roles.admin") },
    ],
    [t]
  );

  const [users, setUsers] = useState<User[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [userToDelete, setUserToDelete] = useState<User | null>(null);

  // --- CHANGE 2: Consolidate modal state ---
  const [showUserModal, setShowUserModal] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null); // null for 'Add', User object for 'Edit'

  const { success, handleError } = useAlert();
  const [validationError, setValidationError] = useState<string | null>(null);

  const fetchUsers = useCallback(
    async (page: number, query: string, role: string) => {
      setIsLoading(true);
      try {
        const response = await getUsers({ page, limit: 10, query, role });
        setUsers(response.items);
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
      debounce((query: string, role: string) => {
        setCurrentPage(1);
        fetchUsers(1, query, role);
      }, 500),
    [fetchUsers]
  );

  useEffect(() => {
    fetchUsers(currentPage, searchQuery, roleFilter);
  }, [currentPage, roleFilter, fetchUsers]);

  // --- CHANGE 3: Update handler to open 'Add' modal ---
  const handleShowAddModal = () => {
    setCurrentUser(null); // Set to null for Add mode
    setShowUserModal(true);
  };

  // --- CHANGE 4: Update handler to open 'Edit' modal ---
  const handleShowEditModal = (user: User) => {
    setCurrentUser(user); // Set to the specific user for Edit mode
    setShowUserModal(true);
  };

  const handleModalClose = (needsRefresh: boolean) => {
    setShowUserModal(false);
    setCurrentUser(null); // Also clear the user state on close
    if (needsRefresh) {
      fetchUsers(currentPage, searchQuery, roleFilter);
    }
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    setIsDeleting(true);
    try {
      await deleteUser(userToDelete.user_id);
      success(
        t("usersPage.alerts.deleteSuccess", { username: userToDelete.username })
      );
      setUserToDelete(null);
      fetchUsers(currentPage, searchQuery, roleFilter);
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
                {t("usersPage.title")}
              </Card.Title>
            </Col>
            <Col md={7} className="d-flex justify-content-end">
              <Button variant="primary" onClick={handleShowAddModal}>
                {" "}
                {/* UPDATED */}
                <i className="bi bi-plus-lg mx-2"></i>
                {t("usersPage.addUserButton")}
              </Button>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          {/* ... Search and Filter UI (no changes here) ... */}
          <Row className="g-2 mb-3">
            <Col md={6}>
              <InputGroup>
                <Form.Control
                  placeholder={t("usersPage.searchPlaceholder")}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    debouncedFetch(e.target.value, roleFilter);
                  }}
                />
              </InputGroup>
            </Col>
            <Col md={6}>
              <Select
                aria-label={t("usersPage.roleFilterPlaceholder")}
                options={roleFilterOptions}
                placeholder={t("usersPage.roleFilterPlaceholder")}
                isSearchable={false}
                value={
                  roleFilterOptions.find(
                    (option) => option.value === roleFilter
                  ) || null
                }
                onChange={(option) => setRoleFilter(option ? option.value : "")}
              />
            </Col>
          </Row>

          {validationError && <Alert variant="danger">{validationError}</Alert>}
          {isLoading ? (
            <SkeletonTable cols={4} />
          ) : (
            <Table responsive striped bordered hover>
              <thead>
                <tr>
                  <th>{t("usersPage.table.headerUsername")}</th>
                  <th>{t("usersPage.table.headerPhone")}</th>
                  <th>{t("usersPage.table.headerRole")}</th>
                  <th>{t("usersPage.table.headerActions")}</th>
                </tr>
              </thead>
              <tbody>
                {users.length > 0 ? (
                  users.map((user) => (
                    <tr key={user.user_id}>
                      <td>{user.username}</td>
                      <td>{user.phone_number}</td>
                      <td>
                        <span
                          className={`badge bg-${
                            user.role === "admin" ? "primary" : "secondary"
                          }`}
                        >
                          {t(`usersPage.roles.${user.role}`)}
                        </span>
                      </td>
                      <td>
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          className="mx-2"
                          onClick={() => handleShowEditModal(user)}
                        >
                          <i className="bi bi-pencil"></i>
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => setUserToDelete(user)}
                        >
                          <i className="bi bi-trash"></i>
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="text-center">
                      {t("usersPage.table.noUsersFound")}
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
        {pagination && users.length > 0 && (
          <Card.Footer className="d-flex justify-content-end">
            <Pagination pagination={pagination} onPageChange={setCurrentPage} />
          </Card.Footer>
        )}
      </Card>

      {/* --- CHANGE 5: Render the single UserModal --- */}
      <Suspense fallback={<div>{t("common.loading")}</div>}>
        {showUserModal && (
          <UserModal
            user={currentUser}
            show={showUserModal}
            handleClose={handleModalClose}
          />
        )}
      </Suspense>

      {userToDelete && (
        <ConfirmationModal
          show={!!userToDelete}
          title={t("usersPage.modals.deleteTitle")}
          body={
            <Trans
              i18nKey="usersPage.modals.deleteBody"
              values={{ username: userToDelete.username }}
              components={{ 1: <strong /> }}
            />
          }
          onConfirm={handleDeleteUser}
          onHide={() => setUserToDelete(null)}
          isConfirming={isDeleting}
          confirmText={t("common.delete")}
        />
      )}
    </>
  );
};

export default UsersPage;
