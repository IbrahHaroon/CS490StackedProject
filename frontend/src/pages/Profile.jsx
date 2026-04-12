import { useEffect, useState } from "react";
import EditModal from "../components/EditModal";
import DeleteConfirmModal from "../components/DeleteConfirmModal";

const API = "http://localhost:8000";

function Profile() {
  const [email, setEmail] = useState("");
  const [userId, setUserId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");
  const token = localStorage.getItem("token");

  // S2-020 / S2-016 — section data
  const [experiences, setExperiences] = useState([]);
  const [educations, setEducations] = useState([]);
  const [skills, setSkills] = useState([]);
  const [careerPrefs, setCareerPrefs] = useState(null);
  const [sectionModal, setSectionModal] = useState(null);
  const [activeRecord, setActiveRecord] = useState(null);
  const [sectionStatus, setSectionStatus] = useState({});
  const [deleteTarget, setDeleteTarget] = useState(null); // { type: "experience"|"education"|"skill", id }
  const [isDeleting, setIsDeleting] = useState(false);

  // Initial fetch — profile, auth, documents
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const safe = (p) => p.catch(() => null);
    Promise.all([
      safe(
        fetch(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        }).then((r) => (r.ok ? r.json() : null))
      ),
      safe(
        fetch(`${API}/profile/me`, {
          headers: { Authorization: `Bearer ${token}` },
        }).then((r) => (r.ok ? r.json() : null))
      ),
      safe(
        fetch(`${API}/documents/me`, {
          headers: { Authorization: `Bearer ${token}` },
        }).then((r) => (r.ok ? r.json() : []))
      ),
    ]).then(([me, prof, docs]) => {
      setEmail(me?.email || "");
      setUserId(me?.user_id || null);
      setProfile(prof);
      setDocuments(docs || []);
      setLoading(false);
    });
  }, []);

  // Secondary fetch — experience, education, skills, career prefs (depends on userId)
  useEffect(() => {
    if (!userId) return;
    Promise.all([
      fetch(`${API}/experience/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`${API}/education/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`${API}/skills/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      fetch(`${API}/career-preferences/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
    ]).then(async ([expRes, eduRes, skillRes, prefRes]) => {
      if (expRes.ok) setExperiences(await expRes.json());
      if (eduRes.ok) setEducations(await eduRes.json());
      if (skillRes.ok) setSkills(await skillRes.json());
      if (prefRes.ok) setCareerPrefs(await prefRes.json());
      // 404 on career-preferences is valid — user just hasn't set any yet
    });
  }, [userId]);

  // ── Profile (summary + about) ──────────────────────────────────────────────

  const saveProfile = async (values) => {
    if (!userId) return "Session error — please sign out and sign back in.";

    let res;
    if (!profile) {
      res = await fetch(`${API}/profile/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          first_name: values.first_name || "",
          last_name: values.last_name || "",
          dob: values.dob || "2000-01-01",
          address: { address: "", state: "", zip_code: 0 },
          phone_number: values.phone_number || null,
          summary: values.summary || null,
        }),
      });
    } else {
      res = await fetch(`${API}/profile/${profile.profile_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(
          Object.fromEntries(Object.entries(values).filter(([, v]) => v !== ""))
        ),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail;
      if (Array.isArray(msg))
        return msg.map((e) => e.msg).join(", ") || "Validation error.";
      return (typeof msg === "string" ? msg : null) || "Failed to save.";
    }

    const updated = await res.json();
    setProfile(updated);
    setModal(null);
    setStatusMessage("Profile saved.");
    setTimeout(() => setStatusMessage(""), 3000);
    return null;
  };

  // ── Experience ─────────────────────────────────────────────────────────────

  const saveExperience = async (values) => {
    const missing = [];
    if (!values.company?.trim()) missing.push("Company");
    if (!values.title?.trim()) missing.push("Job Title");
    if (!values.start_date) missing.push("Start Date");
    if (missing.length > 0) return `Required: ${missing.join(", ")}`;

    let res;
    if (!activeRecord) {
      res = await fetch(`${API}/experience/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          company: values.company,
          title: values.title,
          start_date: values.start_date,
          end_date: values.end_date || null,
          description: values.description || null,
          sort_order: experiences.length,
        }),
      });
    } else {
      res = await fetch(`${API}/experience/${activeRecord.experience_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          company: values.company,
          title: values.title,
          start_date: values.start_date,
          end_date: values.end_date || null,
          clear_end_date: !values.end_date,
          description: values.description || null,
        }),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to save.";
    }

    const saved = await res.json();
    setExperiences((prev) =>
      activeRecord
        ? prev.map((e) =>
            e.experience_id === activeRecord.experience_id ? saved : e
          )
        : [...prev, saved]
    );
    setSectionModal(null);
    setActiveRecord(null);
    setSectionStatus((prev) => ({ ...prev, experience: "Saved!" }));
    setTimeout(
      () => setSectionStatus((prev) => ({ ...prev, experience: "" })),
      3000
    );
    return null;
  };

  const confirmDeleteExperience = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`${API}/experience/${deleteTarget.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setExperiences((prev) =>
          prev.filter((e) => e.experience_id !== deleteTarget.id)
        );
      }
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  const moveExperience = async (index, direction) => {
    const swapIndex = index + direction; // -1 = up, +1 = down
    if (swapIndex < 0 || swapIndex >= experiences.length) return;
    const a = experiences[index];
    const b = experiences[swapIndex];
    await Promise.all([
      fetch(`${API}/experience/${a.experience_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ sort_order: b.sort_order }),
      }),
      fetch(`${API}/experience/${b.experience_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ sort_order: a.sort_order }),
      }),
    ]);
    setExperiences((prev) => {
      const updated = [...prev];
      updated[index] = { ...a, sort_order: b.sort_order };
      updated[swapIndex] = { ...b, sort_order: a.sort_order };
      return updated.sort((x, y) => x.sort_order - y.sort_order);
    });
  };

  // ── Education ──────────────────────────────────────────────────────────────

  const saveEducation = async (values) => {
    const missing = [];
    if (!values.highest_education?.trim()) missing.push("Highest Education");
    if (!values.degree?.trim()) missing.push("Degree");
    if (!values.school_or_college?.trim()) missing.push("School");
    if (!values.field_of_study?.trim()) missing.push("Field of Study");
    if (!values.start_date) missing.push("Start Date");
    if (missing.length > 0) return `Required: ${missing.join(", ")}`;

    let res;
    if (!activeRecord) {
      res = await fetch(`${API}/education/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          highest_education: values.highest_education,
          degree: values.degree,
          school_or_college: values.school_or_college,
          address: {
            address: values.address_street || "",
            state: values.address_state || "",
            zip_code: parseInt(values.address_zip) || 0,
          },
          field_of_study: values.field_of_study,
          start_date: values.start_date,
          end_date: values.end_date || null,
          gpa: values.gpa || null,
        }),
      });
    } else {
      res = await fetch(`${API}/education/${activeRecord.education_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          highest_education: values.highest_education,
          degree: values.degree,
          school_or_college: values.school_or_college,
          field_of_study: values.field_of_study,
          start_date: values.start_date,
          end_date: values.end_date || null,
          gpa: values.gpa || null,
        }),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to save.";
    }

    const saved = await res.json();
    setEducations((prev) =>
      activeRecord
        ? prev.map((e) =>
            e.education_id === activeRecord.education_id ? saved : e
          )
        : [...prev, saved]
    );
    setSectionModal(null);
    setActiveRecord(null);
    setSectionStatus((prev) => ({ ...prev, education: "Saved!" }));
    setTimeout(
      () => setSectionStatus((prev) => ({ ...prev, education: "" })),
      3000
    );
    return null;
  };

  const confirmDeleteEducation = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`${API}/education/${deleteTarget.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setEducations((prev) =>
          prev.filter((e) => e.education_id !== deleteTarget.id)
        );
      }
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  // ── Skills ─────────────────────────────────────────────────────────────────

  const saveSkill = async (values) => {
    if (!values.name?.trim()) return "Skill name is required.";

    let res;
    if (!activeRecord) {
      res = await fetch(`${API}/skills/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          name: values.name,
          category: values.category || null,
          proficiency: values.proficiency || null,
          sort_order: skills.length,
        }),
      });
    } else {
      res = await fetch(`${API}/skills/${activeRecord.skill_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: values.name,
          category: values.category || null,
          proficiency: values.proficiency || null,
        }),
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to save.";
    }

    const saved = await res.json();
    setSkills((prev) =>
      activeRecord
        ? prev.map((s) => (s.skill_id === activeRecord.skill_id ? saved : s))
        : [...prev, saved]
    );
    setSectionModal(null);
    setActiveRecord(null);
    setSectionStatus((prev) => ({ ...prev, skills: "Saved!" }));
    setTimeout(
      () => setSectionStatus((prev) => ({ ...prev, skills: "" })),
      3000
    );
    return null;
  };

  const confirmDeleteSkill = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`${API}/skills/${deleteTarget.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSkills((prev) => prev.filter((s) => s.skill_id !== deleteTarget.id));
      }
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  const moveSkill = async (index, direction) => {
    const swapIndex = index + direction;
    if (swapIndex < 0 || swapIndex >= skills.length) return;
    const a = skills[index];
    const b = skills[swapIndex];
    await Promise.all([
      fetch(`${API}/skills/${a.skill_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ sort_order: b.sort_order }),
      }),
      fetch(`${API}/skills/${b.skill_id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ sort_order: a.sort_order }),
      }),
    ]);
    setSkills((prev) => {
      const updated = [...prev];
      updated[index] = { ...a, sort_order: b.sort_order };
      updated[swapIndex] = { ...b, sort_order: a.sort_order };
      return updated.sort((x, y) => x.sort_order - y.sort_order);
    });
  };

  // ── Career Preferences ─────────────────────────────────────────────────────

  const saveCareerPrefs = async (values) => {
    const res = await fetch(`${API}/career-preferences/user/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        target_roles: values.target_roles || null,
        location_preferences: values.location_preferences || null,
        work_mode: values.work_mode || null,
        salary_preference: values.salary_preference || null,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return err.detail || "Failed to save.";
    }

    const saved = await res.json();
    setCareerPrefs(saved);
    setSectionModal(null);
    setSectionStatus((prev) => ({ ...prev, career: "Saved!" }));
    setTimeout(
      () => setSectionStatus((prev) => ({ ...prev, career: "" })),
      3000
    );
    return null;
  };

  // ── Computed values ────────────────────────────────────────────────────────

  const hasResume = documents.some(
    (d) => d.document_type.toLowerCase() === "resume"
  );

  const completionFields = [
    { label: "First Name", done: !!profile?.first_name },
    { label: "Last Name", done: !!profile?.last_name },
    { label: "Email", done: !!email },
    { label: "Phone Number", done: !!profile?.phone_number },
    { label: "Date of Birth", done: !!profile?.dob },
    { label: "Summary", done: !!profile?.summary },
    { label: "Resume", done: hasResume },
  ];

  const completedCount = completionFields.filter((f) => f.done).length;
  const completionPct = Math.round(
    (completedCount / completionFields.length) * 100
  );
  const missingFields = completionFields.filter((f) => !f.done);

  if (loading)
    return (
      <div style={styles.page}>
        <p style={{ color: "#888" }}>Loading…</p>
      </div>
    );

  // ── Education modal fields ─────────────────────────────────────────────────

  const educationModalFields = () => {
    const rec = activeRecord || {};
    const fields = [
      {
        name: "highest_education",
        label: "Highest Education",
        value: rec.highest_education || "",
        placeholder: "e.g. Bachelor's",
      },
      {
        name: "degree",
        label: "Degree",
        value: rec.degree || "",
        placeholder: "e.g. Bachelor of Science",
      },
      {
        name: "school_or_college",
        label: "School / College",
        value: rec.school_or_college || "",
        placeholder: "e.g. Rutgers University",
      },
      {
        name: "field_of_study",
        label: "Field of Study",
        value: rec.field_of_study || "",
        placeholder: "e.g. Computer Science",
      },
      {
        name: "start_date",
        label: "Start Date",
        value: rec.start_date || "",
        type: "date",
      },
      {
        name: "end_date",
        label: "End Date (leave blank if current)",
        value: rec.end_date || "",
        type: "date",
      },
      {
        name: "gpa",
        label: "GPA (optional)",
        value: rec.gpa != null ? String(rec.gpa) : "",
        placeholder: "e.g. 3.8",
      },
    ];
    if (!activeRecord) {
      fields.push(
        {
          name: "address_street",
          label: "Street Address (optional)",
          value: "",
          placeholder: "e.g. 123 College Ave",
        },
        {
          name: "address_state",
          label: "State (optional)",
          value: "",
          placeholder: "e.g. NJ",
        },
        {
          name: "address_zip",
          label: "Zip Code (optional)",
          value: "",
          placeholder: "e.g. 08854",
        }
      );
    }
    return fields;
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Profile</h1>
      <p style={styles.subtitle}>Your account information at a glance.</p>

      {statusMessage && <p style={styles.status}>{statusMessage}</p>}

      {/* Profile Completion */}
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Profile Completion</h2>
        <p style={styles.percentageText}>{completionPct}% complete</p>
        <div style={styles.progressBar}>
          <div style={{ ...styles.progressFill, width: `${completionPct}%` }} />
        </div>
        <p style={styles.helperText}>
          {completedCount} of {completionFields.length} items complete
        </p>
      </div>

      {/* Profile Summary */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>Profile Summary</h2>
          <button style={styles.editBtn} onClick={() => setModal("info")}>
            Edit
          </button>
        </div>
        <div style={styles.summaryGrid}>
          <InfoRow label="First Name" value={profile?.first_name} />
          <InfoRow label="Last Name" value={profile?.last_name} />
          <InfoRow label="Email" value={email} />
          <InfoRow label="Phone" value={profile?.phone_number} />
          <InfoRow label="Date of Birth" value={profile?.dob} />
          <InfoRow
            label="Resume"
            value={hasResume ? "Uploaded" : "Not uploaded"}
          />
        </div>
      </div>

      {/* About */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>About</h2>
          <button style={styles.editBtn} onClick={() => setModal("about")}>
            Edit
          </button>
        </div>
        {profile?.summary ? (
          <p style={styles.summaryText}>{profile.summary}</p>
        ) : (
          <p style={{ color: "#aaa", fontSize: "14px" }}>
            No summary added yet.
          </p>
        )}
      </div>

      {/* Missing Information */}
      {missingFields.length > 0 && (
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Missing Information</h2>
          <ul style={styles.missingList}>
            {missingFields.map((f) => (
              <li key={f.label} style={styles.missingItem}>
                {f.label} —{" "}
                <span style={{ color: "#888" }}>
                  {f.label === "Resume" ? (
                    <a href="/documents" style={{ color: "#4f8ef7" }}>
                      upload via Document Library
                    </a>
                  ) : (
                    "update above"
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Experience (S2-016) */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>Experience</h2>
          <button
            style={styles.addBtn}
            onClick={() => {
              setActiveRecord(null);
              setSectionModal("add-experience");
            }}
          >
            + Add
          </button>
        </div>
        {experiences.length === 0 ? (
          <p style={styles.emptyText}>No experience entries yet.</p>
        ) : (
          experiences.map((exp, index) => (
            <div key={exp.experience_id} style={styles.itemRow}>
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "6px",
                  flexShrink: 0,
                }}
              >
                <button
                  style={styles.reorderBtn}
                  onClick={() => moveExperience(index, -1)}
                  disabled={index === 0}
                  title="Move up"
                >
                  ↑
                </button>
                <button
                  style={styles.reorderBtn}
                  onClick={() => moveExperience(index, 1)}
                  disabled={index === experiences.length - 1}
                  title="Move down"
                >
                  ↓
                </button>
              </div>
              <div style={styles.itemInfo}>
                <p style={styles.itemPrimary}>
                  {exp.title} — {exp.company}
                </p>
                <p style={styles.itemSecondary}>
                  {exp.start_date} – {exp.end_date || "Present"}
                </p>
                {exp.description && (
                  <p style={{ ...styles.itemSecondary, marginTop: "4px" }}>
                    {exp.description}
                  </p>
                )}
              </div>
              <div style={styles.itemActions}>
                <button
                  style={styles.editBtn}
                  onClick={() => {
                    setActiveRecord(exp);
                    setSectionModal("edit-experience");
                  }}
                >
                  Edit
                </button>
                <button
                  style={styles.deleteBtn}
                  onClick={() =>
                    setDeleteTarget({
                      type: "experience",
                      id: exp.experience_id,
                    })
                  }
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
        {sectionStatus.experience && (
          <p style={styles.sectionStatus}>{sectionStatus.experience}</p>
        )}
      </div>

      {/* Education (S2-020) */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>Education</h2>
          <button
            style={styles.addBtn}
            onClick={() => {
              setActiveRecord(null);
              setSectionModal("add-education");
            }}
          >
            + Add
          </button>
        </div>
        {educations.length === 0 ? (
          <p style={styles.emptyText}>No education records yet.</p>
        ) : (
          educations.map((edu) => (
            <div key={edu.education_id} style={styles.itemRow}>
              <div style={styles.itemInfo}>
                <p style={styles.itemPrimary}>
                  {edu.degree} in {edu.field_of_study}
                </p>
                <p style={styles.itemSecondary}>
                  {edu.school_or_college} · {edu.start_date}–
                  {edu.end_date || "Present"}
                  {edu.gpa ? ` · GPA: ${edu.gpa}` : ""}
                </p>
              </div>
              <div style={styles.itemActions}>
                <button
                  style={styles.editBtn}
                  onClick={() => {
                    setActiveRecord(edu);
                    setSectionModal("edit-education");
                  }}
                >
                  Edit
                </button>
                <button
                  style={styles.deleteBtn}
                  onClick={() =>
                    setDeleteTarget({ type: "education", id: edu.education_id })
                  }
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
        {sectionStatus.education && (
          <p style={styles.sectionStatus}>{sectionStatus.education}</p>
        )}
      </div>

      {/* Skills (S2-020) */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>Skills</h2>
          <button
            style={styles.addBtn}
            onClick={() => {
              setActiveRecord(null);
              setSectionModal("add-skill");
            }}
          >
            + Add
          </button>
        </div>
        {skills.length === 0 ? (
          <p style={styles.emptyText}>No skills added yet.</p>
        ) : (
          skills.map((skill, index) => (
            <div key={skill.skill_id} style={styles.itemRow}>
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "6px",
                  flexShrink: 0,
                }}
              >
                <button
                  style={styles.reorderBtn}
                  onClick={() => moveSkill(index, -1)}
                  disabled={index === 0}
                  title="Move up"
                >
                  ↑
                </button>
                <button
                  style={styles.reorderBtn}
                  onClick={() => moveSkill(index, 1)}
                  disabled={index === skills.length - 1}
                  title="Move down"
                >
                  ↓
                </button>
              </div>
              <div style={styles.itemInfo}>
                <p style={styles.itemPrimary}>{skill.name}</p>
                {(skill.category || skill.proficiency) && (
                  <p style={styles.itemSecondary}>
                    {[skill.category, skill.proficiency]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                )}
              </div>
              <div style={styles.itemActions}>
                <button
                  style={styles.editBtn}
                  onClick={() => {
                    setActiveRecord(skill);
                    setSectionModal("edit-skill");
                  }}
                >
                  Edit
                </button>
                <button
                  style={styles.deleteBtn}
                  onClick={() =>
                    setDeleteTarget({ type: "skill", id: skill.skill_id })
                  }
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
        {sectionStatus.skills && (
          <p style={styles.sectionStatus}>{sectionStatus.skills}</p>
        )}
      </div>

      {/* Career Preferences (S2-020) */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>Career Preferences</h2>
          <button
            style={styles.editBtn}
            onClick={() => setSectionModal("edit-career")}
          >
            Edit
          </button>
        </div>
        {careerPrefs ? (
          <div style={styles.summaryGrid}>
            <InfoRow label="Target Roles" value={careerPrefs.target_roles} />
            <InfoRow
              label="Location"
              value={careerPrefs.location_preferences}
            />
            <InfoRow label="Work Mode" value={careerPrefs.work_mode} />
            <InfoRow
              label="Salary"
              value={formatSalary(careerPrefs.salary_preference)}
            />
          </div>
        ) : (
          <p style={styles.emptyText}>No preferences set yet.</p>
        )}
        {sectionStatus.career && (
          <p style={styles.sectionStatus}>{sectionStatus.career}</p>
        )}
      </div>

      {/* ── Modals ── */}

      {/* Profile Summary edit */}
      {modal === "info" && (
        <EditModal
          title="Edit Profile Info"
          fields={[
            {
              name: "first_name",
              label: "First Name",
              value: profile?.first_name || "",
            },
            {
              name: "last_name",
              label: "Last Name",
              value: profile?.last_name || "",
            },
            {
              name: "phone_number",
              label: "Phone Number",
              value: profile?.phone_number || "",
              placeholder: "e.g. 201-555-0101 or +1 (555) 555-0100",
            },
            {
              name: "dob",
              label: "Date of Birth",
              value: profile?.dob || "",
              type: "date",
            },
          ]}
          onSave={saveProfile}
          onCancel={() => setModal(null)}
        />
      )}

      {/* About edit */}
      {modal === "about" && (
        <EditModal
          title="Edit About"
          fields={[
            {
              name: "summary",
              label: "Summary",
              value: profile?.summary || "",
              type: "textarea",
              placeholder: "Tell us about yourself…",
            },
          ]}
          onSave={saveProfile}
          onCancel={() => setModal(null)}
        />
      )}

      {/* Experience add / edit */}
      {(sectionModal === "add-experience" ||
        sectionModal === "edit-experience") && (
        <EditModal
          title={
            sectionModal === "add-experience"
              ? "Add Experience"
              : "Edit Experience"
          }
          fields={[
            {
              name: "company",
              label: "Company",
              value: activeRecord?.company || "",
              placeholder: "e.g. Google",
            },
            {
              name: "title",
              label: "Job Title",
              value: activeRecord?.title || "",
              placeholder: "e.g. Software Engineer",
            },
            {
              name: "start_date",
              label: "Start Date",
              value: activeRecord?.start_date || "",
              type: "date",
            },
            {
              name: "end_date",
              label: "End Date (blank = current)",
              value: activeRecord?.end_date || "",
              type: "date",
            },
            {
              name: "description",
              label: "Description (optional)",
              value: activeRecord?.description || "",
              type: "textarea",
              placeholder: "Responsibilities, achievements…",
            },
          ]}
          onSave={saveExperience}
          onCancel={() => {
            setSectionModal(null);
            setActiveRecord(null);
          }}
        />
      )}

      {/* Education add / edit */}
      {(sectionModal === "add-education" ||
        sectionModal === "edit-education") && (
        <EditModal
          title={
            sectionModal === "add-education"
              ? "Add Education"
              : "Edit Education"
          }
          fields={educationModalFields()}
          onSave={saveEducation}
          onCancel={() => {
            setSectionModal(null);
            setActiveRecord(null);
          }}
        />
      )}

      {/* Skill add / edit */}
      {(sectionModal === "add-skill" || sectionModal === "edit-skill") && (
        <EditModal
          title={sectionModal === "add-skill" ? "Add Skill" : "Edit Skill"}
          fields={[
            {
              name: "name",
              label: "Skill Name",
              value: activeRecord?.name || "",
              placeholder: "e.g. Python",
            },
            {
              name: "category",
              label: "Category (optional)",
              type: "select",
              value: activeRecord?.category || "",
              placeholder: "— Select a category —",
              options: [
                "Technical Skills",
                "Soft Skills",
                "Programming Languages",
                "Frameworks & Libraries",
                "Tools & Platforms",
                "Data & Analytics",
                "Design",
                "Marketing",
                "Finance",
                "Management & Leadership",
                "Communication",
                "Languages (spoken)",
                "Other",
              ],
            },
            {
              name: "proficiency",
              label: "Proficiency (optional)",
              type: "select",
              value: activeRecord?.proficiency || "",
              placeholder: "— Select proficiency —",
              options: ["Beginner", "Intermediate", "Advanced", "Expert"],
            },
          ]}
          onSave={saveSkill}
          onCancel={() => {
            setSectionModal(null);
            setActiveRecord(null);
          }}
        />
      )}

      {/* Career Preferences edit */}
      {sectionModal === "edit-career" && (
        <EditModal
          title="Edit Career Preferences"
          fields={[
            {
              name: "target_roles",
              label: "Target Roles",
              value: careerPrefs?.target_roles || "",
              placeholder: "e.g. Software Engineer, Backend Developer",
            },
            {
              name: "location_preferences",
              label: "Location Preferences",
              value: careerPrefs?.location_preferences || "",
              placeholder: "e.g. New York, Remote",
            },
            {
              name: "work_mode",
              label: "Work Mode",
              value: careerPrefs?.work_mode || "",
              placeholder: "e.g. Hybrid, Remote, On-site",
            },
            {
              name: "salary_preference",
              label: "Salary Preference",
              value: careerPrefs?.salary_preference || "",
              placeholder: "e.g. $90,000+",
            },
          ]}
          onSave={saveCareerPrefs}
          onCancel={() => setSectionModal(null)}
        />
      )}

      {/* Delete confirmation */}
      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        title={
          deleteTarget?.type === "experience"
            ? "Delete experience entry?"
            : deleteTarget?.type === "education"
              ? "Delete education record?"
              : "Delete skill?"
        }
        message={
          deleteTarget?.type === "experience"
            ? "This experience entry will be permanently removed."
            : deleteTarget?.type === "education"
              ? "This education record will be permanently removed."
              : "This skill will be permanently removed."
        }
        onCancel={() => setDeleteTarget(null)}
        onConfirm={
          deleteTarget?.type === "experience"
            ? confirmDeleteExperience
            : deleteTarget?.type === "education"
              ? confirmDeleteEducation
              : confirmDeleteSkill
        }
        isDeleting={isDeleting}
      />
    </div>
  );
}

function formatSalary(value) {
  if (!value) return value;
  // Replace any plain integer-like number in the string with formatted currency
  return value.replace(/\d+/g, (n) =>
    Number(n) >= 1000 ? "$" + Number(n).toLocaleString("en-US") : n
  );
}

function InfoRow({ label, value }) {
  return (
    <div>
      <p style={styles.summaryLabel}>{label}</p>
      <p style={styles.summaryValue}>
        {value || <span style={{ color: "#aaa" }}>Not set</span>}
      </p>
    </div>
  );
}

const styles = {
  page: {
    maxWidth: "900px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: { fontSize: "32px", marginBottom: "8px" },
  subtitle: { color: "#555", marginBottom: "24px" },
  status: { color: "green", fontSize: "14px", marginBottom: "12px" },
  sectionStatus: {
    color: "green",
    fontSize: "13px",
    marginTop: "8px",
    marginBottom: 0,
  },
  card: {
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    borderRadius: "12px",
    padding: "24px",
    marginBottom: "20px",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },
  cardTitle: { fontSize: "22px", margin: 0, color: "#444" },
  editBtn: {
    padding: "4px 14px",
    border: "1px solid #ccc",
    borderRadius: "6px",
    background: "none",
    cursor: "pointer",
    fontSize: "14px",
    color: "#333",
  },
  addBtn: {
    padding: "4px 14px",
    border: "1px solid #4f8ef7",
    borderRadius: "6px",
    background: "none",
    cursor: "pointer",
    fontSize: "14px",
    color: "#4f8ef7",
  },
  deleteBtn: {
    padding: "4px 14px",
    border: "1px solid #ef4444",
    borderRadius: "6px",
    background: "none",
    cursor: "pointer",
    fontSize: "14px",
    color: "#ef4444",
  },
  reorderBtn: {
    padding: "2px 7px",
    border: "1px solid #ccc",
    borderRadius: "4px",
    background: "none",
    cursor: "pointer",
    fontSize: "13px",
    color: "#555",
    lineHeight: 1,
  },
  emptyText: { color: "#aaa", fontSize: "14px", margin: 0 },
  itemRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: "10px 0",
    borderBottom: "1px solid #f0f0f0",
  },
  itemInfo: { flex: 1, marginRight: "12px" },
  itemPrimary: {
    margin: 0,
    fontSize: "15px",
    fontWeight: "600",
    color: "#222",
  },
  itemSecondary: { margin: "3px 0 0", fontSize: "13px", color: "#666" },
  itemActions: { display: "flex", gap: "8px", flexShrink: 0 },
  percentageText: { fontSize: "24px", fontWeight: "700", color: "#333" },
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
  summaryLabel: { fontSize: "13px", color: "#555", margin: 0 },
  summaryValue: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#222",
    wordBreak: "break-word",
    margin: "4px 0 0",
  },
  summaryText: { fontSize: "15px", color: "#333", lineHeight: "1.6" },
  missingList: { paddingLeft: "20px" },
  missingItem: { marginBottom: "8px", color: "#333" },
};

export default Profile;
