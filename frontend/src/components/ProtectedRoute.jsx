import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../lib/apiClient";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");
  const [valid, setValid] = useState(null); // null = checking, true = ok, false = invalid

  useEffect(() => {
    if (!token) {
      setValid(false);
      return;
    }
    api
      .get("/auth/me", { caller: "ProtectedRoute.validate", action: "validate_token" })
      .then((res) => {
        if (res.ok) {
          setValid(true);
        } else {
          localStorage.removeItem("token");
          localStorage.removeItem("isRecruiter");
          setValid(false);
        }
      })
      .catch(() => {
        setValid(false);
      });
  }, [token]);

  if (valid === null) return null; // still checking — render nothing briefly
  if (!valid) return <Navigate to="/signin" replace />;
  return children;
}

export default ProtectedRoute;
