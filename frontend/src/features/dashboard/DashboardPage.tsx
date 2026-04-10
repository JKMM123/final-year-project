import { useState, useEffect, useCallback } from "react";
import { Card, Col, Form, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next"; // 1. IMPORT THE HOOK
import { useAlert } from "../../hooks/useAlert";
import type { DashboardSummary } from "./types";
import { getDashboardSummary } from "./dashboardService";
import { MetricCard } from "./components/MetricCard";
import { getDefaultMonth } from "../../utils/dateHelpers";

const DashboardPage = () => {
  const { t } = useTranslation(); // 2. INITIALIZE THE TRANSLATION FUNCTION
  const [summaryData, setSummaryData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialDelay, setIsInitialDelay] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(getDefaultMonth());
  const { handleError } = useAlert();

  const fetchDashboardData = useCallback(
    async (month: string) => {
      setIsLoading(true);
      try {
        const data = await getDashboardSummary(month);
        setSummaryData(data);
      } catch (err) {
        handleError(err);
        setSummaryData(null);
      } finally {
        setIsLoading(false);
      }
    },
    [handleError]
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialDelay(false);
      fetchDashboardData(selectedMonth);
    }, 1000);
    return () => clearTimeout(timer);
  }, [selectedMonth, fetchDashboardData]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // 3. UPDATED: Explicitly use 'en-US' locale to keep numbers in English format
  const formatLbp = (value: number) =>
    `${value.toLocaleString("en-US", {
      // <-- Force English numerals
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })} LBP`;
  const formatUsd = (value: number) =>
    `$${value.toLocaleString("en-US", {
      // <-- Force English numerals
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;

  if (isInitialDelay) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          height: "60vh",
        }}
      >
        <Spinner
          animation="border"
          role="status"
          variant="primary"
          style={{ width: "3rem", height: "3rem" }}
        />
        {/* UPDATED */}
        <span className="mt-3 text-muted">
          {t("dashboardPage.loadingText")}
        </span>
      </div>
    );
  }

  return (
    <Card>
      <Card.Header className="d-flex flex-column flex-sm-row justify-content-between align-items-sm-center">
        {/* UPDATED */}
        <h5 className="mb-2 mb-sm-0">{t("dashboardPage.summaryTitle")}</h5>
        <Form.Control
          type="month"
          value={selectedMonth}
          onChange={(e) => {
            const value = e.target.value;
            setSelectedMonth(value === "" ? getDefaultMonth() : value);
          }}
          style={{ width: "auto", minWidth: "140px" }}
        />
      </Card.Header>
      <Card.Body>
        {/* UPDATED */}
        <h5 className="mb-3">{t("dashboardPage.metersTitle")}</h5>
        <Row xs={1} md={2} lg={3} xl={4} className="g-4">
          <Col>
            <MetricCard
              title={t("dashboardPage.meters.totalActive")}
              value={summaryData?.meters.active.total ?? 0}
              icon="bi-speedometer2"
              isLoading={isLoading}
              variant="primary"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.meters.activeFixed")}
              value={summaryData?.meters.active.fixed ?? 0}
              icon="bi-plug"
              isLoading={isLoading}
              variant="primary"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.meters.activeUsage")}
              value={summaryData?.meters.active.usage ?? 0}
              icon="bi-lightning-charge"
              isLoading={isLoading}
              variant="primary"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.meters.totalInactive")}
              value={summaryData?.meters.inactive.total ?? 0}
              icon="bi-power"
              isLoading={isLoading}
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.meters.withoutReadings")}
              value={summaryData?.meters_without_readings ?? 0}
              icon="bi-journal-x"
              isLoading={isLoading}
              variant="warning"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.meters.total")}
              value={summaryData?.meters.total.total ?? 0}
              icon="bi-reception-4"
              isLoading={isLoading}
            />
          </Col>
        </Row>

        <hr className="my-4" />

        {/* UPDATED */}
        <h5 className="mb-3">{t("dashboardPage.readingsTitle")}</h5>
        <Row xs={1} md={2} lg={3} xl={4} className="g-4">
          <Col>
            <MetricCard
              title={t("dashboardPage.readings.verified")}
              value={summaryData?.readings.verified ?? 0}
              icon="bi-check-circle-fill"
              isLoading={isLoading}
              variant="success"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.readings.pending")}
              value={summaryData?.readings.pending ?? 0}
              icon="bi-hourglass-split"
              isLoading={isLoading}
            />
          </Col>
        </Row>

        <hr className="my-4" />

        {/* UPDATED */}
        <h5 className="mb-3">{t("dashboardPage.billsTitle")}</h5>
        <Row xs={1} md={2} lg={3} xl={4} className="g-4">
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.generated")}
              value={summaryData?.bills.generated ?? 0}
              icon="bi-receipt-cutoff"
              isLoading={isLoading}
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.paidTotal")}
              value={summaryData?.bills_payment_status.paid.total ?? 0}
              icon="bi-cash-coin"
              isLoading={isLoading}
              variant="info"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.paidCash")}
              value={summaryData?.bills_payment_status.paid.cash ?? 0}
              icon="bi-cash-stack"
              isLoading={isLoading}
              variant="info"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.paidWhish")}
              value={summaryData?.bills_payment_status.paid.whish ?? 0}
              icon="bi-wallet2"
              isLoading={isLoading}
              variant="info"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.paidOmt")}
              value={summaryData?.bills_payment_status.paid.omt ?? 0}
              icon="bi-phone-fill"
              isLoading={isLoading}
              variant="info"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.unpaid")}
              value={summaryData?.bills_payment_status.unpaid ?? 0}
              icon="bi-exclamation-diamond-fill"
              isLoading={isLoading}
              variant="danger"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.bills.partiallyPaid")}
              value={summaryData?.bills_payment_status.partially_paid ?? 0}
              icon="bi-pie-chart-fill"
              isLoading={isLoading}
              variant="warning"
            />
          </Col>
        </Row>

        <hr className="my-4" />

        {/* UPDATED */}
        <h5 className="mb-3">{t("dashboardPage.earnings.title")}</h5>
        <Row className="g-4">
          <Col xs={12}>
            <Card className="bg-light">
              <Card.Body>
                {/* UPDATED */}
                <h5 className="mb-3 text-center">
                  {t("dashboardPage.earnings.totalEarnings")}
                </h5>
                <Row>
                  <Col md={6} className="text-center border-end-md">
                    <MetricCard
                      title={t("dashboardPage.earnings.totalUsd")}
                      value={formatUsd(
                        summaryData?.earnings.total.total_earnings_usd ?? 0
                      )}
                      icon="bi-currency-dollar"
                      isLoading={isLoading}
                    />
                  </Col>
                  <Col md={6} className="text-center mt-3 mt-md-0">
                    <MetricCard
                      title={t("dashboardPage.earnings.totalLbp")}
                      value={formatLbp(
                        summaryData?.earnings.total.total_earnings_lbp ?? 0
                      )}
                      icon="bi-bank"
                      isLoading={isLoading}
                    />
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
          <Col xs={12}>
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  {t("dashboardPage.earnings.breakdownTitle")}
                </h6>
              </Card.Header>
              <Card.Body>
                <Row className="g-4">
                  <Col md={4}>
                    <Card className="h-100">
                      <Card.Header className="text-center text-muted">
                        <h6 className="mb-0">
                          {t("dashboardPage.earnings.cash")}
                        </h6>
                      </Card.Header>
                      <Card.Body className="d-flex flex-column justify-content-center gap-3 p-2">
                        <MetricCard
                          title={t("dashboardPage.earnings.earningsUsd")}
                          value={formatUsd(
                            summaryData?.earnings.cash?.total_earnings_usd ?? 0
                          )}
                          icon="bi-currency-dollar"
                          isLoading={isLoading}
                        />
                        <MetricCard
                          title={t("dashboardPage.earnings.earningsLbp")}
                          value={formatLbp(
                            summaryData?.earnings.cash?.total_earnings_lbp ?? 0
                          )}
                          icon="bi-bank"
                          isLoading={isLoading}
                        />
                      </Card.Body>
                    </Card>
                  </Col>
                  <Col md={4}>
                    <Card className="h-100">
                      <Card.Header className="text-center text-muted">
                        <h6 className="mb-0">
                          {t("dashboardPage.earnings.whish")}
                        </h6>
                      </Card.Header>
                      <Card.Body className="d-flex flex-column justify-content-center gap-3 p-2">
                        <MetricCard
                          title={t("dashboardPage.earnings.earningsUsd")}
                          value={formatUsd(
                            summaryData?.earnings.whish?.total_earnings_usd ?? 0
                          )}
                          icon="bi-currency-dollar"
                          isLoading={isLoading}
                        />
                        <MetricCard
                          title={t("dashboardPage.earnings.earningsLbp")}
                          value={formatLbp(
                            summaryData?.earnings.whish?.total_earnings_lbp ?? 0
                          )}
                          icon="bi-bank"
                          isLoading={isLoading}
                        />
                      </Card.Body>
                    </Card>
                  </Col>
                  <Col md={4}>
                    <Card className="h-100">
                      <Card.Header className="text-center text-muted">
                        <h6 className="mb-0">
                          {t("dashboardPage.earnings.omt")}
                        </h6>
                      </Card.Header>
                      <Card.Body className="d-flex flex-column justify-content-center gap-3 p-2">
                        <MetricCard
                          title={t("dashboardPage.earnings.earningsUsd")}
                          value={formatUsd(
                            summaryData?.earnings.omt?.total_earnings_usd ?? 0
                          )}
                          icon="bi-currency-dollar"
                          isLoading={isLoading}
                        />
                        <MetricCard
                          title={t("dashboardPage.earnings.earningsLbp")}
                          value={formatLbp(
                            summaryData?.earnings.omt?.total_earnings_lbp ?? 0
                          )}
                          icon="bi-bank"
                          isLoading={isLoading}
                        />
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <hr className="my-4" />

        {/* UPDATED */}
        <h5 className="mb-3">{t("dashboardPage.unpaidTitle")}</h5>
        <Row xs={1} md={2} lg={4} className="g-4">
          <Col>
            <MetricCard
              title={t("dashboardPage.unpaid.totalUsd")}
              value={formatUsd(
                summaryData?.unpaid_arrears?.total_unpaid_usd ?? 0
              )}
              icon="bi-graph-down-arrow"
              isLoading={isLoading}
              variant="danger"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.unpaid.totalLbp")}
              value={formatLbp(
                summaryData?.unpaid_arrears?.total_unpaid_lbp ?? 0
              )}
              icon="bi-graph-down-arrow"
              isLoading={isLoading}
              variant="danger"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.unpaid.thisMonthUsd")}
              value={formatUsd(
                summaryData?.unpaid_arrears?.total_unpaid_this_month_usd ?? 0
              )}
              icon="bi-calendar-x"
              isLoading={isLoading}
              variant="danger"
            />
          </Col>
          <Col>
            <MetricCard
              title={t("dashboardPage.unpaid.thisMonthLbp")}
              value={formatLbp(
                summaryData?.unpaid_arrears?.total_unpaid_this_month_lbp ?? 0
              )}
              icon="bi-calendar-x"
              isLoading={isLoading}
              variant="danger"
            />
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};

export default DashboardPage;
