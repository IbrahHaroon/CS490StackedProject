-- =============================================================================
-- SCHEMA RECREATION SCRIPT
-- Drops all tables and recreates them from scratch.
-- Run this to reset a database to a clean state.
-- WARNING: This will permanently delete all data.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Drop tables (reverse FK order)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS token_blacklist CASCADE;
DROP TABLE IF EXISTS interview CASCADE;
DROP TABLE IF EXISTS follow_up CASCADE;
DROP TABLE IF EXISTS job_activity CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS applied_jobs CASCADE;
DROP TABLE IF EXISTS education CASCADE;
DROP TABLE IF EXISTS password_reset_token CASCADE;
DROP TABLE IF EXISTS profile CASCADE;
DROP TABLE IF EXISTS credentials CASCADE;
DROP TABLE IF EXISTS experience CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS career_preferences CASCADE;
DROP TABLE IF EXISTS "position" CASCADE;
DROP TABLE IF EXISTS recruiter_password_reset_token CASCADE;
DROP TABLE IF EXISTS recruiter_credentials CASCADE;
DROP TABLE IF EXISTS recruiter CASCADE;
DROP TABLE IF EXISTS company CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;
DROP TABLE IF EXISTS address CASCADE;

-- -----------------------------------------------------------------------------
-- address
-- (no FKs — root table)
-- -----------------------------------------------------------------------------
CREATE TABLE address (
    address_id  SERIAL PRIMARY KEY,
    address     VARCHAR(255) NOT NULL,
    state       VARCHAR(100) NOT NULL,
    zip_code    INTEGER      NOT NULL
);

-- -----------------------------------------------------------------------------
-- user
-- (no FKs — root table)
-- -----------------------------------------------------------------------------
CREATE TABLE "user" (
    user_id  SERIAL PRIMARY KEY,
    email    VARCHAR(255) NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- credentials
-- ON DELETE CASCADE: credentials are owned by the user; delete user → delete credentials
-- -----------------------------------------------------------------------------
CREATE TABLE credentials (
    credential_id   SERIAL PRIMARY KEY,
    user_id         INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    hashed_password VARCHAR(255) NOT NULL
);

-- -----------------------------------------------------------------------------
-- profile
-- user_id   ON DELETE CASCADE:  profile is owned by the user
-- address_id ON DELETE RESTRICT: prevent deleting an address still linked to a profile
-- -----------------------------------------------------------------------------
CREATE TABLE profile (
    profile_id   SERIAL PRIMARY KEY,
    user_id      INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    address_id   INTEGER      NOT NULL REFERENCES address(address_id) ON DELETE RESTRICT,
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    dob          DATE         NOT NULL,
    phone_number VARCHAR(20),
    summary      VARCHAR(1000)
);

-- -----------------------------------------------------------------------------
-- company
-- address_id ON DELETE RESTRICT: prevent deleting an address still linked to a company
-- -----------------------------------------------------------------------------
CREATE TABLE company (
    company_id  SERIAL PRIMARY KEY,
    address_id  INTEGER      NOT NULL REFERENCES address(address_id) ON DELETE RESTRICT,
    name        VARCHAR(255) NOT NULL
);

-- -----------------------------------------------------------------------------
-- recruiter
-- company_id ON DELETE RESTRICT: recruiter belongs to a company
-- (no user_id FK — recruiters have their own auth, separate from users)
-- -----------------------------------------------------------------------------
CREATE TABLE recruiter (
    recruiter_id  SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    company_id    INTEGER      NOT NULL REFERENCES company(company_id) ON DELETE RESTRICT,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    job_title     VARCHAR(100)
);

-- -----------------------------------------------------------------------------
-- recruiter_credentials
-- ON DELETE CASCADE: credentials are owned by the recruiter
-- -----------------------------------------------------------------------------
CREATE TABLE recruiter_credentials (
    credential_id   SERIAL PRIMARY KEY,
    recruiter_id    INTEGER      NOT NULL UNIQUE REFERENCES recruiter(recruiter_id) ON DELETE CASCADE,
    hashed_password VARCHAR(255) NOT NULL
);

-- -----------------------------------------------------------------------------
-- recruiter_password_reset_token
-- ON DELETE CASCADE: tokens are owned by the recruiter
-- -----------------------------------------------------------------------------
CREATE TABLE recruiter_password_reset_token (
    token_id     SERIAL PRIMARY KEY,
    recruiter_id INTEGER      NOT NULL REFERENCES recruiter(recruiter_id) ON DELETE CASCADE,
    token_hash   VARCHAR(255) NOT NULL UNIQUE,
    expires_at   TIMESTAMPTZ  NOT NULL,
    used         BOOLEAN      NOT NULL DEFAULT FALSE
);

-- -----------------------------------------------------------------------------
-- position
-- company_id ON DELETE RESTRICT: prevent deleting a company that still has positions listed
-- -----------------------------------------------------------------------------
CREATE TABLE "position" (
    position_id    SERIAL PRIMARY KEY,
    company_id     INTEGER       NOT NULL REFERENCES company(company_id) ON DELETE RESTRICT,
    title          VARCHAR(255)  NOT NULL,
    listing_date   DATE          NOT NULL,
    location_type  VARCHAR(20),
    location       VARCHAR(255),
    salary         NUMERIC(10,2),
    education_req  VARCHAR(255),
    experience_req VARCHAR(255),
    description    VARCHAR(2000)
);

-- -----------------------------------------------------------------------------
-- education
-- user_id    ON DELETE CASCADE:  education records are owned by the user
-- address_id ON DELETE RESTRICT: prevent deleting an address still linked to an education record
-- -----------------------------------------------------------------------------
CREATE TABLE education (
    education_id      SERIAL PRIMARY KEY,
    user_id           INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    address_id        INTEGER      NOT NULL REFERENCES address(address_id) ON DELETE RESTRICT,
    highest_education VARCHAR(100) NOT NULL,
    degree            VARCHAR(100) NOT NULL,
    school_or_college VARCHAR(255) NOT NULL,
    field_of_study    VARCHAR(100),
    start_date        DATE,
    end_date          DATE,
    gpa               VARCHAR(10)
);

-- -----------------------------------------------------------------------------
-- experience
-- user_id ON DELETE CASCADE: experience records are owned by the user
-- -----------------------------------------------------------------------------
CREATE TABLE experience (
    experience_id  SERIAL PRIMARY KEY,
    user_id        INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    company        VARCHAR(255) NOT NULL,
    title          VARCHAR(255) NOT NULL,
    start_date     DATE         NOT NULL,
    end_date       DATE,
    description    VARCHAR(2000),
    sort_order     INTEGER      NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- skills
-- user_id ON DELETE CASCADE: skills are owned by the user
-- -----------------------------------------------------------------------------
CREATE TABLE skills (
    skill_id    SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(100),
    proficiency VARCHAR(50),
    sort_order  INTEGER      NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- career_preferences
-- user_id ON DELETE CASCADE: preferences are owned by the user (1:1)
-- -----------------------------------------------------------------------------
CREATE TABLE career_preferences (
    preference_id        SERIAL PRIMARY KEY,
    user_id              INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    target_roles         VARCHAR(500),
    location_preferences VARCHAR(500),
    work_mode            VARCHAR(50),
    salary_preference    VARCHAR(100)
);

-- -----------------------------------------------------------------------------
-- applied_jobs
-- user_id     ON DELETE CASCADE:  applications are owned by the user
-- position_id ON DELETE RESTRICT: prevent deleting a position that has active applications
-- -----------------------------------------------------------------------------
CREATE TABLE applied_jobs (
    job_id               SERIAL PRIMARY KEY,
    user_id              INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    position_id          INTEGER      NOT NULL REFERENCES "position"(position_id) ON DELETE RESTRICT,
    years_of_experience  INTEGER      NOT NULL,
    application_date     DATE         NOT NULL,
    application_status   VARCHAR(50)  NOT NULL DEFAULT 'Interested',
    stage_changed_at     TIMESTAMP,
    deadline             DATE,
    recruiter_notes      VARCHAR(1000),
    outcome_notes        VARCHAR(1000)
);

-- -----------------------------------------------------------------------------
-- documents
-- user_id ON DELETE CASCADE:   documents are owned by the user
-- job_id  ON DELETE SET NULL:  nullable — document can exist without a job context;
--                              if the linked job is deleted the doc is preserved but unlinked
-- -----------------------------------------------------------------------------
CREATE TABLE documents (
    doc_id            SERIAL PRIMARY KEY,
    user_id           INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    job_id            INTEGER      NULL     REFERENCES applied_jobs(job_id) ON DELETE SET NULL,
    document_type     VARCHAR(100) NOT NULL,
    document_location VARCHAR(500)
);

-- -----------------------------------------------------------------------------
-- job_activity
-- job_id ON DELETE CASCADE: activity history is owned by the job
-- -----------------------------------------------------------------------------
CREATE TABLE job_activity (
    activity_id  SERIAL PRIMARY KEY,
    job_id       INTEGER      NOT NULL REFERENCES applied_jobs(job_id) ON DELETE CASCADE,
    stage        VARCHAR(50)  NOT NULL,
    changed_at   TIMESTAMP    NOT NULL,
    event_type   VARCHAR(50)  NOT NULL DEFAULT 'stage_change',
    notes        VARCHAR(1000)
);

-- -----------------------------------------------------------------------------
-- interview
-- job_id ON DELETE CASCADE: interviews are owned by the job
-- -----------------------------------------------------------------------------
CREATE TABLE interview (
    interview_id  SERIAL PRIMARY KEY,
    job_id        INTEGER      NOT NULL REFERENCES applied_jobs(job_id) ON DELETE CASCADE,
    round_type    VARCHAR(100) NOT NULL,
    scheduled_at  TIMESTAMP    NOT NULL,
    notes         VARCHAR(2000)
);

-- -----------------------------------------------------------------------------
-- follow_up
-- job_id ON DELETE CASCADE: follow-ups are owned by the job
-- -----------------------------------------------------------------------------
CREATE TABLE follow_up (
    followup_id  SERIAL PRIMARY KEY,
    job_id       INTEGER      NOT NULL REFERENCES applied_jobs(job_id) ON DELETE CASCADE,
    description  VARCHAR(500) NOT NULL,
    due_date     DATE,
    completed    BOOLEAN      NOT NULL DEFAULT FALSE
);

-- -----------------------------------------------------------------------------
-- password_reset_token
-- user_id ON DELETE CASCADE: tokens are owned by the user
-- -----------------------------------------------------------------------------
CREATE TABLE password_reset_token (
    token_id    SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ  NOT NULL,
    used        BOOLEAN      NOT NULL
);

-- -----------------------------------------------------------------------------
-- token_blacklist
-- (no FKs — stores revoked JWT IDs independently of user records)
-- -----------------------------------------------------------------------------
CREATE TABLE token_blacklist (
    id         SERIAL PRIMARY KEY,
    jti        VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ  NOT NULL
);

COMMIT;
