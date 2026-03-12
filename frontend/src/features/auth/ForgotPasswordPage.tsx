// src/features/auth/ForgotPasswordPage.tsx
import { useNavigate } from "react-router-dom";
import ForgotPasswordModal from "./ForgotPasswordModal";

const ForgotPasswordPage = () => {
  const navigate = useNavigate();

  return (
    <ForgotPasswordModal
      show={true}
      handleClose={() => navigate("/login")} // when closed, go back to login
    />
  );
};

export default ForgotPasswordPage;
