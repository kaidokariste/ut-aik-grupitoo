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


------------------
select * from silver.news where news.source = 'AP' order by news_dtime desc;
select * from silver.news_incremental;

--truncate silver.news;
UPDATE silver.news_incremental set latest_news_dtime = '2026-05-09 13:59:00+03:00' where source = 'ERR'

