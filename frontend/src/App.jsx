import { Routes, Route } from 'react-router-dom'
import { MyAppNav } from './components/Navbar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Profile from './pages/Profile.jsx'
import DocumentLibrary from './pages/DocumentLibrary.jsx'
import Settings from './pages/Settings.jsx'
import Applications from './pages/Applications.jsx'
import './App.css'

function App() {
  return (
    <>
      <MyAppNav />
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/documents" element={<DocumentLibrary />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/applications" element={<Applications />} />
        </Routes>
      </main>
    </>
  )
}

export default App
