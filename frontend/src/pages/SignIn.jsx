import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./SignIn.css";

function SignIn() {
  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const rememberedEmail = localStorage.getItem("rememberedEmail");
    if (rememberedEmail) {
      setEmail(rememberedEmail);
      setRememberMe(true);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    logAction("form_submit", { component: "SignIn", action: mode });

    if (mode === "signup") {
      if (!firstName.trim() || !lastName.trim()) {
        setError("First and last name are required.");
        return;
      }

      // 1. Register
      const regRes = await api.post(
        "/auth/register",
        { email, password },
        { caller: "SignIn.register", action: "user_register" }
      );

      if (!regRes.ok) {
        const err = await regRes.json().catch(() => ({}));
        setError(err.detail || "Registration failed.");
        return;
      }

      const newUser = await regRes.json();

      // 2. Login to get token
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const loginRes = await api.post("/auth/login", form, {
        caller: "SignIn.loginAfterRegister",
        action: "user_login",
      });
      const loginData = await loginRes.json();
      const token = loginData.access_token;

      // 3. Save token and remember me preference
      localStorage.setItem("token", token);
      if (rememberMe) {
        localStorage.setItem("rememberMe", "true");
        localStorage.setItem("rememberedEmail", email);
      }

      setSuccess("Account created! Signing you in…");
      setTimeout(() => navigate("/"), 1000);
      return;
    }

    // Sign in
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const res = await api.post("/auth/login", form, {
      caller: "SignIn.login",
      action: "user_login",
    });

    if (!res.ok) {
      setError("Invalid email or password.");
      return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);

    if (rememberMe) {
      localStorage.setItem("rememberMe", "true");
      localStorage.setItem("rememberedEmail", email);
    } else {
      localStorage.removeItem("rememberMe");
      localStorage.removeItem("rememberedEmail");
    }

    navigate("/");
  };

  const handleGoogleSignIn = () => {
    setError("Google Sign-In coming soon!");
    logAction("oauth_attempt", { provider: "google" });
  };

  const handleGitHubSignIn = () => {
    setError("GitHub Sign-In coming soon!");
    logAction("oauth_attempt", { provider: "github" });
  };

  return (
    <div className="signin-container">
      <div className="signin-content">
        <h1 className="signin-title">Job Tracker</h1>
        <p className="signin-subtitle">
          Sign in to track jobs, generate resumes, and manage your pipeline
        </p>

        <div className="signin-card">
          {/* Tabs */}
          <div className="signin-tabs">
            <button
              className={`signin-tab ${mode === "signin" ? "active" : ""}`}
              onClick={() => setMode("signin")}
            >
              Sign In
            </button>
            <button
              className={`signin-tab ${mode === "signup" ? "active" : ""}`}
              onClick={() => setMode("signup")}
            >
              Sign Up
            </button>
          </div>

          {error && <p className="signin-error">{error}</p>}
          {success && <p className="signin-success">{success}</p>}

          <form onSubmit={handleSubmit} className="signin-form">
            {mode === "signup" && (
              <>
                <div className="signin-form-group">
                  <label htmlFor="firstName">First Name</label>
                  <input
                    id="firstName"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="Jane"
                    required
                  />
                </div>
                <div className="signin-form-group">
                  <label htmlFor="lastName">Last Name</label>
                  <input
                    id="lastName"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Doe"
                    required
                  />
                </div>
              </>
            )}

            <div className="signin-form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>

            <div className="signin-form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>

            {mode === "signin" && (
              <div className="signin-remember-forgot">
                <label htmlFor="rememberMe" className="signin-checkbox-label">
                  <input
                    id="rememberMe"
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  Remember me
                </label>
              </div>
            )}

            <button type="submit" className="signin-btn">
              {mode === "signin" ? "Sign In" : "Sign Up"}
            </button>
          </form>

          {/* OAuth */}
          <div className="signin-oauth">
            <p className="signin-oauth-text">Or continue with</p>
            <div className="signin-oauth-buttons">
              <button
                type="button"
                className="signin-oauth-btn signin-google"
                onClick={handleGoogleSignIn}
              >
                Google
              </button>
              <button
                type="button"
                className="signin-oauth-btn signin-github"
                onClick={handleGitHubSignIn}
              >
                GitHub
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignIn;
