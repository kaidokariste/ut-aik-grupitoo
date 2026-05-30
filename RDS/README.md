# RDS — PostgreSQL andmebaas

Amazon RDS PostgreSQL andmebaas on projekti keskne andmehoidla. Andmebaas kasutab medaljonarhitektuuri (bronze → silver → gold) kihtidega.

## RDS instants

| Parameeter | Väärtus |
|------------|---------|
| **DB identifier** | `db-ut-news` |
| **Mootor** | PostgreSQL |
| **Klass** | `db.t4g.micro` |
| **Regioon** | `eu-north-1a` |
| **Staatus** | Available |

![RDS instansi ülevaade](db1.png)

## Andmebaasi struktuur

Andmebaas `db_news` kasutab kolme skeemi:

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph LR
    subgraph RDS
        DB[("db_news")]
        DB --- B["bronze — toored sisendandmed"]
        DB --- S["silver — puhastatud ja struktureeritud andmed"]
        DB --- G["gold — reserveeritud, agregeeritud ärianalüütika"]
    end
```

### Bronze kiht — `bronze.raw`

Toored RSS XML-andmed, mille Lambda funktsioonid salvestavad:

| Veerg | Tüüp | Kirjeldus |
|-------|------|-----------|
| `id` | BIGSERIAL PK | Automaatne primaarvõti |
| `source` | TEXT NOT NULL | Allika nimi (ERR / ÄRIPÄEV) |
| `inserted_at` | TIMESTAMPTZ | Sisestamise ajatempel (DEFAULT NOW()) |
| `hash` | TEXT UNIQUE | MD5 räsi deduplikatsiooniks |
| `body` | TEXT NOT NULL | Toore RSS XML sisu |

Indeks: `idx_hash` veeru `hash` peal kiireks räsiotsinguks.

### Silver kiht — `silver.news`

Parsitud ja puhastatud uudiste tabel:

| Veerg | Tüüp | Kirjeldus |
|-------|------|-----------|
| `id` | BIGINT PK (IDENTITY) | Surrogaatvõti |
| `source` | VARCHAR | Allikas (ERR / AP) |
| `news_dtime` | TIMESTAMPTZ | Uudise avaldamise aeg |
| `category` | VARCHAR | Uudise kategooria |
| `title` | VARCHAR | Pealkiri |
| `description` | TEXT | Uudise kirjeldus/lühikokkuvõte |
| `link` | VARCHAR | Link originaaluudisele |

### Silver kiht — `silver.news_incremental`

Inkrementaalse laadimise jälgimistabel:

| Veerg | Tüüp | Kirjeldus |
|-------|------|-----------|
| `source` | VARCHAR(10) | Allikas (ERR / AP) |
| `latest_news_dtime` | TIMESTAMPTZ | Viimase töödeldud uudise ajatempel |
| `latest_bronze_id` | BIGINT | Viimati töödeldud `bronze.raw` rea ID |

### Silver kiht — `silver.keywords`

Märksõnade tabel teksti analüüsiks ja stoppsõnade filtreerimiseks:

| Veerg | Tüüp | Kirjeldus |
|-------|------|-----------|
| `keyword` | TEXT PK | Märksõna |
| `wanted` | BOOLEAN | `TRUE` = otsitav märksõna, `FALSE` = stoppsõna |

**Soovitud märksõnad** (geopoliitilised teemad): `trump`, `usa`, `ameerika`, `ukraina`, `venemaa`, `iraan`, `hiina`, `taiwan`, `zelenski`, `putin`, `xi` jm.

**Stoppsõnad**: eesti keele levinumad sidesõnad, asesõnad ja muud semantiliselt tühjad sõnad (~200 sõna).

## Tabelite seosed

```mermaid
%%{init: {'theme': 'neutral'}}%%
erDiagram
    "bronze.raw" {
        BIGSERIAL id PK
        TEXT source
        TIMESTAMPTZ inserted_at
        TEXT hash UK
        TEXT body
    }

    "silver.news" {
        BIGINT id PK
        VARCHAR source
        TIMESTAMPTZ news_dtime
        VARCHAR category
        VARCHAR title
        TEXT description
        VARCHAR link
    }

    "silver.news_incremental" {
        VARCHAR source
        TIMESTAMPTZ latest_news_dtime
        BIGINT latest_bronze_id
    }

    "silver.keywords" {
        TEXT keyword PK
        BOOLEAN wanted
    }

    "bronze.raw" ||--o{ "silver.news" : "allikas (XML parsimine)"
    "bronze.raw" ||--o{ "silver.news_incremental" : "viimati töödeldud rida"
    "silver.news_incremental" ||--o{ "silver.news" : "jälgib viimast laadimist"
    "silver.keywords" }|--|{ "silver.news" : "teksti analüüs"
```


## Failide struktuur

```
RDS/
├── db_setup.sql                          # Andmebaasi ja tabelite loomine
├── bronze.sql                            # Bronze kihi tabeli loomine
├── Kuvatõmmis 2026-05-29 100705.png      # RDS instansi kuvatõmmis
└── README.md
```
