# EC2 — Airflow orkestreerimine

EC2 instants hostib Apache Airflow keskkonda, mis orkestreerib uudiste ETL-protsessi. Airflow käivitatakse Docker Compose abil ja see töötab CeleryExecutor režiimis koos Redis ja PostgreSQL teenustega.

## EC2 instants

- **AMI:** Ubuntu 26.04 LTS (`ubuntu-resolute-26.04-amd64-server`)
- **Platvorm:** Linux/UNIX
- **vCPU-d:** 2
- **vMälumaht:** 8GB

![EC2 instansi detailid](airflow1.png)

## Airflow

Airflow on paigaldatud Docker Compose abil (`docker-compose.yaml`) ning kasutab järgmisi teenuseid:

| Teenus | Kirjeldus |
|--------|-----------|
| `postgres` | Airflow metaandmebaas (PostgreSQL 16) |
| `redis` | Celery sõnumivahendaja (Redis 7.2) |
| `airflow-apiserver` | Airflow veebiserver (port 8080) |
| `airflow-scheduler` | DAG-ide ajastaja |
| `airflow-dag-processor` | DAG-ide töötleja |
| `airflow-worker` | Celery töötaja |
| `airflow-triggerer` | Trigerite haldur |

### DAG: `airflow_etl_dag_news`

DAG käivitub **iga 2 tunni tagant** (`0 */2 * * *`) ja sisaldab kahte paralleelset taski:

1. **`processing_err_news`** — tõmbab ERR RSS voost uudised
2. **`processing_aripaev_news`** — tõmbab Äripäeva RSS voost uudised

Mõlemad taskid:
- Laevad RSS XML-i alla
- Parsivad artiklid BeautifulSoup abil
- Filtreerivad välja soovimatud kategooriad (nt Teater, Galerii, Saated)
- Kasutavad **inkrementaalset laadimist** — salvestavad ainult uudised, mis on uuemad kui eelmise käivituse ajatempel (`silver.news_incremental` tabel)
- Sisestavad uued uudised `silver.news` tabelisse PostgreSQL (RDS) andmebaasis
- Kasutavad Airflow `PostgresHook` ühendust nimega `aws-postgres`

![Airflow DAG-ide nimekiri](airflow2.png)

![Airflow DAG-i käivituste ajalugu](airflow3.png)

## Failide struktuur

```
EC2/
├── airflow/
│   ├── airflow-etl-dag-news.py   # Airflow DAG definitsioon
│   ├── extract_news.py           # Standalone uudiste ekstraktimise skript
│   ├── docker-compose.yaml       # Airflow Docker Compose konfiguratsioon
│   ├── airflow_pg_hook_example.txt
│   └── .env.example              # Keskkonnamuutujate näidis
├── airflow1.png                  # EC2 instansi kuvatõmmis
├── airflow2.png                  # Airflow DAG-ide kuvatõmmis
├── airflow3.png                  # DAG käivituste ajaloo kuvatõmmis
└── requirements.txt              # Pythoni sõltuvused
```

## Käivitamine

```bash
# 1. Kopeeri keskkonnamuutujad
cp airflow/.env.example airflow/.env
# Muuda .env failis andmebaasi ja Airflow seaded

# 2. Käivita Airflow
cd airflow
docker compose up -d

# 3. Airflow veebiliides
# http://localhost:8080 (kasutaja/parool: airflow)
```

## Keskkonnamuutujad

| Muutuja | Kirjeldus |
|---------|-----------|
| `DB_DATABASE` | Andmebaasi nimi (`db_news`) |
| `DB_USERNAME` | Andmebaasi kasutaja |
| `DB_HOSTNAME` | RDS hosti aadress |
| `DB_PASSWORD` | Andmebaasi parool |
| `AIRFLOW_UID` | Airflow kasutaja ID |
| `_AIRFLOW_WWW_USER_USERNAME` | Airflow veebi kasutajanimi |
| `_AIRFLOW_WWW_USER_PASSWORD` | Airflow veebi parool |
