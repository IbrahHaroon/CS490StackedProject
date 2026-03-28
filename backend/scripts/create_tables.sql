-- =============================================================================
-- create_tables.sql
-- ATS (Applicant Tracking System) — PostgreSQL schema setup
--
-- Usage:
--   psql -U <user> -d <database> -f create_tables.sql
--
-- Tables are created in FK dependency order:
--   address → user → credentials
--              ├─→ profile     (FK: user, address)
--              ├─→ education   (FK: user, address)
--              ├─→ documents   (FK: user)
--              └─→ applied_jobs (FK: user, position)
--   company → position → applied_jobs
-- =============================================================================

-- ---------------------------------------------------------------------------
-- address
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS address (
    address_id  SERIAL PRIMARY KEY,
    address     VARCHAR(255) NOT NULL,
    state       VARCHAR(100) NOT NULL,
    zip_code    INTEGER      NOT NULL
);

-- ---------------------------------------------------------------------------
-- "user"  (quoted because USER is a reserved word in PostgreSQL)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "user" (
    user_id  SERIAL PRIMARY KEY,
    email    VARCHAR(255) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- credentials
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS credentials (
    credential_id   SERIAL PRIMARY KEY,
    user_id         INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    hashed_password VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------------
-- profile
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profile (
    profile_id   SERIAL PRIMARY KEY,
    user_id      INTEGER      NOT NULL UNIQUE REFERENCES "user"(user_id) ON DELETE CASCADE,
    address_id   INTEGER      NOT NULL REFERENCES address(address_id),
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    dob          DATE         NOT NULL,
    phone_number VARCHAR(20),
    summary      VARCHAR(1000)
);

-- ---------------------------------------------------------------------------
-- education
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS education (
    education_id      SERIAL PRIMARY KEY,
    user_id           INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    address_id        INTEGER      NOT NULL REFERENCES address(address_id),
    highest_education VARCHAR(100) NOT NULL,
    degree            VARCHAR(100) NOT NULL,
    school_or_college VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------------
-- documents
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    doc_id            SERIAL PRIMARY KEY,
    user_id           INTEGER      NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    document_type     VARCHAR(100) NOT NULL,
    document_location VARCHAR(500) NOT NULL
);

-- ---------------------------------------------------------------------------
-- company
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company (
    company_id SERIAL PRIMARY KEY,
    address_id INTEGER      NOT NULL REFERENCES address(address_id),
    name       VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------------
-- position
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS position (
    position_id    SERIAL PRIMARY KEY,
    company_id     INTEGER       NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
    title          VARCHAR(255)  NOT NULL,
    salary         NUMERIC(10,2),
    education_req  VARCHAR(255),
    experience_req VARCHAR(255),
    description    VARCHAR(2000),
    listing_date   DATE          NOT NULL
);

-- ---------------------------------------------------------------------------
-- applied_jobs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applied_jobs (
    job_id               SERIAL PRIMARY KEY,
    user_id              INTEGER     NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    position_id          INTEGER     NOT NULL REFERENCES position(position_id) ON DELETE CASCADE,
    years_of_experience  INTEGER     NOT NULL,
    application_date     DATE        NOT NULL,
    application_status   VARCHAR(50) NOT NULL DEFAULT 'pending review'
);
