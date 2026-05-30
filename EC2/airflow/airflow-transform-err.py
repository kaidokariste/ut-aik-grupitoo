"""
ERR Bronze → Silver transformatsiooni DAG.

Loeb bronze.raw tabelist töötlemata ERR RSS XML-i,
parsib uudised, filtreerib kategooriate järgi ja
laadib silver.news tabelisse.
"""

from datetime import datetime
import dateutil.parser
from bs4 import BeautifulSoup

from airflow.models import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator


# DAG-i põhiseaded
default_args = {
    'start_date': datetime(2022, 1, 1)
}

# ERR-i spetsiifilised välistatavad kategooriad
EXCLUDE_TOPICS = [
    'Teater', 'ETV uudised', 'Raadiouudised', 'Galerii',
    'Kultuurisaated', 'Viipekeelsed', 'Tele/raadio', 'Loodus',
    'Galeriid', 'TV10 Olümpiastarti', 'Muusika', 'ETV spordisaade'
]

SOURCE = 'ERR'

# ---------------------------------------------------------
# Pythoni funktsioonid (Operatorite sisu)


def fetch_new_bronze_rows(**context):
    """Pärib bronze.raw tabelist uued ERR read, mida pole veel töödeldud."""
    pg_hook = PostgresHook(
        postgres_conn_id='aws-postgres',
        schema='db_news'
    )

    conn = pg_hook.get_conn()
    cur = conn.cursor()

    try:
        # Leiame viimase töödeldud bronze rea ID
        cur.execute(
            "SELECT latest_bronze_id FROM silver.news_incremental WHERE source = %s",
            (SOURCE,)
        )
        result = cur.fetchone()
        latest_bronze_id = result[0] if result else 0

        print(f"Viimane töödeldud bronze ID ({SOURCE}): {latest_bronze_id}")

        # Pärime kõik uued read
        cur.execute(
            "SELECT id, body FROM bronze.raw WHERE source = %s AND id > %s ORDER BY id",
            (SOURCE, latest_bronze_id)
        )
        rows = cur.fetchall()

        print(f"Leitud {len(rows)} uut bronze rida")

        # Edastame andmed järgmisele taskile XCom kaudu
        context['ti'].xcom_push(key='bronze_rows', value=rows)

    finally:
        cur.close()
        conn.close()


def transform_and_load(**context):
    """Parsib bronze XML-i, filtreerib ja laadib silver.news tabelisse."""
    rows = context['ti'].xcom_pull(key='bronze_rows', task_ids='fetch_new_bronze_rows')

    if not rows:
        print("Uusi bronze ridu ei leitud, midagi pole teha.")
        return

    pg_hook = PostgresHook(
        postgres_conn_id='aws-postgres',
        schema='db_news'
    )

    conn = pg_hook.get_conn()
    cur = conn.cursor()

    try:
        # Leiame viimase salvestatud uudise aja (incremental load loogika)
        cur.execute(
            "SELECT latest_news_dtime FROM silver.news_incremental WHERE source = %s",
            (SOURCE,)
        )
        result = cur.fetchone()
        err_benchmark = result[0]

        print(f"Algne ERR benchmark: {err_benchmark}")

        dates = []
        max_bronze_id = 0
        inserted_count = 0

        for bronze_id, body in rows:
            max_bronze_id = max(max_bronze_id, bronze_id)

            # Parsime RSS XML-i
            soup = BeautifulSoup(body, features='lxml-xml')
            articles = soup.find_all('item')

            for a in articles:
                pubDate = a.find('pubDate').text
                isodate = dateutil.parser.parse(pubDate)
                category = a.find('category').text

                # Filtreerimine: ainult uued ja lubatud kategooriad
                if err_benchmark < isodate and category not in EXCLUDE_TOPICS:
                    title = a.find('title').text
                    description = a.find('description').text
                    link = a.find('link').text

                    # Uue uudise lisamine silver tabelisse
                    sql = """INSERT INTO silver.news (source, news_dtime, title, category, description, link)
                             VALUES (%s, %s, %s, %s, %s, %s)"""
                    cur.execute(sql, (SOURCE, isodate, title, category, description, link))

                    dates.append(isodate)
                    inserted_count += 1
                    print(f"Salvestatud: {title}")

        # Uuendame benchmarke
        currentbenchmark = ''
        if dates:
            currentbenchmark = max(dates)
            print(f"Uus ERR benchmark: {currentbenchmark}")

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
        print(f"Kokku lisatud {inserted_count} uudist, max bronze ID: {max_bronze_id}")

    except Exception as e:
        print(f"Viga: {e}")
        raise

    finally:
        cur.close()
        conn.close()


# ---------------------------------------------------------
# DAG-i definitsioon

with DAG(
    dag_id='transform_err_bronze_to_silver',
    schedule='0 * * * *',  # Käivitub iga tunni tagant
    default_args=default_args,
    catchup=False,
    tags=["transform", "err", "bronze-to-silver"]
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
