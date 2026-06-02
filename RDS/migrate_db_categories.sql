-- Andmebaasi migratsioon: Kategooria viimine tabeli silver.news veerust vahetabelisse silver.news_categories

-- 1. Loo vahetabel
CREATE TABLE IF NOT EXISTS silver.news_categories (
    news_id  BIGINT REFERENCES silver.news(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    PRIMARY KEY (news_id, category)
);

-- 2. Täida vahetabel olemasoleva kategooria veeru andmetega
INSERT INTO silver.news_categories (news_id, category)
SELECT id, category
FROM silver.news
WHERE category IS NOT NULL AND category <> ''
ON CONFLICT (news_id, category) DO NOTHING;

-- 3. Eemalda kategooria veerg tabelist silver.news
ALTER TABLE silver.news DROP COLUMN IF EXISTS category;
