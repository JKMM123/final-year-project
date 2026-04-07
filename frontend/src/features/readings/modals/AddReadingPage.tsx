import { useParams, useLocation, useNavigate } from "react-router-dom";
import AddReadingModal from "./AddReadingModal";

export default function AddReadingPage() {
  const { meter_id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as {
    capturedImage?: File;
    meterIdForState?: string;
    meter?: any;
  };

  if (!meter_id) return null;

  return (
    <AddReadingModal
      show={true}
      meter={state?.meter || ({ meter_id } as any)}
      handleClose={(needsRefresh) => {
        navigate("/readings", {
          replace: true,
          state: { refresh: needsRefresh }, // 👈 send a flag back
        });
      }}
      preloadedImage={state?.capturedImage || null}
    />
  );
}
