-- =============================================================================
-- SEED DATA SCRIPT — Sprint 2
-- Populates demo data for presentation / development.
--
-- Two accounts:
--   User A  usera@demo.com / Demo1234!  — full data (profile, education,
--           experience, skills, career prefs, 4 applications with activity,
--           interviews, follow-ups, documents)
--   User B  userb@demo.com / Demo1234!  — bare account, no data
--
-- Prerequisites:
--   Run schema.sql first to recreate all tables from scratch.
--
-- Usage (from backend/scripts/):
--   psql $DATABASE_URL -f seed.sql
--
-- Password hash below is bcrypt of "Demo1234!" with 12 rounds.
-- =============================================================================

BEGIN;

-- =============================================================================
-- CLEANUP (safe to re-run — DELETE-based so FK constraints handle ordering)
-- =============================================================================
DELETE FROM token_blacklist;
DELETE FROM interview;
DELETE FROM follow_up;
DELETE FROM job_activity;
DELETE FROM documents;
DELETE FROM applied_jobs;
DELETE FROM career_preferences;
DELETE FROM skills;
DELETE FROM experience;
DELETE FROM education;
DELETE FROM password_reset_token;
DELETE FROM profile;
DELETE FROM credentials;
DELETE FROM "position";
DELETE FROM recruiter_password_reset_token;
DELETE FROM recruiter_credentials;
DELETE FROM recruiter;
DELETE FROM company;
DELETE FROM "user";
DELETE FROM address;

-- =============================================================================
-- ADDRESSES
-- IDs: 1 = User A home, 2 = NJIT, 3 = Google, 4 = Microsoft,
--      5 = Amazon, 6 = Meta
-- =============================================================================
INSERT INTO address (address_id, address, state, zip_code) VALUES
    (1, '123 Main Street',          'NJ', 7030),
    (2, '323 Dr Martin Luther King Jr Blvd', 'NJ', 7102),
    (3, '1600 Amphitheatre Pkwy',   'CA', 94043),
    (4, '1 Microsoft Way',          'WA', 98052),
    (5, '410 Terry Ave N',          'WA', 98109),
    (6, '1 Hacker Way',             'CA', 94025);

-- =============================================================================
-- USERS
-- =============================================================================
INSERT INTO "user" (user_id, email) VALUES
    (1, 'usera@demo.com'),
    (2, 'userb@demo.com');

-- =============================================================================
-- CREDENTIALS  (bcrypt of "Demo1234!", 12 rounds)
-- =============================================================================
INSERT INTO credentials (credential_id, user_id, hashed_password) VALUES
    (1, 1, '$2b$12$EY2gk/D84cdS16h89DIILucUTdjf.FGvnPTdm2dxQrvVJ0XdrZnxq'),
    (2, 2, '$2b$12$EY2gk/D84cdS16h89DIILucUTdjf.FGvnPTdm2dxQrvVJ0XdrZnxq');

-- =============================================================================
-- PROFILE  (User A only)
-- =============================================================================
INSERT INTO profile (profile_id, user_id, address_id, first_name, last_name, dob, phone_number, summary) VALUES
    (1, 1, 1,
     'Alex', 'Johnson',
     '1999-06-15',
     '201-555-0101',
     'Computer Science senior seeking full-time software engineering roles. Experienced in Python, React, and PostgreSQL.');

-- =============================================================================
-- EDUCATION  (User A — NJIT, with Sprint 2 fields)
-- =============================================================================
INSERT INTO education (education_id, user_id, address_id, highest_education, degree, school_or_college,
                       field_of_study, start_date, end_date, gpa) VALUES
    (1, 1, 2,
     'Bachelor''s',
     'Computer Science',
     'New Jersey Institute of Technology',
     'Computer Science',
     '2021-09-01',
     '2025-05-15',
     '3.7/4.0');

-- =============================================================================
-- EXPERIENCE  (User A — 2 prior roles, Sprint 2)
-- =============================================================================
INSERT INTO experience (experience_id, user_id, company, title, start_date, end_date, description, sort_order) VALUES
    (1, 1,
     'TechStartup Inc.',
     'Software Engineering Intern',
     '2024-06-01', '2024-08-31',
     'Built REST APIs with FastAPI and PostgreSQL; improved query performance by 30% through index optimization.',
     0),
    (2, 1,
     'Campus IT Services',
     'Web Developer (Part-time)',
     '2023-01-15', '2024-05-31',
     'Maintained and extended the university portal using React and Django; led migration to AWS S3 for static assets.',
     1);

-- =============================================================================
-- SKILLS  (User A — Sprint 2)
-- =============================================================================
INSERT INTO skills (skill_id, user_id, name, category, proficiency, sort_order) VALUES
    (1, 1, 'Python',        'Programming Languages', 'Advanced',      0),
    (2, 1, 'React',         'Frontend',              'Intermediate',  1),
    (3, 1, 'PostgreSQL',    'Databases',             'Intermediate',  2),
    (4, 1, 'FastAPI',       'Frameworks',            'Intermediate',  3),
    (5, 1, 'Docker',        'DevOps',                'Beginner',      4),
    (6, 1, 'Git',           'Tools',                 'Advanced',      5),
    (7, 1, 'JavaScript',    'Programming Languages', 'Intermediate',  6),
    (8, 1, 'AWS S3',        'Cloud',                 'Beginner',      7);

-- =============================================================================
-- CAREER PREFERENCES  (User A — Sprint 2)
-- =============================================================================
INSERT INTO career_preferences (preference_id, user_id, target_roles, location_preferences, work_mode, salary_preference) VALUES
    (1, 1,
     'Software Engineer, Backend Engineer, Full Stack Engineer',
     'New York Metro Area, Remote',
     'Hybrid',
     '$120,000 – $150,000');

-- =============================================================================
-- COMPANIES
-- =============================================================================
INSERT INTO company (company_id, address_id, name) VALUES
    (1, 3, 'Google'),
    (2, 4, 'Microsoft'),
    (3, 5, 'Amazon'),
    (4, 6, 'Meta');

-- =============================================================================
-- RECRUITER  (Sarah Connor — Technical Recruiter at Google)
-- Password: Demo1234!  (same bcrypt hash as user accounts)
-- =============================================================================
INSERT INTO recruiter (recruiter_id, email, company_id, first_name, last_name, job_title) VALUES
    (1, 'recruiter@demo.com', 1, 'Sarah', 'Connor', 'Technical Recruiter');

INSERT INTO recruiter_credentials (credential_id, recruiter_id, hashed_password) VALUES
    (1, 1, '$2b$12$EY2gk/D84cdS16h89DIILucUTdjf.FGvnPTdm2dxQrvVJ0XdrZnxq');

-- =============================================================================
-- POSITIONS
-- =============================================================================
INSERT INTO "position" (position_id, company_id, title, listing_date, salary,
                        education_req, experience_req, description) VALUES
    (1, 1, 'Software Engineer',          '2026-01-10', 140000.00,
     'Bachelor''s in CS or related field', '2+ years',
     'Build and scale Google''s core infrastructure.'),
    (2, 2, 'Backend Engineer',           '2026-01-20', 135000.00,
     'Bachelor''s in CS',                 '1+ years',
     'Develop backend services for Microsoft Azure.'),
    (3, 3, 'Software Development Engineer', '2026-02-01', 145000.00,
     'Bachelor''s in CS or related field', '2+ years',
     'Work on Amazon''s e-commerce platform.'),
    (4, 4, 'Frontend Engineer',          '2026-02-10', 130000.00,
     'Bachelor''s in any discipline',      '1+ years React',
     'Build user-facing features for Meta''s social platforms.');

-- =============================================================================
-- APPLIED JOBS  (User A — 4 applications)
-- job_id 1 = Google  → Interview stage
-- job_id 2 = Microsoft → Applied stage
-- job_id 3 = Amazon  → Offer stage
-- job_id 4 = Meta    → Interested stage
--
-- Sprint 2 new columns: deadline, recruiter_notes, outcome_notes
-- =============================================================================
INSERT INTO applied_jobs (job_id, user_id, position_id, years_of_experience,
                          application_date, application_status, stage_changed_at,
                          deadline, recruiter_notes, outcome_notes) VALUES
    (1, 1, 1, 2, '2026-01-15', 'Interview',   '2026-02-01 09:00:00',
     '2026-04-30',
     'Strong LeetCode profile noted by recruiter. Bring system design examples.',
     NULL),
    (2, 1, 2, 2, '2026-01-22', 'Applied',     '2026-01-22 14:30:00',
     '2026-05-15',
     NULL,
     NULL),
    (3, 1, 3, 2, '2026-02-05', 'Offer',       '2026-03-10 11:00:00',
     NULL,
     'Hiring manager fast-tracked after phone screen.',
     'Offer received: $145k base + RSUs. Decision deadline 2026-04-15.'),
    (4, 1, 4, 2, '2026-02-12', 'Interested',  NULL,
     NULL,
     NULL,
     NULL);

-- =============================================================================
-- JOB ACTIVITY  (stage transition history for each application)
-- Sprint 2 new columns: event_type (default 'stage_change'), notes
-- =============================================================================

-- Google (job_id=1): Interested → Applied → Interview
INSERT INTO job_activity (activity_id, job_id, stage, changed_at, event_type, notes) VALUES
    (1,  1, 'Interested', '2026-01-15 10:00:00', 'stage_change', NULL),
    (2,  1, 'Applied',    '2026-01-16 08:30:00', 'stage_change', NULL),
    (3,  1, 'Interview',  '2026-02-01 09:00:00', 'stage_change', 'Recruiter reached out via LinkedIn to schedule phone screen.'),

-- Microsoft (job_id=2): Interested → Applied
    (4,  2, 'Interested', '2026-01-22 12:00:00', 'stage_change', NULL),
    (5,  2, 'Applied',    '2026-01-22 14:30:00', 'stage_change', NULL),

-- Amazon (job_id=3): Interested → Applied → Interview → Offer
    (6,  3, 'Interested', '2026-02-05 09:00:00', 'stage_change', NULL),
    (7,  3, 'Applied',    '2026-02-06 11:00:00', 'stage_change', NULL),
    (8,  3, 'Interview',  '2026-02-20 10:00:00', 'stage_change', NULL),
    (9,  3, 'Offer',      '2026-03-10 11:00:00', 'stage_change', 'Received verbal offer; written offer letter sent by email.'),

-- Meta (job_id=4): Interested only
    (10, 4, 'Interested', '2026-02-12 15:00:00', 'stage_change', NULL);

-- =============================================================================
-- DOCUMENTS  (User A — 3 docs; cover letter linked to Google job via job_id)
-- Sprint 2: job_id column nullable, cover letter linked to job_id=1
-- =============================================================================
INSERT INTO documents (doc_id, user_id, job_id, document_type, document_location) VALUES
    (1, 1, NULL, 'resume',       '/uploads/alex_resume_v1.pdf'),
    (2, 1, 1,    'cover_letter', '/uploads/alex_cover_google.pdf'),
    (3, 1, NULL, 'resume',       '/uploads/alex_resume_v2_backend.pdf');

-- =============================================================================
-- INTERVIEWS  (Google job — Sprint 2, S2-011)
-- =============================================================================
INSERT INTO interview (interview_id, job_id, round_type, scheduled_at, notes) VALUES
    (1, 1, 'Phone Screen',
     '2026-02-08 14:00:00',
     'Introductory call with recruiter. ~30 min. Discuss background and role fit.'),
    (2, 1, 'Technical — LeetCode',
     '2026-02-15 11:00:00',
     '60-minute coding round. Focus on arrays, hashmaps, and recursion.'),
    (3, 1, 'System Design',
     '2026-02-22 13:00:00',
     'Design a URL shortener or rate-limiter. Review HLD/LLD beforehand.');

-- =============================================================================
-- FOLLOW-UPS  (Microsoft job — Sprint 2, S2-012)
-- =============================================================================
INSERT INTO follow_up (followup_id, job_id, description, due_date, completed) VALUES
    (1, 2, 'Send thank-you email to recruiter after phone screen.',  '2026-02-01', TRUE),
    (2, 2, 'Follow up if no response received after 2 weeks.',       '2026-02-28', FALSE),
    (3, 2, 'Prepare answers for behavioral questions (STAR format).', NULL,        FALSE);

-- =============================================================================
-- RESET SEQUENCES so next auto-generated IDs continue from 100
-- (prevents collisions when new rows are inserted after seeding)
-- =============================================================================
SELECT setval(pg_get_serial_sequence('address',            'address_id'),    100);
SELECT setval(pg_get_serial_sequence('"user"',             'user_id'),        100);
SELECT setval(pg_get_serial_sequence('credentials',        'credential_id'), 100);
SELECT setval(pg_get_serial_sequence('profile',            'profile_id'),    100);
SELECT setval(pg_get_serial_sequence('education',          'education_id'),  100);
SELECT setval(pg_get_serial_sequence('experience',         'experience_id'), 100);
SELECT setval(pg_get_serial_sequence('skills',             'skill_id'),      100);
SELECT setval(pg_get_serial_sequence('career_preferences', 'preference_id'), 100);
SELECT setval(pg_get_serial_sequence('company',            'company_id'),    100);
SELECT setval(pg_get_serial_sequence('"position"',         'position_id'),   100);
SELECT setval(pg_get_serial_sequence('applied_jobs',       'job_id'),        100);
SELECT setval(pg_get_serial_sequence('job_activity',       'activity_id'),   100);
SELECT setval(pg_get_serial_sequence('documents',          'doc_id'),        100);
SELECT setval(pg_get_serial_sequence('interview',          'interview_id'),  100);
SELECT setval(pg_get_serial_sequence('follow_up',          'followup_id'),   100);
SELECT setval(pg_get_serial_sequence('recruiter',          'recruiter_id'),  100);
SELECT setval(pg_get_serial_sequence('recruiter_credentials', 'credential_id'), 100);

COMMIT;

-- =============================================================================
-- Demo Accounts
--   User A     — usera@demo.com      / Demo1234!  (full data)
--   User B     — userb@demo.com      / Demo1234!  (bare account — ownership checks)
--   Recruiter  — recruiter@demo.com  / Demo1234!  (Sarah Connor, Google)
-- =============================================================================
