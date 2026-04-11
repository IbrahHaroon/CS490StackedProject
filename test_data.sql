-- =============================================================================
-- TEST DATA — safe to run against a dev/staging org, NOT production
-- Passwords:  user1@test.com  → test1234
--             user2@test.com  → password123
-- Wipe all test rows first so the script is re-runnable.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Clean up (reverse FK order)
-- -----------------------------------------------------------------------------
DELETE FROM job_activity;
DELETE FROM applied_jobs;
DELETE FROM documents;
DELETE FROM education;
DELETE FROM profile;
DELETE FROM credentials;
DELETE FROM "user";
DELETE FROM position;
DELETE FROM company;
DELETE FROM address;

-- -----------------------------------------------------------------------------
-- Addresses
-- -----------------------------------------------------------------------------
INSERT INTO address (address_id, address, state, zip_code) VALUES
  (1, '123 Main St',      'NY', 10001),
  (2, '456 Oak Ave',      'CA', 90210),
  (3, '789 Tech Blvd',    'TX', 73301),
  (4, '321 College Rd',   'MA', 02101),
  (5, '100 University Dr','FL', 32601);

-- -----------------------------------------------------------------------------
-- Users
-- -----------------------------------------------------------------------------
INSERT INTO "user" (user_id, email) VALUES
  (1, 'user1@test.com'),
  (2, 'user2@test.com');

-- -----------------------------------------------------------------------------
-- Credentials  (hashed passwords)
-- user1@test.com  → test1234
-- user2@test.com  → password123
-- -----------------------------------------------------------------------------
INSERT INTO credentials (credential_id, user_id, hashed_password) VALUES
  (1, 1, '$2b$12$mupvTKncFBPVLP0T1UaKduIBvltM5SnKHNqkx86BIazBh5cjjJGNm'),
  (2, 2, '$2b$12$uY/gbQv5HEhVPoZRd/MKuO98BChFN8CAdxzhaz2ULpC1hap1UyW52');

-- -----------------------------------------------------------------------------
-- Profiles
-- -----------------------------------------------------------------------------
INSERT INTO profile (profile_id, user_id, address_id, first_name, last_name, dob, phone_number, summary) VALUES
  (1, 1, 1, 'Jane', 'Doe',   '1998-04-15', '555-0101', 'Computer Science student seeking internship opportunities.'),
  (2, 2, 2, 'John', 'Smith', '1997-09-22', '555-0202', 'Full-stack developer with 2 years of experience.');

-- -----------------------------------------------------------------------------
-- Companies
-- -----------------------------------------------------------------------------
INSERT INTO company (company_id, address_id, name) VALUES
  (1, 3, 'Acme Corp'),
  (2, 4, 'Tech Startup Inc');

-- -----------------------------------------------------------------------------
-- Positions
-- -----------------------------------------------------------------------------
INSERT INTO position (position_id, company_id, title, listing_date, salary, education_req, experience_req, description) VALUES
  (1, 1, 'Software Engineer Intern', '2026-01-10', 25.00,  'Bachelor''s in CS or related', 'No experience required',    'Join our engineering team for a summer internship building scalable web services.'),
  (2, 1, 'Junior Backend Developer',  '2026-02-01', 75000.00, 'Bachelor''s in CS',           '1+ years Python/FastAPI',    'Help build and maintain our REST API platform.'),
  (3, 2, 'Frontend Developer',        '2026-03-05', 85000.00, 'Bachelor''s in CS or Design', '2+ years React experience',  'Own the frontend of our SaaS product using React and TypeScript.');

-- -----------------------------------------------------------------------------
-- Education
-- -----------------------------------------------------------------------------
INSERT INTO education (education_id, user_id, address_id, highest_education, degree, school_or_college) VALUES
  (1, 1, 5, 'Bachelor''s', 'B.S. Computer Science',      'State University'),
  (2, 2, 4, 'Bachelor''s', 'B.S. Software Engineering',  'Tech Institute');

-- -----------------------------------------------------------------------------
-- Documents  (paths follow the upload convention: L/F/Full Name/user_id/filename)
-- -----------------------------------------------------------------------------
INSERT INTO documents (doc_id, user_id, document_type, document_location) VALUES
  (1, 1, 'Resume',       'uploads/D/J/Jane Doe/1/resume.pdf'),
  (2, 1, 'Cover Letter', 'uploads/D/J/Jane Doe/1/cover_letter.pdf'),
  (3, 2, 'Resume',       'uploads/S/J/John Smith/2/resume.pdf');

-- -----------------------------------------------------------------------------
-- Applied Jobs
-- -----------------------------------------------------------------------------
INSERT INTO applied_jobs (job_id, user_id, position_id, years_of_experience, application_date, application_status, stage_changed_at) VALUES
  (1, 1, 1, 0, '2026-03-01', 'Applied',    '2026-03-01 09:00:00'),
  (2, 1, 2, 1, '2026-03-10', 'Interviewing', '2026-03-12 14:30:00'),
  (3, 2, 3, 2, '2026-03-15', 'Applied',    '2026-03-15 11:00:00');

-- -----------------------------------------------------------------------------
-- Job Activity
-- -----------------------------------------------------------------------------
INSERT INTO job_activity (activity_id, job_id, stage, changed_at) VALUES
  (1, 1, 'Applied',      '2026-03-01 09:00:00'),
  (2, 2, 'Applied',      '2026-03-10 10:00:00'),
  (3, 2, 'Interviewing', '2026-03-12 14:30:00'),
  (4, 3, 'Applied',      '2026-03-15 11:00:00');

-- -----------------------------------------------------------------------------
-- Bump sequences so new inserts don't collide with test data IDs
-- -----------------------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('"user"',    'user_id'),       100);
SELECT setval(pg_get_serial_sequence('address',   'address_id'),    100);
SELECT setval(pg_get_serial_sequence('credentials','credential_id'),100);
SELECT setval(pg_get_serial_sequence('profile',   'profile_id'),    100);
SELECT setval(pg_get_serial_sequence('company',   'company_id'),    100);
SELECT setval(pg_get_serial_sequence('position',  'position_id'),   100);
SELECT setval(pg_get_serial_sequence('education', 'education_id'),  100);
SELECT setval(pg_get_serial_sequence('documents', 'doc_id'),        100);
SELECT setval(pg_get_serial_sequence('applied_jobs','job_id'),      100);
SELECT setval(pg_get_serial_sequence('job_activity','activity_id'), 100);

COMMIT;
