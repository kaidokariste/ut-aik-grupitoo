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

