-- =============================================================================
-- SCHEMA V2 — Candidate-Facing Redesign
-- Aligns the database with PURPOSE.md: single-user job-search workspace,
-- no recruiter/company/position entities, no shared catalog.
--
-- This file REPLACES scripts/schema.sql once the migration is approved.
-- For an in-place migration of an existing database, run scripts/migrate_v1_to_v2.sql.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Drop everything (reverse FK order)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS token_blacklist CASCADE;
DROP TABLE IF EXISTS job_document_link CASCADE;
DROP TABLE IF EXISTS document_job_link CASCADE;       -- legacy name
DROP TABLE IF EXISTS document_tag CASCADE;
DROP TABLE IF EXISTS document_version CASCADE;
DROP TABLE IF EXISTS document CASCADE;
DROP TABLE IF EXISTS documents CASCADE;               -- legacy name
DROP TABLE IF EXISTS interview CASCADE;
DROP TABLE IF EXISTS follow_up CASCADE;
DROP TABLE IF EXISTS outcome CASCADE;                 -- folded into job.outcome_notes/stage in v2
DROP TABLE IF EXISTS job_document CASCADE;            -- folded into document + document_version + job_document_link in v2
DROP TABLE IF EXISTS job_activity CASCADE;
DROP TABLE IF EXISTS job CASCADE;
DROP TABLE IF EXISTS applied_jobs CASCADE;            -- legacy name
DROP TABLE IF EXISTS education CASCADE;
DROP TABLE IF EXISTS password_reset_token CASCADE;
DROP TABLE IF EXISTS profile CASCADE;
DROP TABLE IF EXISTS credentials CASCADE;
DROP TABLE IF EXISTS experience CASCADE;
DROP TABLE IF EXISTS skill CASCADE;
DROP TABLE IF EXISTS skills CASCADE;                  -- legacy name
DROP TABLE IF EXISTS career_preferences CASCADE;
DROP TABLE IF EXISTS "position" CASCADE;              -- removed entity
DROP TABLE IF EXISTS recruiter_password_reset_token CASCADE;
DROP TABLE IF EXISTS recruiter_credentials CASCADE;
DROP TABLE IF EXISTS recruiter CASCADE;               -- removed entity
DROP TABLE IF EXISTS company CASCADE;                 -- removed entity
DROP TABLE IF EXISTS "user" CASCADE;
DROP TABLE IF EXISTS address CASCADE;                 -- denormalized into profile/education/experience

-- -----------------------------------------------------------------------------
-- user
-- -----------------------------------------------------------------------------
CREATE TABLE "user" (
    user_id  SERIAL PRIMARY KEY,
    email    VARCHAR(255) NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- credentials
-- -----------------------------------------------------------------------------
CREATE TABLE credentials (
    credential_id   SERIAL PRIMARY KEY,
    user_id         INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    hashed_password VARCHAR(255) NOT NULL
);

-- -----------------------------------------------------------------------------
-- password_reset_token
-- -----------------------------------------------------------------------------
CREATE TABLE password_reset_token (
    token_id    SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ  NOT NULL,
    used        BOOLEAN      NOT NULL DEFAULT FALSE
);

-- -----------------------------------------------------------------------------
-- token_blacklist
-- -----------------------------------------------------------------------------
CREATE TABLE token_blacklist (
    id         SERIAL PRIMARY KEY,
    jti        VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ  NOT NULL
);

-- -----------------------------------------------------------------------------
-- profile  (address denormalized inline)
-- -----------------------------------------------------------------------------
CREATE TABLE profile (
    profile_id   SERIAL PRIMARY KEY,
    user_id      INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    dob          DATE         NOT NULL,
    phone_number VARCHAR(20),
    summary      VARCHAR(1000),
    address_line VARCHAR(255),
    city         VARCHAR(100),
    state        VARCHAR(100),
    zip_code     VARCHAR(20),
    country      VARCHAR(100)
);

-- -----------------------------------------------------------------------------
-- education
-- -----------------------------------------------------------------------------
CREATE TABLE education (
    education_id      SERIAL PRIMARY KEY,
    user_id           INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    school            VARCHAR(255) NOT NULL,
    degree            VARCHAR(100) NOT NULL,
    field_of_study    VARCHAR(100),
    start_date        DATE,
    end_date          DATE,
    gpa               VARCHAR(10),
    school_location   VARCHAR(255),
    sort_order        INTEGER      NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- experience
-- -----------------------------------------------------------------------------
CREATE TABLE experience (
    experience_id  SERIAL PRIMARY KEY,
    user_id        INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    company        VARCHAR(255) NOT NULL,
    title          VARCHAR(255) NOT NULL,
    location       VARCHAR(255),
    start_date     DATE         NOT NULL,
    end_date       DATE,
    description    VARCHAR(2000),
    sort_order     INTEGER      NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- skill  (renamed from "skills" for naming consistency)
-- -----------------------------------------------------------------------------
CREATE TABLE skill (
    skill_id    SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(100),
    proficiency VARCHAR(50),
    sort_order  INTEGER      NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- career_preferences
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
-- job  (replaces applied_jobs; absorbs position+company as plain columns)
-- application_date is NULLABLE — Interested-stage jobs are not yet applied
-- -----------------------------------------------------------------------------
CREATE TABLE job (
    job_id                  SERIAL PRIMARY KEY,
    user_id                 INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    title                   VARCHAR(255) NOT NULL,
    company_name            VARCHAR(255) NOT NULL,
    location                VARCHAR(255),
    source_url              VARCHAR(1000),
    description             TEXT,
    stage                   VARCHAR(50)  NOT NULL DEFAULT 'Interested',
    stage_changed_at        TIMESTAMP,
    application_date        DATE,
    deadline                DATE,
    priority                VARCHAR(20),
    salary                  NUMERIC(10,2),
    years_of_experience     INTEGER,
    notes                   TEXT,
    company_research_notes  TEXT,        -- S3-012: AI-assisted company research, editable
    outcome_notes           TEXT,
    created_at              TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_at             TIMESTAMP
);
CREATE INDEX idx_job_user_stage ON job(user_id, stage);

-- -----------------------------------------------------------------------------
-- job_activity  (now records transitions, not snapshots)
-- -----------------------------------------------------------------------------
CREATE TABLE job_activity (
    activity_id  SERIAL PRIMARY KEY,
    job_id       INTEGER      NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
    event_type   VARCHAR(50)  NOT NULL DEFAULT 'stage_change',
    from_stage   VARCHAR(50),
    to_stage     VARCHAR(50),
    notes        VARCHAR(1000),
    occurred_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_job_activity_job ON job_activity(job_id, occurred_at DESC);

-- -----------------------------------------------------------------------------
-- interview
-- -----------------------------------------------------------------------------
CREATE TABLE interview (
    interview_id  SERIAL PRIMARY KEY,
    job_id        INTEGER      NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
    round_type    VARCHAR(100) NOT NULL,
    scheduled_at  TIMESTAMP    NOT NULL,
    interviewer   VARCHAR(255),
    mode          VARCHAR(50),
    prep_notes    TEXT,        -- S3-013: pre-interview preparation, distinct from post-hoc notes
    notes         VARCHAR(2000)
);

-- -----------------------------------------------------------------------------
-- follow_up
-- -----------------------------------------------------------------------------
CREATE TABLE follow_up (
    followup_id  SERIAL PRIMARY KEY,
    job_id       INTEGER      NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
    description  VARCHAR(500) NOT NULL,
    due_date     DATE,
    completed    BOOLEAN      NOT NULL DEFAULT FALSE
);

-- -----------------------------------------------------------------------------
-- document  (parent record; current_version_id added after document_version)
-- -----------------------------------------------------------------------------
CREATE TABLE document (
    document_id        SERIAL PRIMARY KEY,
    user_id            INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    title              VARCHAR(255) NOT NULL,
    document_type      VARCHAR(100) NOT NULL,
    status             VARCHAR(50)  NOT NULL DEFAULT 'Draft',  -- S3-002/006: lifecycle state, distinct from is_deleted
    current_version_id INTEGER,
    is_deleted         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP   -- S3-006: sortable "updated date"
);

-- -----------------------------------------------------------------------------
-- document_version
-- -----------------------------------------------------------------------------
CREATE TABLE document_version (
    version_id        SERIAL PRIMARY KEY,
    document_id       INTEGER      NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    version_number    INTEGER      NOT NULL,
    storage_location  VARCHAR(500),
    content           TEXT,
    source            VARCHAR(50),
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (document_id, version_number)
);

ALTER TABLE document
    ADD CONSTRAINT document_current_version_fk
    FOREIGN KEY (current_version_id) REFERENCES document_version(version_id) ON DELETE SET NULL;

-- -----------------------------------------------------------------------------
-- document_tag  (one tag per row; supports multi-tag without serialization)
-- -----------------------------------------------------------------------------
CREATE TABLE document_tag (
    tag_id       SERIAL PRIMARY KEY,
    document_id  INTEGER      NOT NULL REFERENCES document(document_id) ON DELETE CASCADE,
    label        VARCHAR(100) NOT NULL,
    UNIQUE (document_id, label)
);

-- -----------------------------------------------------------------------------
-- job_document_link  (N:N between jobs and document VERSIONS — not docs)
-- role: 'resume' | 'cover_letter' | other context
-- -----------------------------------------------------------------------------
CREATE TABLE job_document_link (
    link_id     SERIAL PRIMARY KEY,
    job_id      INTEGER     NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
    version_id  INTEGER     NOT NULL REFERENCES document_version(version_id) ON DELETE CASCADE,
    role        VARCHAR(50),
    linked_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, version_id, role)
);

COMMIT;
