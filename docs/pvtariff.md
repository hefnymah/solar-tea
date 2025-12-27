VESE - Verband unabhängiger Energieerzeuger, eine Fachgruppe der SSES
Aarbergergasse 21, 3011 Bern, [http://www.vese.ch,](http://www.vese.ch,) Tel. 031 371 80 00, E-Mail info@vese.ch

# pvtarif API Interface

## 1.Einleitung

Es werden zwei API-Calls zur Verfügung gestellt.

```
1) Abfrage der Gemeinden: mittels der BFS-Gemeindenummer “idofs“ kann eine Liste
alle in einer Gemeinde tätigen EWs ermittelt werden
```
```
2) Abfrage der Tarifdaten eines EWs, mit Hilfe der ElCom-Nummer „nrElcom“ oder der
Unternehmens-Identifikationsnummer (UID) des EWs.
```
## 2.Lizenzschlüssel / API-Key

Zur Benutzung der API-Schnittstelle ist ein Key notwendig. Dieser kann kostenfrei bei VESE

(info@vese.ch) angefordert werden. Mit der Anforderung ist die unterzeichnete
Lizenzvereinbarung (Download:

[http://www.vese.ch/wp-content/uploads/pvtarif/pvtarif2/appPvMapExpert/pvtarif-map-expert-](http://www.vese.ch/wp-content/uploads/pvtarif/pvtarif2/appPvMapExpert/pvtarif-map-expert-)
data-de.html (de) und

[http://www.vese.ch/wp-content/uploads/pvtarif/pvtarif2/appPvMapExpert/pvtarif-map-expert-](http://www.vese.ch/wp-content/uploads/pvtarif/pvtarif2/appPvMapExpert/pvtarif-map-expert-)
data-fr.html (fr) ) mitzusenden.

## 3.Gemeindeabfrage

Die Gemeinde muss mit der offiziellen Gemeindenummer des Bundesamts für Statistik BFS

identifiziert werden. Alle Erklärungen zu dieser Gemeindenummer finden sich auf folgender
Webseite: [http://www.communes.bfs.admin.ch](http://www.communes.bfs.admin.ch)

Die innerhalb der Gemeinde tätigen EWs sind von pvtarif aufgrund folgender Datensätze der
Elcom bestimmt worden:

Webseite: [http://www.elcom.admin.ch/elcom/de/home/themen/strompreise/tarif-rohdaten-](http://www.elcom.admin.ch/elcom/de/home/themen/strompreise/tarif-rohdaten-)
verteilnetzbetreiber.html


```
Aufruf Gemeindeabfrage
URL: https://opendata.vese.ch/pvtarif/api/getData/muni
```
```
Parameter Format Bemerkung
```
```
idofs String „XXXX“ Gemeindenummer des
Bundesamts für Statistik BFS
```
```
licenseKey String „ABCDEF...123456“ der von VESE mitgeteilte
Lizenzschlüssel
```
```
Beispiel Aufruf Gemeinde Aadorf (Gemeindenummer idofs: 4551)
https://opendata.vese.ch/pvtarif/api/getData/muni?idofs=4551&licenseKey=your_license_key
```
```
Antwort:
```
```
Parameter Format Bemerkung
```
```
valid String true, wenn Antwort gültig,
false sonst
```
```
evus Array von EVU-Objekten alle EVUs, welche in dieser
Gemeinde tätig sind
```
```
EVU-Objekt (innerhalb der Antwort)
```
```
Parameter Format Bemerkung
```
```
nrElcom String die ElCom-Id des EVU
```
```
Name String der Name des EVUs
```
```
idofs String BFS-Gemeindenummer
```
```
PLZ String die Postleitzahl (PLZ4) der
Gemeinde
```
```
Gemeinde String der Gemeindename
```
```
uid String Unternehmens-Identifikations-
nummer UID, ist der
Nachfolger der ElCom-ID
```
```
Hinweis zur Unternehmens-Identifikationsnummer UID: sollte ein EVU keine solche Nummer
haben, so wird im Feld "uid" eine erzeugte Unternehmens-Identifikationsnummer im Format
"CHE-999.999.nrElcom" zurückgegeben
```
```
Beispiel Antwort (Gemeinde Aadorf, idofs: 4551, total 3 EWs)
```
1. {valid: true,...}
    1. evus:[{"nrElcom": "544", Name: "EW Aadorf", idofs: "4551", PLZ: "8355", Gemeinde:
       "Aadorf",uid:"CHE-108.953.536"},...]


1. 0 :{"nrElcom": "544", Name: "EW Aadorf", idofs: "4551", PLZ: "8355",
    Gemeinde: "Aadorf"}
       1. Gemeinde:"Aadorf"
       2. Name:"EW Aadorf"
       3. PLZ:" 8355 "
       4. idofs:" 4551 "
       5. "nrElcom":" 544 "
       6. "uid":"CHE-108.953.536"
2. 1 :{"nrElcom": "142", Name: "Elektra Häuslenen", idofs: "4551", PLZ: "8355",
    Gemeinde: "Aadorf", uid:"CHE-108.226.494"}
       1. Gemeinde:"Aadorf"
       2. Name:"Elektra Häuslenen"
       3. PLZ:" 8355 "
       4. idofs:" 4551 "
       5. "nrElcom":" 142 "
       6. "uid":"CHE-108.226.494"
3. 2 :{"nrElcom": "208", Name: "Elektra-Genossenschaft Guntershausen",
    idofs: "4551", PLZ: "8355",...}
       1. Gemeinde:"Aadorf"
       2. Name:"Elektra-Genossenschaft Guntershausen"
       3. PLZ:" 8355 "
       4. idofs:" 4551 "
       5. "nrElcom":" 208 "
       6. "uid":"CHE-999.999.208"
2. valid:true

## 4.EW-Abfrage

Durch diese Abfrage können alle von pvtarif für ein EW für ein vorgegebenes Jahr erhobenen

Daten abgerufen werden.
Das EW muss durch die ElCom-Nummer oder alternativ die Unternehmens-

Identifikationsnummer UID identifiziert werden.
pvtarif.ch stellt die Daten jahresweise zur Verfügung. 2017 ist das erste Jahr, für welches das

API Interface implementiert ist, die Jahre 2015 und 2016 können nur über die Internetseite
pvtarif.ch konsultiert werden.

**Aufruf**
URL: https://opendata.vese.ch/pvtarif/api/getData/evu

```
Parameter Format Bemerkung
```
```
evuId String „XXX“ die ElCom-ID oder
Unternehmens-
Identifikationsnummer UID
des EWs
```
```
year String „YY“ das Jahr, zweistellig, für
welches die Tarifdaten
zurückgegeben werden
```

```
sollen
```
```
licenseKey String der von VESE mitgeteilte
Lizenzschlüssel
```
**Beispiel Aufruf für Elektrizitätswerk des Kantons Zürich EKZ, Elcom-Nummer: 486**

https://opendata.vese.ch/pvtarif/api/getData/evu?
evuId=486&year=17&licenseKey=your_license_key

**Alternative Abfrage mit Unternehmens-Identifikationsnummer:**
https://opendata.vese.ch/pvtarif/api/getData/evu?

evuId=CHE-108.954.688&year=17&licenseKey=your_license_key

**Antwort:**

```
Parameter Format Bemerkung
```
```
valid String true/false
```
```
nrElcom String Elcom Nummer
```
```
uid
```
```
String Unternehmens-
Identifikationsnummer UID
```
```
nomEw EW Name
```
```
link Link auf Homepage EW
```
```
tarif1 Link auf Tarifblatt 1
```
```
tarif2 Link auf Tarifblatt 2
```
```
tarif3 Link auf Tarifblatt 3
```
```
explText
```
```
Erklärungstext betreffend
speziellen für die PV
wichtigen Regelungen
```
```
counterCost
```
```
Kosten eines einfachen
Zählers (CHF/Monat)
```
```
loadCurveCost
```
```
Kosten Lastgangmessung
(CHF/Monat)
```
```
nbrPowerCat
```
```
Anzahl Leistungsklassen bei
den Vergütungen (minimal
1, maximal 4)
```
```
power
```
```
Anfangsleistung der ersten
Leistungsstufe in kWp (fast
immer 0 kWp)
```
```
energy
```
```
Tarif für die Energie in der
1sten Leistungsklasse in
Rp/kWh, falls Hoch/Nieder-
oder Saisontarif, wird hier
```

```
der berechnete effektive
Jahrsdurchschnittstarif einer
PV-Anlage angegeben
```
eco

```
Tarif für den HKN in der
1sten Leistungsklasse in
Rp/kWh
```
energyAuto

```
Tarif für die Energie in der
1sten Leistungsklasse für
Eigenverbraucher in
Rp/kWh
```
ecoAuto

```
Tarif für den HKN in der
1sten Leistungsklasse für
Eigenverbraucher in
Rp/kWh
```
power

```
Beginn der 2ten
Leistungskategorie der
Vergütung in kWp
```
energy2 Gleich wie oben ...

eco

energyAuto

ecoAuto

power

```
Beginn der 3ten
Leistungskategorie der
Vergütung in kWp
```
energy3 Gleich wie oben ...

eco

energyAuto

ecoAuto

power

```
Oberste Leistung der 3ten
Leistungskategorie
```
htnt

```
y, falls Unterscheidung
Hoch/Niedertarif bei der
Vergütung
```
stwt

```
y, falls Unterscheidung
Sommer/Wintertarif bei der
Vergütung
```
ecoIncl

```
y, falls der HKN in der
Vergütung der Energie
inbegriffen ist (obligatorische
Übertragung)
```

autot

```
y, falls Unterscheidung
Vergütung für reine
Produktion und Vergütung
Eigenverbraucher
```
energy1_bfe

```
y, falls sich der Energietarif
auf den sog. BFE-Marktpreis
beruft
```
energy1_ht

```
Vergütung Energie Hochtarif
Ganzjahr oder Sommer
(Rp/kWh)
```
energy1_nt

```
Falls Niedertarif, Vergütung
Energie Niedertarif Ganzjahr
oder Sommer
(Rp/kWh)
```
energy1_wht

```
Falls Wintertarif, Wintertarif
Hochtarif
```
energy1_wnt

```
Falls Wintertarif und
Niedertarif, Wintertarif
Niedertarif
```
energyAuto1_bfe

```
Wie oben, jedoch für
Eigenverbraucher, falls
Unterschied zu reinen
Produzenten
```
energyAuto1_ht ....

energyAuto1_nt

energyAuto1_wht

energyAuto1_wnt

energy2_bfe

```
Wie oben, aber für
Leistungskategorie 2
```
energy2_ht .....

energy2_nt

energy2_wht

energy2_wnt

energyAuto2_bfe

energyAuto2_ht

energyAuto2_nt

energyAuto2_wht


energyAuto2_wnt

energy3_bfe

```
Wie oben, aber für
Leistungskategorie 3
```
energy3_ht .....

energy3_nt

energy3_wht

energy3_wnt

energyAuto3_bfe

energyAuto3_ht

energyAuto3_nt

energyAuto3_wht

energyAuto3_wnt

ht_mofr_on

```
Beginn Hochtarif Montag
bis Freitag (0..24)
```
ht_mofr_off

```
Ende Hochtarif Montag bis
Freitag (0..24)
```
ht_sa_on

```
Beginn Hochtarif Samstag
(0..24)
```
ht_sa_off

```
Ende Hochtarif Samstag
(0..24)
```
ht_su_on

```
Beginn Hochtarif Sonntag
(0..24)
```
ht_su_off

```
Ende Hochtarif Sonntag
(0..24)
```
neg

```
y, falls negative
Gegebenheit betreffend
Photovoltaik
```
neg_text

```
Textbeschreibung des
negativen Effekts
```
pos

```
y, falls positive Gegebenheit
betreffend Photovoltaik
```
pos_text

```
Textbeschreibung des
positiven Effekts
```
leist

```
y, falls Leistungstarif für
Eigenverbraucher
```

```
leist_power
```
```
Schwelle in kVA, ab welcher
der Leistungstarif einsetzt
(meistens 10 kVA)
```
```
leist_tax
```
```
Leistungstarif in
CHF/kVA/Monat
```
**Beispiel Antwort EKZ 2017:**

{"valid":true,
"nrElcom":"486",
"uid":"CHE-108.954.688",
"nomEw":" Elektrizitätswerke des Kantons Zürich EKZ",
Name
"link":"www.ekz.ch", Link auf Webseite
"tarif1":" [http://www.ekz.ch/content/dam/ekz-internet/private/Kaufen/EKZ-](http://www.ekz.ch/content/dam/ekz-internet/private/Kaufen/EKZ-)
Tarifsammlung-2017.pdf",
Link auf Tarifblatt
"tarif2":"", keine weiteren Tarifblätter erfasst
"tarif3":"",
"explText":"", keine besonderen Bemerkungen
"counterCost":"0", Zählerkosten = 0
"loadCurveCost":"25", Lastgangkosten = 25 CHF/Monat
"nbrPowerCat":"2", 2 Leistungskategorien
"power1":"0", Beginn 1ste Leistungklasse Vergütung bei 0 kVA
"energy1":"6.23", Vergütung Energie 1ste Leistungsklasse Rp/kWh
"eco1":"0", Vergütung HKN 1ste Leistungsklasse
"energyAuto1":"6.23", Vergütung Energie Eigenverbracher 1ste LK
"ecoAuto1":"0", Vergütung HKN Eigenverbracher 1ste LK
"power2":"150", Beginn 2te Leistungklasse bei 150 kVA
"energy2":"5.15", Vergütung Energie 2ste Leistungsklasse
"eco2":"0", .....
"energyAuto2":"5.15",
"ecoAuto2":"0",
"power3":"1000", Ende der Leistungsklasse 2 bei 1000 kVA
"energy3":"",
"eco3":"",
"energyAuto3":"",
"ecoAuto3":"",
"power4":"",
"htnt":"y", Hoch-Niedertarif
"stwt":"", Kein Sommer/Wintertarif
"ecoIncl":"", HKN ist nicht im Energietarif integriert
"autot":"", Kein spezieller Eigenverbrauchstarif
"energy1_bfe":"", Kein Bezug auf den BFE-Marktpreis für LK
"energy1_ht":"6.5", LK1: Hochtarif 6.5 Rp/kWh
"energy1_nt":"5.3", LK1: Niedertaif 5.3 Rp/kWh
"energy1_wht":"",
"energy1_wnt":"",
"energyAuto1_bfe":"",
"energyAuto1_ht":"",
"energyAuto1_nt":"",
"energyAuto1_wht":"",
"energyAuto1_wnt":"",
"energy2_bfe":"",
"energy2_ht":"5.3",
"energy2_nt":"4.3",
"energy2_wht":"",
"energy2_wnt":"",
"energyAuto2_bfe":"",


"energyAuto2_ht":"",
"energyAuto2_nt":"",
"energyAuto2_wht":"",
"energyAuto2_wnt":"",
"energy3_bfe":"",
"energy3_ht":"",
"energy3_nt":"",
"energy3_wht":"",
"energy3_wnt":"",
"energyAuto3_bfe":"",
"energyAuto3_ht":"",
"energyAuto3_nt":"",
"energyAuto3_wht":"",
"energyAuto3_wnt":"",
"ht_mofr_on":"7", Tarifzeiten
"ht_mofr_off":"20",
"ht_sa_on":"7",
"ht_sa_off":"13",
"ht_su_on":"0",
"ht_su_off":"0",
"neg":"", keine negativen Bemerkungen
"neg_text":"",
"pos":"", keine positiven Bemerkungen
"pos_text":"",
"leist":"", keine Leistungstaxen
"leist_power":"",
"leist_tax":""}

## 5.Fragen:

info@pvtarif.ch

## 6.Version

### Datum Version Wer Änderungen

### 06.05.2025 03 W. Sachs Beschreibung um Unternehmens-

### Identifikationsnummer UID erweitert



