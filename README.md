# Naksitrallid — Kriisikollete kajastus Eesti meedias

> **Juhend:** Asenda kõik nurksulgudes vormid oma sisuga enne esitamist. Kustuta see juhendrida.

## Äriküsimus

Geopoliitiliste kriiside ja nendega seotud isikute kajastatuse osakaal ning temaatiline jaotus Eesti meediamaastikul ERR-i ja Äripäeva uudistevoogude näitel.

**Mõõdikud:**

1. Millise osakaalu kogu meediamahtudest moodustavad sihtriikidega (USA, Iraan, Iisrael, Ukraina, Venemaa) ja nendega seotud isikutega seonduvad uudised ERR-i ning Äripäeva päeva lõikes. Kogume valimi märksõnu nagu "USA, Trump, Iraan ... jne." Loeme kokku uudised, mis päevas sisaldavad neid sõnu ja vaatame kogusuhet päevastesse uudistesse.
2. Millistes temaatilistes kategooriates ja rubriikides nimetatud meediakanalid antud geopoliitilisi konflikte kajastavad? Uudistel on olemas kategooriad. Grupeerime ülalnimetatud märksõnadega uudised neisse kategooriatesse.

## Arhitektuur

```mermaid
flowchart TD
    RSS1["ERR RSS voog"]
    RSS2["Äripäev RSS voog"]
    AIRFLOW["Apache Airflow"]

    RSS1 -->|HTTPS| LAMBDA["AWS Lambda"]
    RSS2 -->|HTTP| LAMBDA["AWS Lambda"]
    LAMBDA --> RDS[("Amazon RDS PostgreSQL")]
    AIRFLOW -->RDS
    RDS --> AIRFLOW

    RDS --> METABASE[("Metabase")]

    %% Stiiliklassid ja teemad
    classDef allikas fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,color:#01579B;
    classDef lambda fill:#FFE0B2,stroke:#F57C00,stroke-width:2px,color:#E65100;
    classDef andmed fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#1B5E20;
    classDef airflow fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#4A148C;
    classDef metabase fill:#FCE4EC,stroke:#E91E63,stroke-width:2px,color:#880E4F;

    %% Klasside omistamine elementidele
    class RSS1,RSS2 allikas;
    class LAMBDA lambda;
    class RDS andmed;
    class METABASE metabase;
    class AIRFLOW airflow;

```

Täpsem joonis ja kirjeldus: [`docs/arhitektuur.md`](docs/arhitektuur.md)

## Andmestik

| Allikas | Tüüp | Ajas muutuv? | Roll |
|---------|------|--------------|------|
| [ERR RSS](https://www.err.ee/rss) | RSS | Jah, iga tund | Põhiandmevoog |
| [Äripäev RSS](http://feeds.feedburner.com/aripaev-rss) | RSS | Jah, iga tund  | Põhiandmevoog |

## Stack

| Komponent | Tööriist | Kirjeldus |
|-----------|---------|-----------|
| Sissevõtt (Extract) | AWS Lambda | Tõmbab RSS voo ja salvestab toore XML sisu `bronze.raw` tabelisse |
| Transformatsioon (Transform & Load) | Airflow (Python & SQL) | Eraldi DAG-id kummallegi allikale (ERR ja Äripäev), loevad `bronze` kiht ja kirjutavad `silver` kihti |
| Andmehoidla | Amazon RDS PostgreSQL | Medaljonarhitektuur (bronze -> silver -> gold) |
| Näidikulaud | Metabase | Ärianalüütika ja visuaalid |
| Orkestreerimine | Airflow | Käivitab transformatsiooni (hetkel testimisel, kulude säästmiseks käsitsi või tunnisel graafikul) |

## Käivitamine

```bash
# 1. Klooni repo ja liigu kausta
git clone <repo-url>
cd <projekti-kaust>

# 2. Kopeeri keskkonnamuutujad
cp .env.example .env
# Muuda .env failis paroolid ja muud seaded vastavalt vajadusele

# 3. Käivita teenused
docker compose up -d --build
```

Airflow (kui kasutatakse): http://localhost:8080 (kasutaja: airflow / parool: airflow)
Näidikulaud: http://localhost:[PORT]

## Saladused ja konfiguratsioon

Kõik saladused (paroolid, API võtmed, andmebaasi URL-id) on `.env` failis. Repos on ainult `.env.example`, mis näitab vajalike muutujate struktuuri ilma tegelike väärtusteta. Päris `.env` faili ei tohi GitHubi panna - see on `.gitignore`-s.

Vajalikud muutujad:

| Muutuja | Tähendus | Näide |
|---------|----------|-------|
| `DB_PASSWORD` | PostgreSQL parool | (saladus) |
| `[teised]` | ... | ... |

## Andmevoog lühidalt

1. **Sissevõtt (Extract)** — AWS Lambda funktsioonid tõmbavad regulaarselt ERR ja Äripäeva RSS-vooge ning lisavad need unikaalsuse kontrolliga (MD5 räsi) `bronze.raw` tabelisse. Kuna see on serverless ja odav, saab seda jooksutada pidevalt.
2. **Laadimine & Transformatsioon (Transform & Load)** — Airflow eraldiseisvad DAG-id (`transform_err_bronze_to_silver` ja `transform_aripaev_bronze_to_silver`) loevad toorandmeid skeemist `bronze`, viivad läbi transformatsioonid, filtreerivad lubamatud kategooriad ning kirjutavad tulemused `silver.news` tabelisse. Kulude kokkuhoiuks käivitatakse neid vajadusel käsitsi või korra tunnis (säästes EC2 tööaega).
3. **Inkrementaalsus** — Airflow jälgib viimati töödeldud rea ID-d (`latest_bronze_id`) tabelis `silver.news_incremental`, tagades, et igal käivitamisel töödeldakse vaid uusi toorandmeid.
4. **Testimine** — Andmekvaliteedi testid kontrollivad andmete terviklikkust.
5. **Näidikulaud** — Metabase teeb päringuid `silver` (ja hiljem `gold`) kihi pealt äriküsimustele vastamiseks.

## Andmekvaliteedi testid

Projekt kontrollib järgmist:

1. [Test 1 - *]
2. [Test 2 - *]
3. [Test 3 - *]
[Lisa rohkem, kui sul on]

Testide tulemused: [kuhu salvestatakse / kuidas vaadata]

## Projekti struktuur

```
.
├── README.md
├── compose.yml
├──
├── .env.example
├── .gitignore
├── docs/
│   ├── arhitektuur.md      ← nädal 1 väljund
│   └── progress.md         ← nädal 2 väljund
└── ...                     ← ülejäänud projektifailid
```

## Kokkuvõte, puudused ja võimalikud edasiarendused

**Kokkuvõte:**
- [Loetle, mis on lõpule viidud, mis töötab hästi]

**Puudused:**
- [Loetle ausalt, mis jäi tegemata - see ei mõjuta hinnet negatiivselt, vaid aitab hinnata]

**Mis edasi:**
- [Mida tahaksid edasi teha, kui aega oleks rohkem]

## Meeskond

| Nimi | Roll |
|------|------|
| Kaido Kariste | AWS teenused, seade |
| Allar Lääne | Näidikulaud ja visuaalid |
| Laurynas Matušaitis | Kvaliteedi omanik |
| Arno Pilvar | Transformatsioonid, lambdad |
