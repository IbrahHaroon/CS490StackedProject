-- =============================================================================
-- MIGRATION: Add title column to documents table
--
-- Safe to re-run — uses ALTER TABLE ... ADD COLUMN IF NOT EXISTS.
-- Run in Supabase SQL Editor before deploying the updated backend.
--
-- HOW TO RUN (Supabase):
--   1. Go to your Supabase project → SQL Editor
--   2. Paste the entire contents of this file
--   3. Click Run
-- =============================================================================

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS title VARCHAR(255);
