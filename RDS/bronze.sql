CREATE TABLE IF NOT EXISTS bronze.raw
(
    id                 BIGSERIAL PRIMARY KEY,
    source             TEXT NOT NULL,
    inserted_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    hash               TEXT NOT NULL UNIQUE,
    body               TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hash ON bronze.raw (hash);
