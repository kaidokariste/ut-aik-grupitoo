import requests
from bs4 import BeautifulSoup
from datetime import datetime
import dateutil.parser

from airflow.models import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import Variable

# DAG-i põhiseaded
default_args = {
    'start_date': datetime(2022, 1, 1)
}

# ---------------------------------------------------------
# Pythoni funktsioonid (Operatorite sisu)

def get_aripaev_news():
    """Tõmbab Äripäeva RSS voost uudised ja salvestab uued kanded andmebaasi."""
    dates = []
    currentbenchmark = ''

    # Teemad, mida me ei soovi andmebaasi salvestada
    exclude_topics = ['Lisa', 'Saated', 'Leht']

    # Päring RSS voogu ja XML-i parsimine
    r = requests.get("http://feeds.feedburner.com/aripaev-rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.find_all('item')

    try:
        # Airflow PostgresHooki loomine ühenduse loomiseks
        pg_hook = PostgresHook(
            postgres_conn_id='aws-postgres',  # Connection ID in airflow
            schema='db_news'  # Database Name
        )

        conn = pg_hook.get_conn()
        cur = conn.cursor()

        # Leiame viimase salvestatud uudise aja (incremental load loogika)
        sql_ts = """SELECT latest_news_dtime FROM silver.news_incremental WHERE source = 'AP'"""
        cur.execute(sql_ts)
        result = cur.fetchone()
        ap_benchmark = result[0]

        print('Initial AP benchmark', ap_benchmark)

        for a in articles:
            pubDate = a.find('pubDate').text.strip()
            isodate = dateutil.parser.parse(pubDate)
            category = a.find('category').text.strip()

            # Kontroll: Salvestame ainult juhul, kui uudis on uuem kui viimane benchmark ja kategooria on lubatud
            if ap_benchmark < isodate and category not in exclude_topics:
                title = a.find('title').text.strip()
                description = a.find('description').text.strip()
                link = a.find('link').text.strip()

                # Uue uudise lisamine andmebaasi
                sql = """INSERT INTO silver.news (source, news_dtime, title, category, description, link) VALUES (%s, %s, %s, %s, %s, %s)"""
                cur.execute(sql, ('AP', isodate, title, category, description, link))

                dates.append(isodate)
                print(f"Salvestatud: {title}")

        # Kui lisati uusi uudiseid, uuendame benchmarki tabelit kõige hilisema kuupäevaga
        if dates:
            currentbenchmark = max(dates)
            print(f"Uus AP benchmark: {currentbenchmark}")

        sql_update = """ UPDATE silver.news_incremental \
                         SET latest_news_dtime = COALESCE(NULLIF(%s::TEXT, ''), latest_news_dtime::TEXT)::TIMESTAMPTZ \
                         WHERE source = 'AP' """
        cur.execute(sql_update, (currentbenchmark,))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Viga: {e}")
        raise

def get_err_news():
    """Tõmbab ERR-i RSS voost uudised ja salvestab uued kanded andmebaasi."""
    dates = []
    currentbenchmark=''

    # ERR-i spetsiifilised välistatavad kategooriad
    exclude_topics = ['Teater', 'ETV uudised', 'Raadiouudised', 'Galerii',
                      'Kultuurisaated','Viipekeelsed','Tele/raadio','Loodus','Galeriid','TV10 Olümpiastarti','Muusika','ETV spordisaade']


    r = requests.get("https://www.err.ee/rss")
    soup = BeautifulSoup(r.content, features='lxml-xml')
    articles = soup.find_all('item')

    try:

        pg_hook = PostgresHook(
            postgres_conn_id='aws-postgres',
            schema='db_news'
        )

        conn = pg_hook.get_conn()
        cur = conn.cursor()

        # Kontrollime viimast ERR-i uudise aega
        sql_ts = """select latest_news_dtime from silver.news_incremental where source = 'ERR'"""
        cur.execute(sql_ts)
        result = cur.fetchone()

        err_benchmark = result[0]

        print('Initial ERR benchmark', err_benchmark)

        for a in articles:
            pubDate = a.find('pubDate').text
            isodate = dateutil.parser.parse(pubDate)
            category = a.find('category').text

            # Filtreerimine: ainult uued ja lubatud kategooriad
            if err_benchmark < isodate and category not in exclude_topics:
                title = a.find('title').text
                description = a.find('description').text
                link = a.find('link').text

                # SQL Insert
                sql = """INSERT INTO silver.news (source, news_dtime, title, category, description, link) VALUES (%s, %s, %s, %s, %s, %s )"""

                cur.execute(sql, ('ERR', isodate, title, category, description, link))
                dates.append(isodate)
                print(f"Salvestatud: {title}")

        # Uuendame andmebaasis märget viimase töödeldud uudise kohta
        if dates:
            currentbenchmark = max(dates)
            print(f"Uus ERR benchmark: {currentbenchmark}")

        # Uuenda ERR benchmark
        sql_update = """ UPDATE silver.news_incremental set latest_news_dtime = COALESCE(NULLIF(%s::TEXT,''),latest_news_dtime::text)::timestamptz where source = 'ERR' """
        cur.execute(sql_update, (currentbenchmark,))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Viga: {e}")
        raise
# ---------------------------------------------------------
# DAG-i definitsioon

with (DAG(dag_id='airflow_etl_dag_news',
         schedule='0 */2 * * *', # Käivitub iga 2 tunni tagant
         default_args=default_args,
         catchup=False,
         tags=["etl"])
      as dag):

    # Task 1: Äripäeva uudiste töötlus
    processing_aripaev_news = PythonOperator(
        task_id='processing_aripaev_news',
        python_callable=get_aripaev_news,
        do_xcom_push=False
    )

    # Task 2: ERR uudiste töötlus
    processing_err_news = PythonOperator(
        task_id='processing_err_news',
        python_callable=get_err_news,
        do_xcom_push=False
    )

    # Taskid käivitatakse paralleelselt
    [processing_err_news, processing_aripaev_news]

