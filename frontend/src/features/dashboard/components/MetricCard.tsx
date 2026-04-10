import { Card, Col, Row, Placeholder } from "react-bootstrap";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: string; // e.g., 'bi-speedometer2'
  variant?: string; // Bootstrap color variant e.g., 'primary'
  isLoading: boolean;
}

export const MetricCard = ({
  title,
  value,
  icon,
  variant,
  isLoading,
}: MetricCardProps) => {
  if (isLoading) {
    return (
      <Card>
        <Card.Body>
          <Placeholder as="div" animation="glow">
            <Row>
              <Col xs={3}>
                <Placeholder xs={12} size="lg" bg="secondary" />
              </Col>
              <Col xs={9}>
                <Placeholder xs={8} />
                <Placeholder xs={5} size="lg" />
              </Col>
            </Row>
          </Placeholder>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card bg={variant} text={variant ? "white" : "dark"} className="h-100">
      <Card.Body>
        <Row className="align-items-center">
          <Col xs={3}>
            <i className={`bi ${icon} fs-1`}></i>
          </Col>
          <Col xs={9} className="text-end">
            <div className="fs-3 fw-bold">{value}</div>
            <div className="text-uppercase small">{title}</div>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
};
