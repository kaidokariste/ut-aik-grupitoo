# Arhitektuur

## Äriküsimus

Geopoliitiliste kriiside ja nendega seotud isikute kajastatuse osakaal ning temaatiline jaotus Eesti meediamaastikul ERR-i ja Äripäeva uudistevoogude näitel.

## Mõõdikud

1. Millise osakaalu kogu meediamahtudest moodustavad sihtriikidega (USA, Iraan, Iisrael, Ukraina, Venemaa) ja nendega seotud isikutega seonduvad uudised ERR-i ning Äripäeva päeva lõikes. Kogume valimi märksõnu nagu "USA, Trump, Iraan ... jne." Loeme kokku uudised, mis päevas sisaldavad neid sõnu ja vaatame kogusuhet päevastesse uudistesse.
2. Millistes temaatilistes kategooriates ja rubriikides nimetatud meediakanalid antud geopoliitilisi konflikte kajastavad? Uudistel on olemas kategooriad. Grupeerime ülalnimetatud märksõnadega uudised neisse kategooriatesse.


## Andmeallikad

| Allikas | Tüüp | Ajas muutuv? | Roll |
|---------|------|--------------|------|
| [ERR RSS](https://www.err.ee/rss) | RSS | Jah, iga tund | Põhiandmevoog |
| [Äripäev RSS](http://feeds.feedburner.com/aripaev-rss) | RSS | Jah, iga tund  | Põhiandmevoog |

## Andmevoog

```mermaid
flowchart TD
    subgraph ALLIKAD["Uudistevood (Välissüsteemid)"]
        RSS1["ERR RSS voog"]
        RSS2["Äripäev RSS voog"]
    end

    subgraph INGEST["AWS Cloud"]
        LAMBDA1["AWS Lambda: rss-fetcher-err"]
        LAMBDA2["AWS Lambda: rss-fetcher-aripaev"]
        subgraph TRANS["AWS EC2 (Apache Airflow)"]
            AIRFLOW["Airflow: <br>transform_err_bronze_to_silver<br>transform_aripaev_bronze_to_silver"]
        end
            subgraph STORAGE["AWS RDS PostgreSQL"]
        BRONZE[("bronze.raw")]
        SILVER_NEWS[("silver.news")]
        SILVER_INC[("silver.news_incremental")]
        KEYWORDS[("silver.keywords")]
        end
    end

    subgraph VISUAL["Ettevõtte sisevõrk"]
        METABASE["Metabase<br>Dashboardid ja analüüs"]
    end

    RSS1 -->|HTTPS| LAMBDA1
    RSS2 -->|HTTP| LAMBDA2
    LAMBDA1 -->|INSERT toore XML + MD5 räsi| BRONZE
    LAMBDA2 -->|INSERT toore XML + MD5 räsi| BRONZE

    BRONZE -->|Loe uued read| AIRFLOW
    AIRFLOW -->|INSERT parsitud artiklid| SILVER_NEWS
    AIRFLOW -->|UPDATE viimased ID-d ja ajad| SILVER_INC

    SILVER_NEWS --> METABASE
    KEYWORDS --> METABASE

    %% Stiiliklassid ja teemad
    classDef allikas fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,color:#01579B;
    classDef lambda fill:#FFE0B2,stroke:#F57C00,stroke-width:2px,color:#E65100;
    classDef andmed fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#1B5E20;
    classDef airflow fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#4A148C;
    classDef metabase fill:#FCE4EC,stroke:#E91E63,stroke-width:2px,color:#880E4F;

    %% Klasside omistamine elementidele
    class RSS1,RSS2 allikas;
    class LAMBDA1,LAMBDA2 lambda;
    class BRONZE,SILVER_NEWS,SILVER_INC,KEYWORDS andmed;
    class AIRFLOW airflow;
    class METABASE metabase;
    
    %% Subgraphide stiilid
    style ALLIKAD fill:#F4F8FA,stroke:#B0BEC5,stroke-width:1px,stroke-dasharray: 5 5,color:#37474F
    style INGEST fill:#FFF8F1,stroke:#FFE0B2,stroke-width:1px,stroke-dasharray: 5 5,color:#E65100
    style STORAGE fill:#F4FAF5,stroke:#C8E6C9,stroke-width:1px,stroke-dasharray: 5 5,color:#1B5E20
    style TRANS fill:#FAF5FB,stroke:#E1BEE7,stroke-width:1px,stroke-dasharray: 5 5,color:#4A148C
    style VISUAL fill:#FFF5F8,stroke:#F8BBD0,stroke-width:1px,stroke-dasharray: 5 5,color:#880E4F
```


Projekti andmevoog on jagatud kaheks eraldiseisvaks etapiks (Separation of Concerns):

1. **Sissevõtt (Extract):** AWS Lambda funktsioonid pärinevad RSS voogudest andmeid ja salvestavad toore XML-i otse RDS andmebaasi `bronze.raw` tabelisse. Kuna Lambda on serverless ja tasuta limiidid/kulud on minimaalsed, saab seda jooksutada tihedalt. See tagab, et me ei kaota andmeid ka siis, kui Airflow server on maas.
2. **Transformatsioon (Transform & Load):** Airflow DAG-id (`transform_err_bronze_to_silver` ja `transform_aripaev_bronze_to_silver`) loevad toorandmeid skeemist `bronze`, parsivad XML-i, puhastavad andmed ja laadivad need `silver.news` tabelisse. Kuna EC2 instantsi jooksutamine Airflow jaoks on kallis, hoitakse Airflow-d töös vaid vajadusel (nt testimise ajal ja käsitsi käivitamisel või tunnisel graafikul).

Inkrementaalseks laadimiseks kasutatakse `latest_bronze_id` veergu `silver.news_incremental` tabelis, et vältida juba töödeldud ridade uuesti parsimist.

## Andmebaasi kihid

| Kiht | Roll |
|------|------|
| `bronze` | Hoiab allika toorandmeid töötlemata kujul (`bronze.raw` tabelis). |
| `silver` | Hoiab transformeeritud, parsitud ja filtreeritud andmeid (`silver.news`, stoppsõnu/märksõnu `silver.keywords`). |
| `gold` | Puhastatud, rikastatud andmestik (agregeeritud vaated ja tabelid ärianalüütika jaoks). |

## Praegune andmebaasi olem-seose mudel (ERD)

```mermaid
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
        VARCHAR(10) source
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

## Tööjaotus

| Roll | Vastutus | Täitja |
|------|----------|--------|
| Andmeallika omanik | Kirjutab sissevõtu loogika, hoiab API-t töös | Kaido Kariste |
| Transformatsioonide omanik | Kirjutab mart kihi mudelid ja mõõdikute arvutuse | Arno Pilvar |
| Kvaliteedi omanik | Kirjutab testid ja vaatab läbi ebaõnnestunud kontrollid | Laurynas Matušaitis |
| Näidikulaua omanik | Ehitab näidikulaua ja seob selle äriküsimusega | Allar Lääne |

*rollid on paindlikud ning muutuvad jooksvalt vastavalt vajadusele.

## Riskid

| Risk | Mõju | Maandus |
|------|------|---------|
| Risk 1 - Uudistevoo URL-i liigutatakse | Airflow DAG peaks minema katki | Kasutaks "One failed" dagi |
| Risk 2 - Uudistevoo struktuur muutub | DAG hakkab saama tühje tulemusi | NOT NULL piirangud andmebaasis |
| Risk 3 - Sama uudis mitmes kategoorias | Mõned märksõnad hakkavad võimenduma | Enne dashboardi unikaalsus läbi SQL.  |

## Privaatsus ja turve

Kõik andmed on avalikud uudised.
