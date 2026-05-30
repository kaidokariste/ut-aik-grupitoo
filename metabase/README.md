# Metabase — Näidikulaud

Metabase on avatud lähtekoodiga ärianalüütika tööriist, mida kasutatakse projekti näidikulauaks (dashboard). See jookseb Docker Compose abil EC2 instansis ja ühendub RDS PostgreSQL andmebaasiga uudiste analüüsimiseks.

## Arhitektuur

Metabase on paigaldatud Docker Compose abil kahe teenusega:

| Teenus | Pilt | Kirjeldus |
|--------|------|-----------|
| `db` | `postgres:14.22-trixie` | Metabase enda metaandmebaas |
| `metabase` | `metabase/metabase:v0.59.2` | Metabase rakendus |

Metabase ühendub **kahte** PostgreSQL andmebaasi:
1. **Oma metaandmebaas** (`db` teenus) — salvestab Metabase seaded, kasutajad, dashboardid
2. **RDS andmebaas** (`host.docker.internal` kaudu) — projekti uudiste andmed (`silver.news` tabel)

Võrguseaded:
- Metabase on kättesaadav pordil `${MB_PORT}` (vaikimisi 3000), seotud ainult `127.0.0.1`-ga
- Docker võrk: `172.16.200.0/24`, Metabase IP: `172.16.200.30`
- `host.docker.internal` kasutatakse RDS ühenduse jaoks

## Päringud (Queries)

Failis `metabase_queries.sql` on defineeritud järgmised päringud dashboardi jaoks:

### 1. Uudiste jaotus allika/kategooria järgi
Loendab unikaalsed pealkirjad allika, kategooria ja kuupäeva lõikes.

### 2. Maailmasündmuste jaotus kategooriate järgi
Kategoriseerib uudised riikide järgi (USA, Venemaa, Iraan, Hiina) pealkirja märksõnade alusel.

### 3. Top 10 kategooriad
Näitab kõige populaarsemaid uudiskategooriaid.

### 4. Top 10 märksõna
Analüüsib uudiste kirjeldusi, eemaldab stoppsõnad (`silver.keywords` tabelist) ja leiab kõige sagedamini esinevad sisukad sõnad.

### 5. Uudiste arv päevade lõikes
Aegrida unikaalsete uudiste arvust päevade kaupa.

### 6. Erinevate sündmuste kajastus meedias
Arvutab iga geopoliitilise teema (Ukraina sõda, USA, Iraani sõda, Hiina) osakaalu protsendina päevases uudistevoos. Kasutab `silver.keywords` tabeli märksõnu teemade tuvastamiseks.

### 7. Suuremad sündmused maailmas
Artiklite absoluutarv teemade ja päevade lõikes (sarnane eelmisele, kuid ilma protsendiarvutuseta).

## Käivitamine kohalikuks arenduseks

```bash
# 1. Kopeeri ja seadista keskkonnamuutujad
cp .env.example .env
# Muuda .env failis paroole vastavalt vajadusele

# 2. Käivita Metabase
docker compose up -d

# 3. Ava brauser
# http://localhost:3000
```

## Keskkonnamuutujad

| Muutuja | Kirjeldus | Vaikeväärtus |
|---------|-----------|-------------|
| `DB_NAME` | Metabase metaandmebaasi nimi | `metabase` |
| `DB_USER` | Metaandmebaasi kasutaja | `metabase` |
| `DB_PASSWORD` | Metaandmebaasi parool | `metabase` |
| `DB_DATA_DIR` | PostgreSQL andmekataloog | `/var/lib/postgresql/data` |
| `MB_PORT` | Metabase port | `3000` |
| `MB_JAVA_TIMEZONE` | Java ajavöönd | `Europe/Tallinn` |

## Failide struktuur

```
metabase/
├── docker-compose.yml     # Docker Compose konfiguratsioon
├── metabase_queries.sql   # Dashboardi SQL päringud
├── .env.example           # Keskkonnamuutujate näidis
└── README.md
```
