CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.raw
(
    id                 BIGSERIAL PRIMARY KEY,
    source             TEXT NOT NULL,
    inserted_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    hash               TEXT NOT NULL UNIQUE,
    body               TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hash ON bronze.raw (hash);

-- Lisame silver.news_incremental tabelisse veeru viimase töödeldud bronze rea jälgimiseks
ALTER TABLE silver.news_incremental
    ADD COLUMN IF NOT EXISTS latest_bronze_id BIGINT DEFAULT 0;
