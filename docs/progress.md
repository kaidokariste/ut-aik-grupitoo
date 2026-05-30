# Edenemisraport

## Mis on valmis

- [X] AWS konto on loodud
- [X] Andmeid saadakse allikast kätte (ERR ja Äripäev RSS-vood)
- [X] Toorandmete `bronze` kihti laadimine AWS lambda funktsioonide abil
- [X] Vähemalt üks transformatsioon toimib (kuupäevade parsijad ja teemade filtreerimine)
- [X] Andmed laetakse `silver` kihti inkrementaalselt
- [X] Vähemalt üks näidikulaud on nähtaval (Metabase seadistatud)
- [X] Ülesannete eraldatus (Separation of Concerns): loodud eraldi transformatsiooni DAG-id mõlemale allikale (`transform_err_bronze_to_silver` ja `transform_aripaev_bronze_to_silver`)
- [ ] Vähemalt üks andmekvaliteedi test läbib

Andmevoog on otsast lõpuni käivitatav (allikast `bronze` kihti läbi Lambda ja sealt `silver` kihti ning näidikutabeleisse). Vanem monoliitne DAG on märgitud aegunuks (deprecated). Kuna Airflow EC2 instantsi pidev jooksutamine on kulukas, on hetkel lahendus testimisfaasis: odavad serverless Lambda funktsioonid koguvad pidevalt toorandmeid `bronze` kihti ja uued transformatsiooni DAG-id käivitatakse käsitsi või tunnisel graafikul.

Esimene visuaal:
![Sprint 2 visuaal](./visuaal1.png)

## Järgmised sammud (Sprint 3)

- Andmekvaliteedi testide lisamine (näiteks dubleerivate uudiste kontrolli).
- Visuaalide täiendamine ja viimistlemine Metabase'is.
- Andmemudeli dokumentatsiooni ja arhitektuuri jooniste täpsustamine.

## Mis takistab

- Praegu ei ole otseseid blokeerivaid probleeme.

## Kontrollpunkt

**Märkus infrastruktuuri kohta:** Projekti komponendid on hetkel hajutatud (Sissevõtt toimub AWS Lambda abil, andmed kogunevad AWS RDS PostgreSQL andmebaasi, Airflow asub AWS EC2 virtuaalmasinas ning Metabase asub sisevõrgus). Seetõttu ei ole projekti toimivust kolmandal osapoolel lokaalselt lihtne käivitada, samuti pole ühe käsuga ülesseadmine olnud eesmärgiks.

Kuna Airflow EC2 instantsi pidev üleval hoidmine on kulukas (AWS tasuta krediit saaks muidu enne kursuse lõppu otsa), on Airflow ja selle uued transformatsiooni DAG-id hetkel käivitamisel vastavalt vajadusele. Kogu toorandmete sissevõtt (Lambda -> `bronze.raw`) töötab aga pidevalt ja efektiivselt.

Andmevoo otsast-lõpuni toimimise tõestuseks on esitatud ülaltoodud väljavõte Metabase'ist. Vajadusel saame andmebaasi sisu täiendavalt demonstreerida.
