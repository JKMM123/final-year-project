import { Card, Col, Row, Placeholder } from "react-bootstrap";
import { useTranslation } from "react-i18next"; // Import useTranslation
import type { ReadingsSummary } from "../types";

interface SummaryBarProps {
  summary: ReadingsSummary | null;
  isLoading: boolean;
}

const SummaryCard = ({
  title,
  value,
  variant,
}: {
  title: string;
  value: number;
  variant?: string;
}) => (
  <Col>
    <Card
      bg={variant}
      text={variant ? "white" : "dark"}
      className="text-center"
    >
      <Card.Body>
        {/* Numbers are kept as is (will render in English numerals) */}
        <h4 className="mb-1">{value.toLocaleString()}</h4>
        <small>{title}</small>
      </Card.Body>
    </Card>
  </Col>
);

const SummaryPlaceholder = () => (
  <Col>
    <Placeholder as={Card.Body} animation="glow">
      <Placeholder xs={12} style={{ height: "60px" }} />
    </Placeholder>
  </Col>
);

export const SummaryBar = ({ summary, isLoading }: SummaryBarProps) => {
  const { t } = useTranslation(); // Initialize the translation function

  return (
    <Card className="mb-4">
      <Card.Body>
        <Row xs={1} md={3} lg={5} className="g-3">
          {isLoading || !summary ? (
            Array.from({ length: 5 }).map((_, i) => (
              <SummaryPlaceholder key={i} />
            ))
          ) : (
            <>
              <SummaryCard
                title={t("readings.summary.totalActiveMeters")}
                value={summary.total_active_meters}
              />
              <SummaryCard
                title={t("readings.summary.metersWithReadings")}
                value={summary.meters_with_readings}
                variant="success"
              />
              <SummaryCard
                title={t("readings.summary.metersNeedingReadings")}
                value={summary.meters_needing_readings}
                variant="warning"
              />
              <SummaryCard
                title={t("readings.summary.pendingReadings")}
                value={summary.pending_readings_count}
                variant="info"
              />
              <SummaryCard
                title={t("readings.summary.verifiedReadings")}
                value={summary.verified_readings_count}
                variant="primary"
              />
            </>
          )}
        </Row>
      </Card.Body>
    </Card>
  );
};
