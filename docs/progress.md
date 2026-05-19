# Edenemisraport

> **Juhend:** See fail on projektitöö teise nädala väljund. Uuenda lühidalt iga esitamise eel. Kustuta see juhendrida.

## Mis on valmis

- [ ] AWS konto on loodud
- [ ] Andmeid saadakse allikast kätte
- [ ] Andmed laetakse `silver` kihti
- [ ] Vähemalt üks transformatsioon toimib
- [ ] Vähemalt üks näidikulaud on nähtaval
- [ ] Vähemalt üks andmekvaliteedi test läbib

[Täpsusta lühidalt, mis täpselt valmis on]

## Järgmised sammud

- AWS konto loomine
- EC2 instantsi seadistamine Airflow jooksutamiseks
- Docker Compose abil Airflow ülesseadmine
- _Silver_ kihi andmemudel ja inkrementaalsustabel 
- Esialgne python script, mis
    - Extract - vajalike väljade eraldamine RSS XML-st
    - Transform - ajavööndite ja kuupäevaformaatide teisendamine ISO standardisse
    - Load - Inkrementaalne laadimine _Silver_ kihi tabelisse
- Airflow DAGi kokkupanek ja CRON graafik.
- Metabase ülesseadmine Docker Compose abil
- Näidikulaua koostamine
- Andmekvaliteedi kontroll dubleerivate uudiste leidmiseks

## Mis takistab

- "Praegu pole blokeerivaid probleeme"

## Kontrollpunkt

Käsk, millega saab kontrollida, et töövoog töötab:

```bash
# [Lisa siia käsk, mis näitab, et andmed liiguvad allikast näidikulauani]
# Näiteks:
docker compose exec pipeline python scripts/run_pipeline.py check
```

Oodatav tulemus: [Kirjelda, mida töötav süsteem väljastab]
