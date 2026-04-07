// src/features/readings/components/CameraPage.tsx

import { useEffect } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { Button, Container, Alert, Spinner, Stack } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useCamera } from "../../../hooks/useCamera";
import {
  ArrowLeft,
  ArrowRight,
  Camera as CameraIcon,
} from "react-bootstrap-icons";

// Basic styling for the camera view (no changes needed here)
const cameraStyles: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundColor: "#000",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 1050, // Higher than default modal z-index
};

const videoStyles: React.CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
};

const controlsStyles: React.CSSProperties = {
  position: "absolute",
  bottom: 0,
  left: 0,
  width: "100%",
  padding: "1.5rem",
  background: "rgba(0, 0, 0, 0.4)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  gap: "2rem",
};

const CameraPage = () => {
  const { t, i18n } = useTranslation();
  const { meter_id } = useParams<{ meter_id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    videoRef,
    canvasRef,
    isStreaming,
    error,
    startCamera,
    stopCamera,
    capturePhoto,
  } = useCamera();

  // For better RTL support, we dynamically choose the correct arrow icon.
  const BackIcon = i18n.dir() === "rtl" ? ArrowRight : ArrowLeft;

  useEffect(() => {
    startCamera();
    // Ensure camera is stopped when the component unmounts
    return () => {
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  const handleCapture = async () => {
    try {
      const imageFile = await capturePhoto();
      if (imageFile && meter_id) {
        stopCamera();

        // Navigate back to the modal with the captured image
        navigate(`/readings/add-reading/${meter_id}`, {
          state: {
            backgroundLocation: location.state?.backgroundLocation,
            meter: location.state?.meter,
            capturedImage: imageFile,
            newReadingValue: location.state?.newReadingValue,
          },
          replace: true,
        });
      }
    } catch (err) {
      console.error("Failed to capture photo:", err);
      // Optional: Show an alert for capture failure
    }
  };

  const handleBack = () => {
    stopCamera();

    // Navigate back to the modal without a captured image
    navigate(`/readings/add-reading/${meter_id}`, {
      state: {
        backgroundLocation: location.state?.backgroundLocation,
        meter: location.state?.meter,
        newReadingValue: location.state?.newReadingValue,
      },
      replace: true,
    });
  };

  return (
    <div style={cameraStyles}>
      {error && (
        <Container className="text-center">
          {/* Assumes `error` from useCamera is a translation key, e.g., "readings.camera.errorPermissionDenied" */}
          <Alert variant="danger">{t(error, { ns: "camera" })}</Alert>
          <Button variant="secondary" onClick={handleBack}>
            <BackIcon className="me-2" /> {t("common.goBack")}
          </Button>
        </Container>
      )}

      {!isStreaming && !error && (
        <div className="text-center text-light">
          <Spinner animation="border" role="status" className="mb-2" />
          <p>{t("readings.camera.starting")}</p>
        </div>
      )}

      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{ ...videoStyles, display: isStreaming ? "block" : "none" }}
      />

      <canvas ref={canvasRef} style={{ display: "none" }} />

      {isStreaming && (
        <div style={controlsStyles}>
          <Stack
            direction="horizontal"
            gap={4}
            className="justify-content-center w-100"
          >
            <Button
              variant="light"
              onClick={handleBack}
              className="rounded-circle p-3"
              aria-label={t("common.goBack")}
            >
              <BackIcon size={24} />
            </Button>
            <Button
              variant="primary"
              onClick={handleCapture}
              className="rounded-circle p-4"
              aria-label={t("common.takePhoto")}
            >
              <CameraIcon size={30} />
            </Button>
            <div style={{ width: "64px" }}></div>{" "}
            {/* Placeholder for symmetry */}
          </Stack>
        </div>
      )}
    </div>
  );
};

export default CameraPage;
