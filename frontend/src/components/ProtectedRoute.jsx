import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

const API = "http://localhost:8000";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");
  const [valid, setValid] = useState(null); // null = checking, true = ok, false = invalid

  useEffect(() => {
    if (!token) {
      setValid(false);
      return;
    }
    fetch(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
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
