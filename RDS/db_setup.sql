CREATE USER news_loader WITH ENCRYPTED PASSWORD 'lihtne-parool';
CREATE DATABASE db_news WITH ENCODING 'UTF8' LC_COLLATE ='en_US.UTF-8' LC_CTYPE ='en_US.UTF-8' OWNER news_loader;

set role news_loader;
CREATE SCHEMA IF NOT EXISTS bronze AUTHORIZATION news_loader;
CREATE SCHEMA IF NOT EXISTS silver AUTHORIZATION news_loader;
CREATE SCHEMA IF NOT EXISTS gold AUTHORIZATION news_loader;

-- Create silver table
CREATE TABLE silver.news
(
    source      VARCHAR,
    news_dtime  TIMESTAMP WITH TIME ZONE,
    category    VARCHAR,
    title       VARCHAR,
    description TEXT,
    link        VARCHAR
);

CREATE TABLE silver.news_incremental
(
    source            VARCHAR(10),
    latest_news_dtime timestamptz
);
INSERT INTO silver.news_incremental(source,latest_news_dtime) VALUES ('ERR','2026-01-01 01:00:00.000000 +00:00');
INSERT INTO silver.news_incremental(source,latest_news_dtime) VALUES ('AP','2026-01-01 01:00:00.000000 +00:00');

------------------------------
-- Lisame tabelile surrogaatvõtme
ALTER TABLE silver.news ADD COLUMN id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

------------------

select * from silver.news order by news_dtime desc;
select * from silver.news_incremental;


--UPDATE silver.news_incremental set latest_news_dtime = '2026-05-09 13:59:00+03:00' where source = 'ERR'

select * from  silver.news WHERE title ILIKE ANY (ARRAY['%trump%', '%usa%']);
select * from  silver.news WHERE title ILIKE ANY (ARRAY['%big%', '%pruunsild%','%eamets%','%laen%']);
select * from  silver.news WHERE title ILIKE ANY (ARRAY['%sõda%', '%rahu%','%ukraina%','%venemaa%']);

---------------

-- IDEE
---teemade sõnade puhastamine

WITH cleaned_news AS (SELECT DISTINCT description
                      FROM silver.news),

     deconstructed_sentence AS (SELECT REGEXP_SPLIT_TO_TABLE(
                                               description,
                                               '\s+'
                                       ) AS sona
                                FROM cleaned_news)

SELECT sona, COUNT(sona) AS total_use
FROM deconstructed_sentence
WHERE LOWER(trim(sona)) NOT IN ('ja', 'ning', 'on', 'saab', 'peaks', 'kuid', 'vaid','kes','järel','korda','toimuval',
                                'aga', 'mille', 'rohkem','pärast','sai','kirjutab','seda','kõik','pühapäeval','laupäeval',
                                'et','ehk','ei', 'kui', 'ka', 'oli', 'oma', 'ütles', 'sõnul', 'mis','-','stuudios','alistas',
                                'tekkinud')
GROUP BY sona
ORDER BY total_use DESC;