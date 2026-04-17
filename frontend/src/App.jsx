import { Routes, Route, useLocation } from "react-router-dom";
import { useEffect, useRef } from "react";
import { MyAppNav } from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Profile from "./pages/Profile.jsx";
import DocumentLibrary from "./pages/DocumentLibrary.jsx";
import Settings from "./pages/Settings.jsx";
import Applications from "./pages/Applications.jsx";
import Postings from "./pages/Postings.jsx";
import JobForm from "./pages/JobForm";
import SignIn from "./pages/SignIn";
import DevLogViewer from "./components/DevLogViewer.jsx";
import { api } from "./lib/apiClient";
import { logNavigation } from "./lib/actionLogger";
import "./App.css";

function App() {
  const location = useLocation();
  const prevPath = useRef(location.pathname);

  // Log route navigations
  useEffect(() => {
    if (prevPath.current !== location.pathname) {
      logNavigation(prevPath.current, location.pathname);
      prevPath.current = location.pathname;
    }
  }, [location.pathname]);

  useEffect(() => {
    if (localStorage.getItem("darkMode") === "false") {
      document.body.classList.add("light-mode");
    }
  }, []);

  // Validate stored token on startup — clear it if expired or invalid
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    api
      .get("/auth/me", {
        caller: "App.validateToken",
        action: "validate_token",
      })
      .then((res) => {
        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem("token");
          localStorage.removeItem("isRecruiter");
          window.location.reload();
        }
      })
      .catch(() => {
        // Network error — leave token alone so offline use still works
      });
  }, []);

  return (
    <>
      <MyAppNav />
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/signin" element={<SignIn />} />
          <Route
            path="/jobs/new"
            element={
              <ProtectedRoute>
                <JobForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobs/edit/:id"
            element={
              <ProtectedRoute>
                <JobForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <DocumentLibrary />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/applications"
            element={
              <ProtectedRoute>
                <Applications />
              </ProtectedRoute>
            }
          />
          <Route path="/postings" element={<Postings />} />
        </Routes>
      </main>
      {import.meta.env.VITE_SHOW_CONSOLE === "true" && <DevLogViewer />}
    </>
  );
}

export default App;
