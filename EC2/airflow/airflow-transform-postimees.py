"""
Postimees Bronze → Silver transformatsiooni DAG.

Loeb bronze.raw tabelist töötlemata Postimehe RSS XML-i,
parsib uudised, filtreerib kategooriate järgi ja
laadib silver.news tabelisse.
"""

import logging
from datetime import datetime, timezone
import dateutil.parser
from bs4 import BeautifulSoup

from airflow.models import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator

# DAG-i põhiseaded
default_args = {
    'start_date': datetime(2022, 1, 1)
}

# Postimehe spetsiifilised välistatavad kategooriad
EXCLUDE_TOPICS = [
    'Sport', 'Talisport', 'Jäähoki', 'Kergejõustik', 'Poks', 'Jalgpall',
    'Koondisejalgpall', 'WRC', 'Elu24', 'Lemmik', 'Kodu', 'Õues', 'Reis',
    'Naine', 'Suhted & seks', 'Digiajakirjad', 'Horoskoop', 'Meelelahutus',
    'Sõbranna', 'Tervis'
]

SOURCE = 'POSTIMEES'

# ---------------------------------------------------------
# Pythoni funktsioonid (Operatorite sisu)


def fetch_new_bronze_rows(**context):
    """Pärib bronze.raw tabelist uued Postimehe read, mida pole veel töödeldud."""
    pg_hook = PostgresHook(
        postgres_conn_id='aws-postgres',
        schema='db_news'
    )

    conn = pg_hook.get_conn()
    cur = conn.cursor()

    try:
        # Tagame, et incrementali rida on olemas
        cur.execute(
            "SELECT 1 FROM silver.news_incremental WHERE source = %s",
            (SOURCE,)
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO silver.news_incremental (source, latest_news_dtime, latest_bronze_id) VALUES (%s, %s, %s)",
                (SOURCE, datetime(2026, 1, 1, tzinfo=timezone.utc), 0)
            )
            conn.commit()

        # Leiame viimase töödeldud bronze rea ID
        cur.execute(
            "SELECT latest_bronze_id FROM silver.news_incremental WHERE source = %s",
            (SOURCE,)
        )
        result = cur.fetchone()
        latest_bronze_id = result[0] if (result and result[0] is not None) else 0

        logging.info(f"Viimane töödeldud bronze ID ({SOURCE}): {latest_bronze_id}")

        # Pärime kõik uued read
        cur.execute(
            "SELECT id, body FROM bronze.raw WHERE source = %s AND id > %s ORDER BY id",
            (SOURCE, latest_bronze_id)
        )
        rows = cur.fetchall()

        logging.info(f"Leitud {len(rows)} uut bronze rida")

        # Edastame andmed järgmisele taskile XCom kaudu
        context['ti'].xcom_push(key='bronze_rows', value=rows)

    finally:
        cur.close()
        conn.close()


def transform_and_load(**context):
    """Parsib bronze XML-i, filtreerib ja laadib silver.news tabelisse."""
    rows = context['ti'].xcom_pull(key='bronze_rows', task_ids='fetch_new_bronze_rows')

    if not rows:
        logging.info("Uusi bronze ridu ei leitud, midagi pole teha.")
        return

    pg_hook = PostgresHook(
        postgres_conn_id='aws-postgres',
        schema='db_news'
    )

    conn = pg_hook.get_conn()
    cur = conn.cursor()

    try:
        # Tagame, et incrementali rida on olemas
        cur.execute(
            "SELECT latest_news_dtime FROM silver.news_incremental WHERE source = %s",
            (SOURCE,)
        )
        result = cur.fetchone()
        if not result:
            cur.execute(
                "INSERT INTO silver.news_incremental (source, latest_news_dtime, latest_bronze_id) VALUES (%s, %s, %s)",
                (SOURCE, datetime(2026, 1, 1, tzinfo=timezone.utc), 0)
            )
            conn.commit()
            pm_benchmark = datetime(2026, 1, 1, tzinfo=timezone.utc)
        else:
            pm_benchmark = result[0] if result[0] is not None else datetime(2026, 1, 1, tzinfo=timezone.utc)

        logging.info(f"Algne {SOURCE} benchmark: {pm_benchmark}")

        dates = []
        max_bronze_id = 0
        inserted_count = 0

        for bronze_id, body in rows:
            max_bronze_id = max(max_bronze_id, bronze_id)

            # Parsime RSS XML-i
            soup = BeautifulSoup(body, features='lxml-xml')
            articles = soup.find_all('item')

            for a in articles:
                pubDate_el = a.find('pubDate')
                if not pubDate_el:
                    continue
                pubDate = pubDate_el.text.strip()
                isodate = dateutil.parser.parse(pubDate)

                categories = [c.text.strip() for c in a.find_all('category') if c.text]
                is_excluded = len(categories) > 0 and all(cat in EXCLUDE_TOPICS for cat in categories)

                # Filtreerimine: ainult uued ja lubatud kategooriad
                if pm_benchmark < isodate and not is_excluded:
                    title = a.find('title').text.strip() if a.find('title') else ''
                    description = a.find('description').text.strip() if a.find('description') else ''
                    link = a.find('link').text.strip() if a.find('link') else ''

                    # Uue uudise lisamine silver tabelisse
                    sql = """INSERT INTO silver.news (source, news_dtime, title, description, link)
                             VALUES (%s, %s, %s, %s, %s)
                             ON CONFLICT (link) DO NOTHING
                             RETURNING id"""
                    cur.execute(sql, (SOURCE, isodate, title, description, link))
                    res = cur.fetchone()
                    if res:
                        news_id = res[0]
                        # Lisame kategooriad seostabelisse
                        for cat in categories:
                            sql_cat = """INSERT INTO silver.news_categories (news_id, category)
                                         VALUES (%s, %s)
                                         ON CONFLICT (news_id, category) DO NOTHING"""
                            cur.execute(sql_cat, (news_id, cat))

                    dates.append(isodate)
                    inserted_count += 1
                    logging.info(f"Salvestatud: {title}")

        # Uuendame benchmarke
        currentbenchmark = ''
        if dates:
            currentbenchmark = max(dates)
            logging.info(f"Uus {SOURCE} benchmark: {currentbenchmark}")

        # Uuendame news_dtime benchmarki
        sql_update = """UPDATE silver.news_incremental
                        SET latest_news_dtime = COALESCE(NULLIF(%s::TEXT,''), latest_news_dtime::text)::timestamptz
                        WHERE source = %s"""
        cur.execute(sql_update, (currentbenchmark, SOURCE))

        # Uuendame bronze ID benchmarki
        if max_bronze_id > 0:
            sql_bronze = """UPDATE silver.news_incremental
                            SET latest_bronze_id = %s
                            WHERE source = %s"""
            cur.execute(sql_bronze, (max_bronze_id, SOURCE))

        conn.commit()
        logging.info(f"Kokku lisatud {inserted_count} uudist, max bronze ID: {max_bronze_id}")

    except Exception as e:
        logging.error(f"Viga: {e}")
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


# ---------------------------------------------------------
# DAG-i definitsioon

with DAG(
    dag_id='transform_postimees_bronze_to_silver',
    schedule='0 * * * *',  # Käivitub iga tunni tagant
    default_args=default_args,
    catchup=False,
    tags=["transform", "postimees", "bronze-to-silver"]
) as dag:

    # Task 1: Uute bronze ridade pärimine
    t_fetch = PythonOperator(
        task_id='fetch_new_bronze_rows',
        python_callable=fetch_new_bronze_rows,
    )

    # Task 2: Transformeerimine ja laadimine silverisse
    t_transform = PythonOperator(
        task_id='transform_and_load',
        python_callable=transform_and_load,
    )

    # Järjestikune käivitamine
    t_fetch >> t_transform
