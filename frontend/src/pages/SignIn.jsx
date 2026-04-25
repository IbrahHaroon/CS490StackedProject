import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/apiClient";
import { logAction } from "../lib/actionLogger";
import "./SignIn.css";

const EMPTY_SIGNUP = {
  firstName: "",
  lastName: "",
  dob: "",
  address: "",
  state: "",
  zipCode: "",
};

function SignIn() {
  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signup, setSignup] = useState(EMPTY_SIGNUP);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleSignupField = (e) => {
    const { name, value } = e.target;
    setSignup((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    logAction("form_submit", { component: "SignIn", action: mode });

    if (mode === "signup") {
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

      // 3. Create profile (v2 shape — address fields inlined)
      localStorage.setItem("token", token);
      const profileRes = await api.post(
        "/profile/",
        {
          user_id: newUser.user_id,
          first_name: signup.firstName,
          last_name: signup.lastName,
          dob: signup.dob,
          address_line: signup.address,
          state: signup.state,
          zip_code: signup.zipCode,
        },
        { caller: "SignIn.createProfile", action: "create_profile" }
      );

      if (!profileRes.ok) {
        const err = await profileRes.json().catch(() => ({}));
        setError(err.detail || "Account created but profile setup failed.");
        return;
      }

      setSuccess("Account created! Signing you in…");
      navigate("/");
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
    navigate("/");
  };

  const switchMode = () => {
    setMode(mode === "signin" ? "signup" : "signin");
    setError("");
    setSuccess("");
  };

  return (
    <div className="signin-container">
      <div className="signin-card">
        <h2>{mode === "signin" ? "Sign In" : "Create Account"}</h2>
        {error && <p className="signin-error">{error}</p>}
        {success && <p className="signin-success">{success}</p>}
        <form onSubmit={handleSubmit} className="signin-form">
          {mode === "signup" && (
            <>
              <label>First Name</label>
              <input
                type="text"
                name="firstName"
                value={signup.firstName}
                onChange={handleSignupField}
                placeholder="Jane"
                required
              />
              <label>Last Name</label>
              <input
                type="text"
                name="lastName"
                value={signup.lastName}
                onChange={handleSignupField}
                placeholder="Doe"
                required
              />
              <label>Date of Birth</label>
              <input
                type="date"
                name="dob"
                value={signup.dob}
                onChange={handleSignupField}
                required
              />
              <label>Address</label>
              <input
                type="text"
                name="address"
                value={signup.address}
                onChange={handleSignupField}
                placeholder="123 Main St"
                required
              />
              <label>State</label>
              <input
                type="text"
                name="state"
                value={signup.state}
                onChange={handleSignupField}
                placeholder="NY"
                maxLength={2}
                required
              />
              <label>Zip Code</label>
              <input
                type="text"
                name="zipCode"
                value={signup.zipCode}
                onChange={handleSignupField}
                placeholder="10001"
                required
              />
            </>
          )}

          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
          <button type="submit" className="signin-btn">
            {mode === "signin" ? "Sign In" : "Sign Up"}
          </button>
        </form>
        <p className="signin-switch">
          {mode === "signin"
            ? "Don't have an account?"
            : "Already have an account?"}{" "}
          <button className="signin-switch-btn" onClick={switchMode}>
            {mode === "signin" ? "Sign Up" : "Sign In"}
          </button>
        </p>
      </div>
    </div>
  );
}

export default SignIn;
