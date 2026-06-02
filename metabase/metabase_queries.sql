-- Uudiste jaotus allika/kategooria järgi

SELECT
  n.source,
  c.category,
  n.news_dtime::DATE,
  COUNT(distinct n.title) AS count
FROM silver.news n
LEFT JOIN silver.news_categories c ON n.id = c.news_id
GROUP BY n.source, c.category, n.news_dtime::DATE
ORDER BY n.source, count DESC;
------------------------------------------------------------------------------------------------------------------------
-- Maailmasündmuste jaotus kategooriate järgi

SELECT
  c.category,
  CASE
    WHEN n.title ILIKE '%usa%' THEN 'USA'
    WHEN n.title ILIKE '%venemaa%' THEN 'Venemaa'
    WHEN n.title ILIKE '%Iraan%' THEN 'Iraan'
    WHEN n.title ILIKE '%hiina%' THEN 'Hiina'
    ELSE 'Other'
  END AS keyword,
  COUNT(DISTINCT n.title) AS count
FROM silver.news n
LEFT JOIN silver.news_categories c ON n.id = c.news_id
GROUP BY c.category, keyword
ORDER BY c.category, count DESC;
------------------------------------------------------------------------------------------------------------------------
-- Top 10 kategooriad

SELECT c.category AS kategooria,
       count(distinct n.title) AS kokku
FROM silver.news n
LEFT JOIN silver.news_categories c ON n.id = c.news_id
GROUP BY c.category
ORDER BY count(*) DESC;
------------------------------------------------------------------------------------------------------------------------
-- Top 10 märksõna

WITH cleaned_news           AS (SELECT DISTINCT description FROM silver.news),
     deconstructed_sentence
                            AS (SELECT LOWER(REGEXP_REPLACE(word, '[[:punct:]]+$', '')) AS puhas_sona -- remove trailing punctuation
                                FROM (SELECT REGEXP_SPLIT_TO_TABLE(description, '\s+') AS word FROM cleaned_news) t
                                WHERE word !~ '[0-9]' -- remove anything containing numbers
     )
SELECT puhas_sona,
       COUNT(*) AS total_use
FROM deconstructed_sentence d
WHERE puhas_sona <> '' -- avoid empty strings after cleaning
  AND NOT EXISTS (SELECT 1 FROM silver.keywords k WHERE NOT k.wanted AND LOWER(k.keyword) = d.puhas_sona)
GROUP BY puhas_sona
ORDER BY total_use DESC
LIMIT 10;
------------------------------------------------------------------------------------------------------------------------
-- Uudiste arv päevade lõikes

SELECT news_dtime::date AS kuupäev,
         count(distinct title) AS uudiste_arv
FROM silver.news
GROUP BY news_dtime::date
ORDER BY news_dtime::date DESC;
------------------------------------------------------------------------------------------------------------------------
-- Erinevate sündmuste kajastus meedias

WITH themes AS (

    SELECT 'Ukraina sõda' AS theme, keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('ukraina','zelenski','droon','venemaa')

    UNION ALL

    SELECT 'USA', keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('trump','donald','maga','usa','ameerika')

    UNION ALL

    SELECT 'Iraani sõda', keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('iraan','iran','teheran')

    UNION ALL

    SELECT 'Hiina', keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('hiina','taiwan','xi')
),

cleaned_news AS (
    SELECT DISTINCT
        description,
        date_trunc('day', news_dtime) AS day
    FROM silver.news
),

normalized_news AS (
    SELECT
        description,
        day,
        REGEXP_REPLACE(LOWER(description), '[^a-zäöüõ\s]', '', 'g') AS clean_text
    FROM cleaned_news
),

theme_matches AS (
    SELECT DISTINCT
        n.description,
        n.day,
        t.theme
    FROM normalized_news n
    JOIN themes t
      ON n.clean_text ILIKE '%' || t.keyword || '%'
),

total_articles AS (
    SELECT
        day,
        COUNT(*) AS total
    FROM cleaned_news
    GROUP BY day
),

theme_counts AS (
    SELECT
        day,
        theme,
        COUNT(*) AS article_count
    FROM theme_matches
    GROUP BY day, theme
),

theme_percentages AS (
    SELECT
        tc.day,
        tc.theme,
        tc.article_count,
        ta.total,
        ROUND(100.0 * tc.article_count / NULLIF(ta.total, 0), 2) AS article_percentage
    FROM theme_counts tc
    JOIN total_articles ta
      ON tc.day = ta.day
)

SELECT *
FROM theme_percentages

UNION ALL

SELECT
    ta.day,
    'Kõik uudised' AS theme,
    ta.total AS article_count,
    ta.total AS total,
    100.0 AS article_percentage
FROM total_articles ta

ORDER BY day, article_percentage DESC;
------------------------------------------------------------------------------------------------------------------------
-- Suuremad sündmused maailmas

WITH themes AS (

    SELECT 'Ukraina sõda' AS theme, keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('ukraina','zelenski','droon','venemaa')

    UNION ALL

    SELECT 'USA', keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('trump','donald','maga','usa','ameerika')

    UNION ALL

    SELECT 'Iraani sõda', keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('iraan','iran','teheran')

    UNION ALL

    SELECT 'Hiina', keyword
    FROM silver.keywords
    WHERE LOWER(keyword) IN ('hiina','taiwan','xi')
),

cleaned_news AS (
    SELECT DISTINCT
        title,
        DATE_TRUNC('day', news_dtime) AS day
    FROM silver.news
),

normalized_news AS (
    SELECT
        title,
        day,
        REGEXP_REPLACE(LOWER(title), '[^a-zäöüõ\s]', '', 'g') AS clean_text
    FROM cleaned_news
),

theme_matches AS (
    SELECT DISTINCT
        n.title,
        n.day,
        COALESCE(t.theme, 'Other') AS theme
    FROM normalized_news n
    LEFT JOIN themes t
      ON n.clean_text ILIKE '%' || t.keyword || '%'
)

SELECT
    day,
    theme,
    COUNT(*) AS article_count
FROM theme_matches
GROUP BY day, theme
ORDER BY day ASC, article_count DESC;
------------------------------------------------------------------------------------------------------------------------