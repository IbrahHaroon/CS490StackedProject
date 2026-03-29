import { useMemo, useState } from "react";

function Profile() {
  // Using mock data for now (later this will come from backend)
  const [profileData, setProfileData] = useState({
    fullName: "Amina Mahmoud",
    email: "am3378@njit.edu",
    phone: "",
    location: "New Jersey",
    bio: "",
    linkedin: "",
    github: "https://github.com/aminamah-hash",
    resumeUploaded: false,
  });

  // These are the fields that count toward completion
  const completionFields = [
    { key: "fullName", label: "Full Name" },
    { key: "email", label: "Email" },
    { key: "phone", label: "Phone Number" },
    { key: "location", label: "Location" },
    { key: "bio", label: "Bio" },
    { key: "linkedin", label: "LinkedIn" },
    { key: "github", label: "GitHub" },
    { key: "resumeUploaded", label: "Resume Upload" },
  ];

  // Determines if a field is "completed"
  const isFieldComplete = (value) => {
    if (typeof value === "boolean") return value;
    return value && value.trim() !== "";
  };

  // Count how many fields are completed
  const completedCount = useMemo(() => {
    return completionFields.filter((field) =>
      isFieldComplete(profileData[field.key])
    ).length;
  }, [profileData]);

  // Calculate percentage
  const completionPercentage = Math.round(
    (completedCount / completionFields.length) * 100
  );

  // Get list of missing fields
  const missingFields = completionFields.filter(
    (field) => !isFieldComplete(profileData[field.key])
  );

  // Handle input + checkbox updates
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    setProfileData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Profile</h1>

      <p style={styles.subtitle}>
        Complete your profile to improve readiness across the platform.
      </p>

      {/* Completion card */}
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Profile Completion</h2>

        <p style={styles.percentageText}>
          {completionPercentage}% complete
        </p>

        <div style={styles.progressBar}>
          <div
            style={{
              ...styles.progressFill,
              width: `${completionPercentage}%`,
            }}
          />
        </div>

        <p style={styles.helperText}>
          {completedCount} of {completionFields.length} profile items completed
        </p>
      </div>

      {/* Summary card */}
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Profile Summary</h2>

        <div style={styles.summaryGrid}>
          <div>
            <p style={styles.summaryLabel}>Full Name</p>
            <p style={styles.summaryValue}>
              {profileData.fullName || "Not added"}
            </p>
          </div>

          <div>
            <p style={styles.summaryLabel}>Email</p>
            <p style={styles.summaryValue}>
              {profileData.email || "Not added"}
            </p>
          </div>

          <div>
            <p style={styles.summaryLabel}>Phone</p>
            <p style={styles.summaryValue}>
              {profileData.phone || "Not added"}
            </p>
          </div>

          <div>
            <p style={styles.summaryLabel}>Location</p>
            <p style={styles.summaryValue}>
              {profileData.location || "Not added"}
            </p>
          </div>

          <div>
            <p style={styles.summaryLabel}>LinkedIn</p>
            <p style={styles.summaryValue}>
              {profileData.linkedin || "Not added"}
            </p>
          </div>

          <div>
            <p style={styles.summaryLabel}>GitHub</p>

            {/* Making the GitHub link clickable + fixing overflow */}
            <p style={styles.summaryValue}>
              {profileData.github ? (
                <a
                  href={profileData.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={styles.link}
                >
                  {profileData.github}
                </a>
              ) : (
                "Not added"
              )}
            </p>
          </div>

          <div>
            <p style={styles.summaryLabel}>Resume</p>
            <p style={styles.summaryValue}>
              {profileData.resumeUploaded ? "Uploaded" : "Not uploaded"}
            </p>
          </div>
        </div>
      </div>

      {/* Missing fields */}
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Missing Information</h2>

        {missingFields.length === 0 ? (
          <p style={styles.successText}>
            Your profile is fully complete.
          </p>
        ) : (
          <ul style={styles.missingList}>
            {missingFields.map((field) => (
              <li key={field.key} style={styles.missingItem}>
                Add {field.label}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Editable demo section */}
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Edit Profile Preview</h2>

        <p style={styles.helperText}>
          These inputs are local for now and demonstrate completion logic.
        </p>

        <div style={styles.formGrid}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Phone Number</label>
            <input
              type="text"
              name="phone"
              value={profileData.phone}
              onChange={handleChange}
              style={styles.input}
              placeholder="Enter your phone number"
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Bio</label>
            <input
              type="text"
              name="bio"
              value={profileData.bio}
              onChange={handleChange}
              style={styles.input}
              placeholder="Write a short bio"
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>LinkedIn</label>
            <input
              type="text"
              name="linkedin"
              value={profileData.linkedin}
              onChange={handleChange}
              style={styles.input}
              placeholder="Enter your LinkedIn URL"
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                name="resumeUploaded"
                checked={profileData.resumeUploaded}
                onChange={handleChange}
              />
              Resume uploaded
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

// Styles (keeping inline for now for speed)
const styles = {
  page: {
    maxWidth: "900px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: { fontSize: "32px", marginBottom: "8px" },
  subtitle: { color: "#555", marginBottom: "24px" },

  card: {
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    borderRadius: "12px",
    padding: "24px",
    marginBottom: "20px",
  },

  cardTitle: { fontSize: "22px", marginBottom: "12px" },
  percentageText: { fontSize: "24px", fontWeight: "700" },

  progressBar: {
    width: "100%",
    height: "14px",
    backgroundColor: "#e5e7eb",
    borderRadius: "999px",
    overflow: "hidden",
    margin: "10px 0",
  },

  progressFill: {
    height: "100%",
    backgroundColor: "#22c55e",
    transition: "width 0.3s ease",
  },

  helperText: { fontSize: "14px", color: "#555" },

  summaryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
  },

  summaryLabel: { fontSize: "13px", color: "#666" },

  summaryValue: {
    fontSize: "15px",
    fontWeight: "600",

    // Fix for long text like URLs overflowing
    wordBreak: "break-word",
    overflowWrap: "anywhere",
  },

  link: {
    color: "#2563eb",
    textDecoration: "none",
  },

  missingList: { paddingLeft: "20px" },
  missingItem: { marginBottom: "8px" },
  successText: { color: "green", fontWeight: "600" },

  formGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
    gap: "16px",
  },

  inputGroup: { display: "flex", flexDirection: "column", gap: "8px" },
  label: { fontWeight: "600" },

  input: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ccc",
  },

  checkboxLabel: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginTop: "28px",
    fontWeight: "600",
  },
};

export default Profile;