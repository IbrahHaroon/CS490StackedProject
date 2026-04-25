import { NavLink, useNavigate } from "react-router-dom";
import "./Navbar.css";

export function MyAppNav() {
  const token = localStorage.getItem("token");
  const navigate = useNavigate();

  const handleSignOut = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  return (
    <nav>
      <NavLink to="/" end>
        Dashboard
      </NavLink>

      {token && (
        <>
          <NavLink to="/applications" end>
            Applications
          </NavLink>

          <NavLink to="/documents" end>
            Document Library
          </NavLink>

          <NavLink to="/profile" end>
            Profile
          </NavLink>

          <NavLink to="/settings" end>
            Settings
          </NavLink>
        </>
      )}

      {token ? (
        <button
          className="signout-nav-btn"
          style={{ marginLeft: "auto" }}
          onClick={handleSignOut}
        >
          Sign Out
        </button>
      ) : (
        <NavLink
          to="/signin"
          end
          className="signin-nav-btn"
          style={{ marginLeft: "auto" }}
        >
          Sign In
        </NavLink>
      )}
    </nav>
  );
}
