// ReadingsPage.tsx

import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import { Button, Nav, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import type { Area } from "../areas/types";
import type { ReadingsSummary } from "./types";
import { getAreas } from "../areas/areasService";
import { getReadingsSummary } from "./readingsService";
import { useAlert } from "../../hooks/useAlert";
import { SummaryBar } from "./components/SummaryBar";
import { getDefaultMonth } from "../../utils/dateHelpers";
import { useLocation, useNavigate } from "react-router-dom";

// Lazy load all components
const AwaitingReadingsView = lazy(
  () => import("./components/AwaitingReadingsView")
);
const CollectedReadingsView = lazy(() =>
  import("./components/CollectedReadingsView").then((module) => ({
    default: module.CollectedReadingsView,
  }))
);
// NEW: Lazy load the modal here
const VerifyAllReadingsModal = lazy(
  () => import("./modals/VerifyAllReadingsModal")
);

type ActiveTab = "awaiting" | "collected";

const ReadingsPage = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<ActiveTab>("awaiting");
  const [summary, setSummary] = useState<ReadingsSummary | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(true);
  const [areas, setAreas] = useState<Area[]>([]);
  const [dateForSummary, setDateForSummary] = useState(getDefaultMonth());

  const location = useLocation();
  const navigate = useNavigate();

  // MOVED: Modal state is now managed by the parent page
  const [showVerifyAllModal, setShowVerifyAllModal] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const { handleError } = useAlert();

  const fetchSharedData = useCallback(
    async (month: string) => {
      setIsSummaryLoading(true);
      try {
        const [summaryData, areasData] = await Promise.all([
          getReadingsSummary(month),
          getAreas({ page: 1, limit: 20 }),
        ]);
        setSummary(summaryData);
        setAreas(areasData.items);
      } catch (err) {
        handleError(err);
      } finally {
        setIsSummaryLoading(false);
      }
    },
    [handleError]
  );

  useEffect(() => {
    fetchSharedData(dateForSummary);
  }, [dateForSummary, fetchSharedData]);

  const refreshSummary = () => fetchSharedData(dateForSummary);

  useEffect(() => {
    if (location.state?.refresh) {
      refreshSummary();
      // Optionally trigger the awaiting readings refetch as well
      setRefreshTrigger((prev) => prev + 1);

      // Clear the navigation state (so it doesn't refire on next render)
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state]);

  // NEW: Handler for closing the modal
  const handleVerifyAllModalClose = (needsRefresh: boolean) => {
    setShowVerifyAllModal(false);
    if (needsRefresh) {
      refreshSummary();
      // Trigger collected readings to refetch
      setRefreshTrigger((prev) => prev + 1);
    }
  };

  return (
    <>
      <h2 className="mb-3">{t("readings.title")}</h2>
      <SummaryBar summary={summary} isLoading={isSummaryLoading} />

      {/* NEW: Wrapper div for layout */}
      <div className="d-flex justify-content-between align-items-center">
        <Nav
          variant="tabs"
          activeKey={activeTab}
          onSelect={(k) => setActiveTab(k as ActiveTab)}
        >
          <Nav.Item>
            <Nav.Link eventKey="awaiting">
              {t("readings.uncollectedTab")}
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="collected">
              {t("readings.collectedTab")}
            </Nav.Link>
          </Nav.Item>
        </Nav>

        {/* MOVED & UPDATED: The button is now here */}
        {activeTab === "collected" && (
          <Button
            variant="success" // Changed variant for better visibility
            onClick={() => setShowVerifyAllModal(true)}
            className="align-end me-2" // Pushes the button to the end
          >
            {t("readings.collectedView.verifyAllButton")}
          </Button>
        )}
      </div>

      <Suspense
        fallback={
          <div className="p-5 text-center">
            <Spinner animation="border" />
          </div>
        }
      >
        {activeTab === "awaiting" && (
          <AwaitingReadingsView
            areas={areas}
            refreshSummary={refreshSummary}
            currentMonth={dateForSummary}
            onDateChange={setDateForSummary}
            refreshTrigger={refreshTrigger} // 👈 Add this line
          />
        )}
        {activeTab === "collected" && (
          <CollectedReadingsView
            areas={areas}
            currentMonth={dateForSummary}
            onDateChange={setDateForSummary}
            refreshTrigger={refreshTrigger} // Pass the trigger to child
          />
        )}
      </Suspense>

      {/* NEW: Render the modal conditionally */}
      {showVerifyAllModal && (
        <Suspense fallback={<Spinner animation="border" />}>
          <VerifyAllReadingsModal
            show={showVerifyAllModal}
            handleClose={handleVerifyAllModalClose}
            initialMonth={dateForSummary}
          />
        </Suspense>
      )}
    </>
  );
};

export default ReadingsPage;
