-- =============================================================================
-- SPRINT 2 ADDITIVE SEED — safe to run on top of existing seed data
--
-- Does NOT delete or modify anything already in the database.
-- Uses ON CONFLICT DO NOTHING so re-running this file is also safe.
--
-- What this adds:
--   • 4 more companies  (Apple, Netflix, Stripe, Salesforce)
--   • 4 more positions  (one per company)
--   • 4 more jobs       (jobs 5-8 covering Rejected, Archived, Withdrawn, Interview)
--   • Job activity rows for all 4 new jobs
--   • Second education entry (Bergen Community College)
--   • 3 AI-generated job document drafts (job_document table)
--   • 3 outcome records for terminal-state jobs
--   • 1 additional interview (Salesforce job)
--   • 1 additional follow-up (Salesforce job)
--
-- HOW TO RUN (Supabase):
--   1. Go to your Supabase project → SQL Editor
--   2. Paste the entire contents of this file
--   3. Click Run
-- =============================================================================

BEGIN;

-- =============================================================================
-- NEW ADDRESSES
-- 7  = Apple      (Cupertino, CA)
-- 8  = Netflix    (Los Gatos, CA)
-- 9  = Stripe     (South San Francisco, CA)
-- 10 = Salesforce (San Francisco, CA)
-- 11 = Bergen Community College (Paramus, NJ) — second education entry
-- =============================================================================
INSERT INTO address (address_id, address, state, zip_code) VALUES
    (7,  'One Apple Park Way',  'CA', 95014),
    (8,  '100 Winchester Cir',  'CA', 95032),
    (9,  '354 Oyster Point Blvd', 'CA', 94080),
    (10, '415 Mission St',      'CA', 94105),
    (11, '400 Paramus Rd',      'NJ', 7652)
ON CONFLICT (address_id) DO NOTHING;

-- =============================================================================
-- NEW COMPANIES
-- =============================================================================
INSERT INTO company (company_id, address_id, name) VALUES
    (5, 7,  'Apple'),
    (6, 8,  'Netflix'),
    (7, 9,  'Stripe'),
    (8, 10, 'Salesforce')
ON CONFLICT (company_id) DO NOTHING;

-- =============================================================================
-- NEW POSITIONS
-- =============================================================================
INSERT INTO "position" (position_id, company_id, title, listing_date, salary,
                        education_req, experience_req, description) VALUES
    (5, 5, 'iOS Software Engineer',     '2026-01-05', 150000.00,
     'Bachelor''s in CS or related field', '2+ years',
     'Develop and maintain iOS features for Apple''s core apps.'),
    (6, 6, 'Senior Software Engineer',  '2025-12-10', 160000.00,
     'Bachelor''s in CS',               '3+ years',
     'Work on Netflix''s streaming infrastructure and recommendation systems.'),
    (7, 7, 'Platform Engineer',         '2026-01-18', 145000.00,
     'Bachelor''s in CS or related field', '2+ years',
     'Build Stripe''s payments infrastructure and developer tooling.'),
    (8, 8, 'Software Engineer',         '2026-02-15', 138000.00,
     'Bachelor''s in CS',               '1+ years',
     'Build CRM and cloud solutions on the Salesforce platform.')
ON CONFLICT (position_id) DO NOTHING;

-- =============================================================================
-- SECOND EDUCATION ENTRY  (Bergen Community College)
-- =============================================================================
INSERT INTO education (education_id, user_id, address_id, highest_education, degree,
                       school_or_college, field_of_study, start_date, end_date, gpa) VALUES
    (2, 1, 11,
     'Associate''s',
     'Computer Science',
     'Bergen Community College',
     'Computer Science',
     '2019-09-01',
     '2021-05-15',
     '3.9/4.0')
ON CONFLICT (education_id) DO NOTHING;

-- =============================================================================
-- 4 NEW APPLIED JOBS
-- job 5 = Apple      → Rejected
-- job 6 = Netflix    → Archived
-- job 7 = Stripe     → Withdrawn
-- job 8 = Salesforce → Interview
-- =============================================================================
INSERT INTO applied_jobs (job_id, user_id, position_id, years_of_experience,
                          application_date, application_status, stage_changed_at,
                          deadline, recruiter_notes, outcome_notes) VALUES
    (5, 1, 5, 2, '2026-01-06', 'Rejected',  '2026-02-10 16:00:00',
     '2026-03-01',
     'Recruiter: Kyle from Apple University Staffing.',
     'Did not advance past phone screen. Feedback: needed stronger systems knowledge.'),
    (6, 1, 6, 3, '2025-12-16', 'Archived',  '2026-01-20 10:00:00',
     NULL, NULL, NULL),
    (7, 1, 7, 2, '2026-01-26', 'Withdrawn', '2026-03-05 09:00:00',
     '2026-04-01',
     'Recruiter: Mia at Stripe. Very responsive throughout.',
     'Withdrew after accepting Amazon offer. Sent polite withdrawal email.'),
    (8, 1, 8, 1, '2026-02-19', 'Interview', '2026-03-01 13:00:00',
     '2026-05-01',
     'Recruiter: Dana Chen. Mentioned strong GitHub profile.',
     NULL)
ON CONFLICT (job_id) DO NOTHING;

-- =============================================================================
-- JOB ACTIVITY FOR NEW JOBS  (continues from activity_id 10)
-- =============================================================================
INSERT INTO job_activity (activity_id, job_id, stage, changed_at, event_type, notes) VALUES
    -- Apple (job 5): Interested → Applied → Rejected
    (11, 5, 'Interested', '2026-01-06 09:00:00', 'stage_change', NULL),
    (12, 5, 'Applied',    '2026-01-07 10:00:00', 'stage_change', NULL),
    (13, 5, 'Rejected',   '2026-02-10 16:00:00', 'stage_change', 'Automated rejection email received.'),

    -- Netflix (job 6): Interested → Applied → Archived
    (14, 6, 'Interested', '2025-12-16 11:00:00', 'stage_change', NULL),
    (15, 6, 'Applied',    '2025-12-17 09:00:00', 'stage_change', NULL),
    (16, 6, 'Archived',   '2026-01-20 10:00:00', 'stage_change', 'No response after 5 weeks. Archiving to keep dashboard clean.'),

    -- Stripe (job 7): Interested → Applied → Withdrawn
    (17, 7, 'Interested', '2026-01-26 08:00:00', 'stage_change', NULL),
    (18, 7, 'Applied',    '2026-01-27 09:30:00', 'stage_change', NULL),
    (19, 7, 'Withdrawn',  '2026-03-05 09:00:00', 'stage_change', 'Withdrew after accepting Amazon offer.'),

    -- Salesforce (job 8): Interested → Applied → Interview
    (20, 8, 'Interested', '2026-02-19 10:00:00', 'stage_change', NULL),
    (21, 8, 'Applied',    '2026-02-20 08:00:00', 'stage_change', NULL),
    (22, 8, 'Interview',  '2026-03-01 13:00:00', 'stage_change', 'Phone screen scheduled with Dana Chen.')
ON CONFLICT (activity_id) DO NOTHING;

-- =============================================================================
-- AI-GENERATED JOB DOCUMENTS  (job_document table — was empty before this)
-- Linked to Google (job 1) and Salesforce (job 8)
-- =============================================================================
INSERT INTO job_document (job_document_id, job_id, title, content, created_at, updated_at) VALUES
    (1, 1,
     'AI Resume Draft — Google Software Engineer',
     'Alex Johnson | usera@demo.com | 201-555-0101

SUMMARY
Computer Science senior with hands-on experience in Python, FastAPI, and PostgreSQL. Built production REST APIs and led frontend migrations. Seeking software engineering roles at scale.

EXPERIENCE
Software Engineering Intern — TechStartup Inc. (Jun 2024 – Aug 2024)
• Built and documented REST APIs using FastAPI and PostgreSQL
• Improved query performance by 30% through index optimization
• Collaborated with senior engineers in agile sprints

Web Developer (Part-time) — Campus IT Services (Jan 2023 – May 2024)
• Maintained React/Django university portal used by 10,000+ students
• Led migration of static assets to AWS S3, reducing load times by 40%

EDUCATION
B.S. Computer Science — New Jersey Institute of Technology (2021–2025) | GPA 3.7

SKILLS
Python • FastAPI • React • PostgreSQL • Docker • Git • JavaScript • AWS S3',
     '2026-02-10 15:30:00',
     '2026-02-10 15:45:00'),

    (2, 1,
     'AI Cover Letter Draft — Google Software Engineer',
     'Dear Google Hiring Team,

I am excited to apply for the Software Engineer role at Google. As a Computer Science senior at NJIT with experience building scalable REST APIs and optimizing database performance, I am confident I can contribute meaningfully to Google''s core infrastructure team.

During my internship at TechStartup Inc., I built production-grade FastAPI services and improved query performance by 30% through strategic indexing — the kind of hands-on backend work I am eager to continue at scale. My part-time role at Campus IT Services taught me how to ship reliable software iteratively while supporting a real user base of 10,000+ students.

I am particularly drawn to Google''s emphasis on technical rigor and impact at scale. I would welcome the opportunity to discuss how my background aligns with your team''s needs.

Thank you for your consideration,
Alex Johnson',
     '2026-02-10 15:50:00',
     '2026-02-10 16:00:00'),

    (3, 8,
     'AI Resume Draft — Salesforce Software Engineer',
     'Alex Johnson | usera@demo.com | 201-555-0101

SUMMARY
Motivated CS graduate with backend and frontend experience seeking a software engineering role. Strong foundation in Python, React, and cloud tooling with a track record of shipping production features.

EXPERIENCE
Software Engineering Intern — TechStartup Inc. (Jun 2024 – Aug 2024)
• Designed and built REST APIs powering mobile and web clients
• Reduced average API response time by 25% through query tuning

Web Developer (Part-time) — Campus IT Services (Jan 2023 – May 2024)
• Built new student-facing features in React and Django
• Automated deployment pipeline, cutting release time from 2 hours to 20 minutes

EDUCATION
B.S. Computer Science — NJIT (2021–2025) | GPA 3.7
A.S. Computer Science — Bergen Community College (2019–2021) | GPA 3.9

SKILLS
Python • FastAPI • React • PostgreSQL • Docker • Git • JavaScript • AWS S3',
     '2026-03-02 10:00:00',
     '2026-03-02 10:15:00')
ON CONFLICT (job_document_id) DO NOTHING;

-- =============================================================================
-- OUTCOMES  (terminal-state jobs — outcome table was empty before this)
-- =============================================================================
INSERT INTO outcome (outcome_id, job_id, outcome_state, outcome_notes) VALUES
    (1, 3, 'Offer',     'Offer received: $145k base + RSUs. Accepted 2026-04-10.'),
    (2, 5, 'Rejected',  'Did not advance past phone screen. Feedback: needed stronger systems design knowledge.'),
    (3, 7, 'Withdrawn', 'Withdrew politely after accepting Amazon offer. Left door open for future roles.')
ON CONFLICT (outcome_id) DO NOTHING;

-- =============================================================================
-- ADDITIONAL INTERVIEW  (Salesforce job 8 — continues from interview_id 3)
-- =============================================================================
INSERT INTO interview (interview_id, job_id, round_type, scheduled_at, notes) VALUES
    (4, 8, 'Phone Screen',
     '2026-03-05 14:00:00',
     'First call with Dana Chen. ~45 min. Review resume and discuss Salesforce platform experience.')
ON CONFLICT (interview_id) DO NOTHING;

-- =============================================================================
-- ADDITIONAL FOLLOW-UP  (Salesforce job 8 — continues from followup_id 3)
-- =============================================================================
INSERT INTO follow_up (followup_id, job_id, description, due_date, completed) VALUES
    (4, 8, 'Research Salesforce platform and Apex basics before phone screen.', '2026-03-04', FALSE)
ON CONFLICT (followup_id) DO NOTHING;

-- =============================================================================
-- UPDATE SEQUENCES to prevent ID collisions going forward
-- =============================================================================
SELECT setval(pg_get_serial_sequence('address',            'address_id'),       100);
SELECT setval(pg_get_serial_sequence('company',            'company_id'),       100);
SELECT setval(pg_get_serial_sequence('"position"',         'position_id'),      100);
SELECT setval(pg_get_serial_sequence('education',          'education_id'),     100);
SELECT setval(pg_get_serial_sequence('applied_jobs',       'job_id'),           100);
SELECT setval(pg_get_serial_sequence('job_activity',       'activity_id'),      100);
SELECT setval(pg_get_serial_sequence('job_document',       'job_document_id'),  100);
SELECT setval(pg_get_serial_sequence('outcome',            'outcome_id'),       100);
SELECT setval(pg_get_serial_sequence('interview',          'interview_id'),     100);
SELECT setval(pg_get_serial_sequence('follow_up',          'followup_id'),      100);

COMMIT;

-- =============================================================================
-- After running this you will have:
--   8 jobs spanning: Interested, Applied, Interview (x2), Offer, Rejected, Archived, Withdrawn
--   2 education entries
--   2 experience entries
--   8 skills
--   3 AI-generated job document drafts
--   3 outcome records
--   4 interviews
--   4 follow-ups
-- =============================================================================
