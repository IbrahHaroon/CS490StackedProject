import { NavLink, useNavigate } from "react-router-dom";
import "./Navbar.css";

export function MyAppNav() {
  const token = localStorage.getItem("token");
  const isRecruiter = localStorage.getItem("isRecruiter") === "true";
  const navigate = useNavigate();

  const handleSignOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("isRecruiter");
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

          <NavLink to="/postings" end>
            Postings
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

          {isRecruiter && (
            <NavLink to="/jobs/new" end>
              Add Posting
            </NavLink>
          )}
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
