import { useState } from "react";

function Settings() {
  // I kept all the form values inside one object so everything related to the settings form stays in one place and is easier to update.
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    emailNotifications: true,
    darkMode: false,
  });

  // This stores validation errors for specific fields.
  // For example, if email is invalid, errors.email will hold that message.
  const [errors, setErrors] = useState({});

  // This is just for user feedback after submitting the form.
  // Right now it shows a simple success or failure message.
  const [statusMessage, setStatusMessage] = useState("");

  // This helps simulate a real save action.
  // While this is true, the button changes to save.
  const [isSaving, setIsSaving] = useState(false);

  // This handles both text inputs and checkboxes.
  // For checkboxes, I need to use "checked" instead of "value".
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  // Keeping validation in its own function makes the submit logic cleaner.
  // This also makes it easier to expand later if more settings get added.
  const validateForm = () => {
    const newErrors = {};

    // Full name should not be blank
    if (!formData.fullName.trim()) {
      newErrors.fullName = "Full name is required.";
    }

    // Email should not be blank and should at least look like an email
    if (!formData.email.trim()) {
      newErrors.email = "Email is required.";
    } else if (!formData.email.includes("@")) {
      newErrors.email = "Enter a valid email.";
    }

    return newErrors;
  };

  // This runs when the user clicks Save Changes.
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Run validation first before pretending to save anything
    const validationErrors = validateForm();
    setErrors(validationErrors);

    // Clear any old status message so the user only sees the newest result
    setStatusMessage("");

    // If there are validation errors, stop here
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSaving(true);

    try {
      // This is just simulating a backend request for now.
      // Later this can be replaced with a real API call.
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setStatusMessage("Settings saved.");
    } catch (error) {
      // Even though this mock version probably will not fail,
      // I still kept this here because real save logic should handle errors.
      setStatusMessage("Failed to save settings.");
    } finally {
      // Always turn off the loading state at the end
      setIsSaving(false);
    }
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Settings</h1>

      <p style={styles.subtitle}>
        Manage your account preferences and application settings.
      </p>

      <form onSubmit={handleSubmit} style={styles.formCard}>
        {/* Account section holds the main user identity fields */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Account</h2>

          <label style={styles.label}>Full Name</label>
          <input
            type="text"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            style={styles.input}
            placeholder="Enter your full name"
          />
          {errors.fullName && <p style={styles.error}>{errors.fullName}</p>}

          <label style={styles.label}>Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            style={styles.input}
            placeholder="Enter your email"
          />
          {errors.email && <p style={styles.error}>{errors.email}</p>}
        </div>

        {/* Preferences section is using local state for now.
            The checkboxes work, but they are not hooked up to a backend yet. */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Preferences</h2>

          <label style={styles.checkboxRow}>
            <input
              type="checkbox"
              name="emailNotifications"
              checked={formData.emailNotifications}
              onChange={handleChange}
            />
            Email notifications
          </label>

          <label style={styles.checkboxRow}>
            <input
              type="checkbox"
              name="darkMode"
              checked={formData.darkMode}
              onChange={handleChange}
            />
            Dark mode
          </label>

          {/* I added these helper lines so the toggles feel more obvious.
              That way, when the user clicks them, the page visibly updates. */}
          <p style={styles.helperText}>
            Email notifications are currently{" "}
            <strong>{formData.emailNotifications ? "enabled" : "disabled"}</strong>.
          </p>

          <p style={styles.helperText}>
            Dark mode is currently{" "}
            <strong>{formData.darkMode ? "enabled" : "disabled"}</strong>.
          </p>
        </div>

        {/* This is just a placeholder section for now.
            The button does not do anything yet, but it makes the page feel more complete. */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Security</h2>
          <button type="button" style={styles.secondaryButton}>
            Change Password
          </button>
        </div>

        {/* Main submit button */}
        <div style={styles.actions}>
          <button type="submit" style={styles.primaryButton} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Changes"}
          </button>
        </div>

        {/* This only shows after submit if there is a success/failure message */}
        {statusMessage && <p style={styles.status}>{statusMessage}</p>}
      </form>
    </div>
  );
}

// I kept the styles in this file for now just to move faster during the baseline build.
// Later we can move this into a separate CSS file to clean things up.
const styles = {
  page: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: {
    fontSize: "32px",
    marginBottom: "8px",
  },
  subtitle: {
    color: "#555",
    marginBottom: "24px",
  },
  formCard: {
    border: "1px solid #ddd",
    borderRadius: "12px",
    padding: "24px",
    backgroundColor: "#fff",
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  section: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  sectionTitle: {
    fontSize: "20px",
  },
  label: {
    fontWeight: "600",
  },
  input: {
    padding: "10px",
    borderRadius: "8px",
    border: "1px solid #ccc",
  },
  checkboxRow: {
    display: "flex",
    gap: "10px",
    alignItems: "center",
  },
  helperText: {
    fontSize: "14px",
    color: "#555",
    margin: 0,
  },
  actions: {
    display: "flex",
    justifyContent: "flex-end",
  },
  primaryButton: {
    padding: "10px 16px",
    borderRadius: "8px",
    border: "none",
    cursor: "pointer",
  },
  secondaryButton: {
    padding: "10px 16px",
    borderRadius: "8px",
    border: "1px solid #ccc",
    cursor: "pointer",
  },
  error: {
    color: "red",
    fontSize: "14px",
    margin: 0,
  },
  status: {
    color: "green",
    fontSize: "14px",
  },
};

export default Settings;
