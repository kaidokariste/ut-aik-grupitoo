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

![image](./ut-kursuse-arhitektuur.png)

> Täpsusta diagrammi vastavalt oma projektile — lisa rohkem andmeallikaid, mudeleid või teenuseid.

## Andmebaasi kihid

| Kiht | Roll |
|------|------|
| `bronze` | Hoiab allika andmeid töötlemata kujul. |
| `silver` | Hoiab transformeeritud ja ärilogikat sisaldavaid tabeleid. |
| `gold` | Puhastatud, rikastatud andmestik. |

## Andmebaasi olem-seose mudel (ERD)

```mermaid
erDiagram
    "silver.news" {
        BIGINT id PK
        VARCHAR source
        TIMESTAMP_TZ news_dtime
        VARCHAR category
        VARCHAR title
        TEXT description
        VARCHAR link
    }
    "silver.news_incremental" {
        VARCHAR(10) source
        TIMESTAMPTZ latest_news_dtime
    }
    "silver.keywords" {
        TEXT keyword PK
        BOOLEAN wanted
    }
```

## Tööjaotus

| Roll | Vastutus | Täitja |
|------|----------|--------|
| Andmeallika omanik | Kirjutab sissevõtu loogika, hoiab API-t töös | Kaido Kariste |
| Transformatsioonide omanik | Kirjutab mart kihi mudelid ja mõõdikute arvutuse | Arno Pilvar |
| Kvaliteedi omanik | Kirjutab testid ja vaatab läbi ebaõnnestunud kontrollid | Laurynas Matušaitis |
| Näidikulaua omanik | Ehitab näidikulaua ja seob selle äriküsimusega | Allar Lääne |

## Riskid

| Risk | Mõju | Maandus |
|------|------|---------|
| Risk 1 - Uudistevoo URL-i liigutatakse | Airflow DAG peaks minema katki | Kasutaks "One failed" dagi |
| Risk 2 - Uudistevoo struktuur muutub | DAG hakkab saama tühje tulemusi | NOT NULL piirangud andmebaasis |
| Risk 3 - Sama uudis mitmes kategoorias | Mõned märksõnad hakkavad võimenduma | Enne dashboardi unikaalsus läbi SQL.  |

## Privaatsus ja turve

Kõik andmed on avalikud uudised.
