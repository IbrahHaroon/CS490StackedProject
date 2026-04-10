import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./SignIn.css";

const API = "http://localhost:8000";

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
  const [isRecruiter, setIsRecruiter] = useState(false);
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

    if (mode === "signup") {
      // 1. Register
      const regRes = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

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
      const loginRes = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
      const loginData = await loginRes.json();
      const token = loginData.access_token;

      // 3. Create profile
      const profileRes = await fetch(`${API}/profile/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: newUser.user_id,
          first_name: signup.firstName,
          last_name: signup.lastName,
          dob: signup.dob,
          address: {
            address: signup.address,
            state: signup.state,
            zip_code: parseInt(signup.zipCode, 10),
          },
        }),
      });

      if (!profileRes.ok) {
        const err = await profileRes.json().catch(() => ({}));
        setError(err.detail || "Account created but profile setup failed.");
        return;
      }

      setSuccess("Account created! Signing you in…");
      localStorage.setItem("token", token);
      navigate("/");
      return;
    }

    // Sign in
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const endpoint = isRecruiter
      ? `${API}/auth/recruiter/login`
      : `${API}/auth/login`;

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });

    if (!res.ok) {
      setError("Invalid email or password.");
      return;
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("isRecruiter", isRecruiter ? "true" : "false");
    navigate("/");
  };

  const switchMode = () => {
    setMode(mode === "signin" ? "signup" : "signin");
    setIsRecruiter(false);
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
                type="number"
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
          {mode === "signin" && (
            <label style={{ display: "flex", gap: "8px", alignItems: "center", fontSize: "14px", fontWeight: "normal" }}>
              <input
                type="checkbox"
                checked={isRecruiter}
                onChange={(e) => setIsRecruiter(e.target.checked)}
              />
              I am a recruiter
            </label>
          )}
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
