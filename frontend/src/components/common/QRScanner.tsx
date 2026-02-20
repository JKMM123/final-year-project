// Placeholder for a QR Scanner component.
// In a real implementation, you would use a library like 'react-qr-reader'.

import { useState } from "react";
import { Button, Card, Form } from "react-bootstrap";

interface QRScannerProps {
  onScan: (data: string) => void;
}

const QRScanner = ({ onScan }: QRScannerProps) => {
  const [manualInput, setManualInput] = useState("");

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (manualInput) {
      onScan(manualInput);
    }
  };

  return (
    <Card>
      <Card.Body>
        <Card.Title>Scan Meter QR Code</Card.Title>
        <Card.Text>
          QR scanning is not implemented in this mock. Please enter the meter ID
          manually.
        </Card.Text>
        <Form onSubmit={handleManualSubmit}>
          <Form.Group className="mb-3">
            <Form.Control
              type="text"
              placeholder="Enter Meter ID"
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
            />
          </Form.Group>
          <Button type="submit">Submit ID</Button>
        </Form>
      </Card.Body>
    </Card>
  );
};

export default QRScanner;
