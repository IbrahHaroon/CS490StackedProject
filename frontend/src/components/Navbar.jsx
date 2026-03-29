import { NavLink } from 'react-router-dom'
import './Navbar.css'

// Navbar component — displayed at the top of every page
// Uses Link or NavLink from react-router-dom for client-side navigation (no page reloads)
// Should contain navigation links to: Dashboard, Profile, Document Library, Settings


export function MyAppNav(){
  return(
    <nav>
      <NavLink to="/" end>
        Dashboard
      </NavLink>

      <NavLink to="/profile" end>
        Profile
      </NavLink>

      <NavLink to="/documents" end>
        Document Library
      </NavLink>

      <NavLink to="/settings" end>
        Settings
      </NavLink>

      {/* This is the new link for your job form */}
      <NavLink to="/jobs/new" end>
        Add Job
      </NavLink>
    </nav>
  )
}
