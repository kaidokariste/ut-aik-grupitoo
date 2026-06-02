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
    title       VARCHAR,
    description TEXT,
    link        VARCHAR UNIQUE
);

CREATE TABLE silver.news_incremental
(
    source            VARCHAR(10),
    latest_news_dtime timestamptz
);
INSERT INTO silver.news_incremental(source,latest_news_dtime) VALUES ('ERR','2026-01-01 01:00:00.000000 +00:00');
INSERT INTO silver.news_incremental(source,latest_news_dtime) VALUES ('ÄRIPÄEV','2026-01-01 01:00:00.000000 +00:00');
INSERT INTO silver.news_incremental(source,latest_news_dtime) VALUES ('POSTIMEES','2026-01-01 01:00:00.000000 +00:00');


------------------------------
-- Lisame tabelile surrogaatvõtme
ALTER TABLE silver.news ADD COLUMN id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

-- Kategooriate seostabel
CREATE TABLE IF NOT EXISTS silver.news_categories (
    news_id  BIGINT REFERENCES silver.news(id) ON DELETE CASCADE,
    category VARCHAR NOT NULL,
    PRIMARY KEY (news_id, category)
);

------------------

select min(news_dtime) from silver.news order by news_dtime desc;
select * from silver.news_incremental;


--UPDATE silver.news_incremental set latest_news_dtime = '2026-05-09 13:59:00+03:00' where source = 'ERR'

select * from  silver.news WHERE title ILIKE ANY (ARRAY['%trump%', '%usa%']);
select * from  silver.news WHERE title ILIKE ANY (ARRAY['%big%', '%pruunsild%','%eamets%','%artur taavet%']);
select * from  silver.news WHERE title ILIKE ANY (ARRAY['%sõda%', '%rahu%','%ukraina%','%venemaa%']);

---------------
-- Sõnade kasutuse tabel:
DROP TABLE IF EXISTS silver.keywords;

CREATE TABLE IF NOT EXISTS silver.keywords
(
  keyword TEXT PRIMARY KEY,
  wanted  BOOLEAN DEFAULT FALSE
);

SELECT *
FROM silver.keywords;

-- Soovimatud märksõnad:
INSERT INTO silver.keywords (keyword)
SELECT unnest(ARRAY[
  '-','–','000','aasta','aastal','aastast','aastat','aastani','aastaks','aastaga','aastasse','aga','ajal','all','alla','alt',
  'alates','alati','alati','alates','alistas','andis','andnud','annab','antud','eest','ehk','ei','eile','eilne','eilset',
  'eilseks','enam','enne','ennast','ennastki','ERR-i','esimene','esimese','esimesel','esimest','esimeseks','esindas',
  'esmaspäev','esmaspäeval','et','finaalis','hooaja','hooajal','hooajast','hinnangul','hinnanguga','homme','homsest','homseks',
  'ise','isegi','iseenesest','ja','jaoks','juba','juhul','jõudis','jõudnud','jõuab','ka','kaheksa','kaks','kaasa','kaudu',
  'kas','kasvanud','kasvab','kasvas','kell','kella','kellal','kes','kelle','kelles','kellest','kindlustas','kinnitanud',
  'kinnitas','kirjutab','kirjutas','koha','kohal','kohale','kohast','kohta','koos','kokku','kolm','kolmapäev','kolmapäeval',
  'kommenteerinud','kommenteeris','korda','kord','korraga','kui','kuigi','kuidas','kuid','kuna','kus','kust','kuhu',
  'kuus','kuue','kuuel','kõige','kõik','kõiki','kõigil','kõigest','kümme','kümne','kümnel','laupäev','laupäeval',
  'läbi','liiga','ligi','ligikaudu','looga','mail','mida','mille','millest','milles','milleks','mis','mitme','mitte',
  'möödunud','möödub','möödus','nad','neist','neli','neljapäev','neljapäeval','nende','neile','neil','nii','ning','nädal',
  'nädala','nädalal','nädalast','nädalaks','nädalavahetusel','nädalavahetus','nüüd','nüüdseks','ole','olen','oled','oleks',
  'oleksid','oli','olnud','olla','olema','olles','oma','omad','omas','on','palju','paljude','paljusid','peab','peaks',
  'peaksid','pole','polnud','pärast','pärastlõunal','praegu','praeguseks','pühapäev','pühapäeval','reedel','reede','riigi',
  'riigis','riigist','rohkem','rohket','rääkis','rääkinud','räägib','sai','saab','saanud','saates','saade','seitse','seitsme',
  'sel','seal','sealt','selgitas','selgitanud','selgub','sellest','selle','seda','see','selline','sellised','sest','siis',
  'stuudios','sõnul','ta','tal','talle','temalt','taas','tagasi','teatas','teatanud','teatasid','tegi','teinud','teeb',
  'teha','teise','teisel','teiselt','teisipäev','teisipäeval','tekkinud','tema','temaga','temal','tuleb','tuli','tulemas',
  'tunnistanud','tunnistas','tänane','tänase','tänasel','tänases','tänaseks','tänasest','tänasega','täna','tänavu','uue',
  'uut','uus','uusi','uues','vastu','vaid','vahel','vahepeal','veel','viimase','viimane','viimased','viis','viie','või',
  'võib','võiks','võinud','võitis','võitnud','välja','väljas','väljast','väga','vähem','väitis','väitnud','üha','üks',
  'üheksa','ühe','ühel','üle','üles','ülesse','üleeile','ülehomme','ütlenud','ütles','ütleb','järel','järgi','järgmisel'
                    ])
ON CONFLICT (keyword) DO NOTHING;

-- Soovitud märksõnad:
INSERT INTO silver.keywords
(keyword, wanted)
VALUES
  ('ameerika', TRUE), ('donald', TRUE), ('droon', TRUE), ('hiina', TRUE), ('iran', TRUE), ('iraan', TRUE), ('maga', TRUE),
  ('putin', TRUE), ('taiwan', TRUE), ('teheran', TRUE), ('trump', TRUE), ('ukraina', TRUE), ('USA', TRUE), ('venemaa', TRUE),
  ('Xi', TRUE), ('zelenski', TRUE)
ON CONFLICT (keyword) DO NOTHING;


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
--HAVING COUNT(*) > 10
ORDER BY total_use DESC;