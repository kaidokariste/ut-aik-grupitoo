import requests
import psycopg2
from bs4 import BeautifulSoup
import os
from datetime import datetime
import dateutil.parser
from dateutil.tz import gettz
from dotenv import load_dotenv
load_dotenv()

def get_connection():
    """
    Get database connection handle
    """
    return psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %
                            (os.getenv('DB_DATABASE'),
                             os.getenv('DB_USERNAME'),
                             os.getenv('DB_HOSTNAME'),
                             os.getenv('DB_PASSWORD')))

def db_query():
    query = "SELECT version()"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result
    except psycopg2.Error as err:
        print(err)

def get_err_news():
    dates = []

    currentbenchmark=''
    # List of excluded topics
    exclude_topics = ['Arhitektuur', 'Teater', 'ETV uudised', 'Kunst', 'Raadiouudised', 'Inimesed','Galerii',
                      'Kultuurisaated','Viipekeelsed','Tele/raadio',
                      'Arvamus','Ühiskond','Loodus','Galeriid','TV10 Olümpiastarti','Muusika','ETV spordisaade']


    r = requests.get("https://www.err.ee/rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.find_all('item')

    try:

        conn = get_connection()
        cur = conn.cursor()

        sql_ts = """select latest_news_dtime from silver.news_incremental where source = 'ERR'"""

        ## Peaks tegema päringu incremental tabelisse
        cur.execute(sql_ts)
        result = cur.fetchone()

        err_benchmark = result[0]

        print('Initial ERR benchmark', err_benchmark)

        for a in articles:
            pubDate = a.find('pubDate').text
            isodate = dateutil.parser.parse(pubDate)
            category = a.find('category').text
            # Get only news where date is newer than current saved benchmark and category is not excluded
            if err_benchmark < isodate and category not in exclude_topics:
                title = a.find('title').text
                description = a.find('description').text
                link = a.find('link').text

                # SQL Insert
                sql = """INSERT INTO silver.news (source, news_dtime, title, category, description, link) VALUES (%s, %s, %s, %s, %s, %s )"""

                cur.execute(sql, ('ERR', isodate, title, category, description, link))
                dates.append(isodate)
                print(f"Salvestatud: {title}")

                dates.append(isodate)

        if dates:
            currentbenchmark = max(dates)
            print(f"Uus ERR benchmark: {currentbenchmark}")

        # Uuenda ERR benchmark
        sql_update = """ UPDATE silver.news_incremental set latest_news_dtime = COALESCE(NULLIF(%s::TEXT,''),latest_news_dtime::text)::timestamptz where source = 'ERR' """
        cur.execute(sql_update, (currentbenchmark,))

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.Error as err:
        print(f"Andmebaasi viga: {err}")
    except Exception as e:
        print(f"Viga: {e}")


def get_aripaev_news():
    dates = []

    currentbenchmark = ''
    # List of excluded topics

    exclude_topics = ['Lisa', 'Saated', 'TOP', 'Leht']


    r = requests.get("http://feeds.feedburner.com/aripaev-rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.find_all('item')

    try:
        conn = get_connection()
        cur = conn.cursor()

        sql_ts = """SELECT latest_news_dtime FROM silver.news_incremental WHERE source = 'AP'"""

        ## Peaks tegema päringu incremental tabelisse

        cur.execute(sql_ts)
        result = cur.fetchone()

        ap_benchmark = result[0]

        print('Initial AP benchmark', ap_benchmark)

        for a in articles:
            pubDate = a.find('pubDate').text.strip()
            isodate = dateutil.parser.parse(pubDate)
            category = a.find('category').text.strip()
            # Get only news where date is newer than current saved benchmark and category is not excluded

            if ap_benchmark < isodate and category not in exclude_topics:
                title = a.find('title').text.strip()
                description = a.find('description').text.strip()
                link = a.find('link').text.strip()

            # SQL Insert
            sql = """INSERT INTO silver.news (source, news_dtime, title, category, description, link) VALUES (%s, %s, %s, %s, %s, %s)"""

            cur.execute(sql, ('AP', isodate, title, category, description, link))
            dates.append(isodate)
            print(f"Salvestatud: {title}")

            dates.append(isodate)

        if dates:
            currentbenchmark = max(dates)
            print(f"Uus AP benchmark: {currentbenchmark}")

        # Uuenda ERR benchmark
        sql_update = """ UPDATE silver.news_incremental \
                         SET latest_news_dtime = COALESCE(NULLIF(%s::TEXT, ''), latest_news_dtime::TEXT)::TIMESTAMPTZ \
                         WHERE source = 'AP' """
        cur.execute(sql_update, (currentbenchmark,))

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.Error as err:
        print(f"Andmebaasi viga: {err}")
    except Exception as e:
        print(f"Viga: {e}")

if __name__ == "__main__":
    #get_err_news()
    get_aripaev_news()
    #print(db_query())