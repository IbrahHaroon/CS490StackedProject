import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

const sampleJobs = [
  {
    id: 1,
    company: "Google",
    title: "Software Engineer",
    type: "Full-time",
    salary: "$120k - $180k",
    location: "Mountain View, CA",
    date: "2026-03-25",
    description: "We are looking for a talented Software Engineer to join our team and help build the next generation of cloud infrastructure. You will work alongside world-class engineers to design, develop, and maintain scalable systems that serve billions of users.",
    requirements: "3+ years of software development experience. Proficiency in one or more of: Java, Python, Go, C++. Experience with distributed systems and cloud computing.",
    qualifications: "BS in Computer Science or related field. Strong problem-solving and analytical skills. Excellent communication and collaboration abilities."
  },
  {
    id: 2,
    company: "Amazon",
    title: "Frontend Developer",
    type: "Full-time",
    salary: "$110k - $160k",
    location: "Seattle, WA",
    date: "2026-03-22",
    description: "Join Amazon's retail team to build customer-facing web applications used by millions. You'll develop responsive, performant UIs and collaborate with designers and backend engineers to deliver seamless shopping experiences.",
    requirements: "2+ years of frontend development experience. Strong skills in React, JavaScript/TypeScript, HTML, and CSS. Familiarity with RESTful APIs.",
    qualifications: "BS in Computer Science or equivalent experience. Portfolio of web projects. Experience with testing frameworks."
  },
  {
    id: 3,
    company: "Spotify",
    title: "Data Analyst Intern",
    type: "Internship",
    salary: "$35/hr",
    location: "New York, NY",
    date: "2026-03-20",
    description: "Spotify is seeking a Data Analyst Intern to support our content and marketplace teams. You will analyze user listening patterns, build dashboards, and provide insights that drive product decisions.",
    requirements: "Currently pursuing a degree in Data Science, Statistics, or related field. Experience with SQL and Python. Familiarity with data visualization tools.",
    qualifications: "Strong analytical mindset. Interest in music and media technology. Ability to communicate findings to non-technical stakeholders."
  }
]

function Dashboard() {
  const [selectedJob, setSelectedJob] = useState(sampleJobs[0])
  const jobBoardRef = useRef(null)
  const navigate = useNavigate()

  const scrollToJobBoard = () => {
    jobBoardRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="dashboard">
      <h1 className="dashboard-welcome">Welcome</h1>

      <div className="dashboard-preview-grid">
        <div className="preview-card preview-card-jobs">
          <div className="preview-card-header">
            <h2>Jobs for You</h2>
            <button className="view-more-btn" onClick={scrollToJobBoard}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            {sampleJobs.slice(0, 2).map(job => (
              <div key={job.id} className="preview-job-item">
                <span className="preview-job-company">{job.company}</span>
                <span className="preview-job-title">{job.title}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="preview-card preview-card-apps">
          <div className="preview-card-header">
            <h2>Current Apps</h2>
            <button className="view-more-btn" onClick={() => navigate('/applications')}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            <p className="preview-placeholder">No applications yet</p>
          </div>
        </div>

        <div className="preview-card preview-card-docs">
          <div className="preview-card-header">
            <h2>Documents</h2>
            <button className="view-more-btn" onClick={() => navigate('/documents')}>
              View More →
            </button>
          </div>
          <div className="preview-card-body">
            <p className="preview-placeholder">No documents yet</p>
          </div>
        </div>
      </div>

      <div className="job-board" ref={jobBoardRef}>
        <div className="job-board-list">
          {sampleJobs.map(job => (
            <div
              key={job.id}
              className={`job-card ${selectedJob.id === job.id ? 'job-card-selected' : ''}`}
              onClick={() => setSelectedJob(job)}
            >
              <span className="job-card-company">{job.company}</span>
              <h3 className="job-card-title">{job.title}</h3>
              <span className="job-card-meta">{job.type} &middot; {job.salary}</span>
              <span className="job-card-meta">{job.location} &middot; {job.date}</span>
            </div>
          ))}
        </div>

        <div className="job-board-detail">
          <h2 className="job-detail-title">{selectedJob.title} @ {selectedJob.company}</h2>
          <p className="job-detail-meta">{selectedJob.type} &middot; {selectedJob.salary}</p>
          <p className="job-detail-meta">{selectedJob.location} &middot; {selectedJob.date}</p>

          <div className="job-detail-section">
            <h3>Job Description</h3>
            <p>{selectedJob.description}</p>
          </div>

          <div className="job-detail-section">
            <h3>Requirements</h3>
            <p>{selectedJob.requirements}</p>
          </div>

          <div className="job-detail-section">
            <h3>Qualifications</h3>
            <p>{selectedJob.qualifications}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
