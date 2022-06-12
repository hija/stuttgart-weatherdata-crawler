from typing import Union
import zoneinfo
import requests
import datetime
import json
import traceback


from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
from pathlib import Path


def extract_data(html: str) -> dict[str, Union[str, datetime.datetime]]:
    # Extrahiert Luft- und Wetteraten aus HTML-String
    soup = BeautifulSoup(html, "lxml")

    # Content holen
    content = soup.find(id="contentpos")

    # Alle Tabellen im Inhalt suchen, die "Aktuelle Wetterdaten beinhalten"
    tables = content.find_all(
        lambda tag: tag.name == "table" and "Aktuelle Wetterdaten" in tag.text
    )

    if len(tables) == 0:
        # Wir haben keine Tabellen gefunden --> Website wurde bearbeitet, unser Crawler funktioniert nicht mehr
        raise ValueError(
            "Tabelle mit Wetterdaten konnte nicht auf der Website gefunden werden"
        )
    else:
        # Ansonsten nehmen wir die erste Tabelle auf der Website die wir gefunden haben
        weathertable = tables[0]

        # Und suchen uns alle Zeilen raus
        weathertablerows = weathertable.find_all(
            lambda tag: tag.name == "tr" and tag.find("td", attrs={"align": "right"})
        )

        # Wir speichern die ausgelesenen Werte in einem Dictionary
        observation = dict()

        for weathertablerow in weathertablerows:
            # In jeder Zeile suchen wir jetzt die Spalten
            columns = weathertablerow.find_all("td")

            # Die erste Spalte ist das Attribut, z.B. "UV-Index"
            parameter_name = columns[0].text.strip()

            # Und die zweite Spalte ist der Wert, z.B. 1.64
            parameter_value = columns[1].text.strip()

            # Daten im Dictionary abspeichern
            observation[parameter_name] = parameter_value

        # Zuletzt holen wir uns noch den offiziellen Stand
        last_update_text = weathertable.find(
            lambda tag: tag.name == "td", attrs={"align": "center"}
        ).b.string

        # Den Text zu einem Datetime parsen, damit wir es besser abspeichern können
        last_update_as_datetime = datetime.datetime.strptime(
            last_update_text, "(Stand: %d.%m.%Y, %H:%M Uhr)"
        )

        observation["last_update"] = last_update_as_datetime.isoformat()

    # Dictionary zurückgeben
    return observation


def download_html(website_url: str) -> str:
    return requests.get(website_url).text


STATIONS = {
    "Stuttgart-Mitte (Amt für Umweltschutz)": {
        "url": "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_afu",
        "file": "s-mitte-umweltschutz.json",
    },
    "Stuttgart-Mitte (Schwabenzentrum)": {
        "url": "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_smz",
        "file": "s-mitte-schwabenzentrum.json",
    },
    "Stuttgart-Bad Cannstatt (Branddirektion)": {
        "url": "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_bd",
        "file": "s-bad-cannstatt-branddirektion.json",
    },
    "Stuttgart-Sillenbuch (Geschwister Scholl Gymnasium)": {
        "url": "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_gsg",
        "file": "s-sillenbuch-geschwister-scholl-gymnasium.json",
    },
    "Stuttgart-Mühlhausen (Hauptklärwerk)": {
        "url": "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_hkw",
        "file": "s-muehlhausen-hauptklaerwerk.json",
    },
    "Stuttgart-Vaihingen (Messfeld Uni)": {
        "url": "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_uni_vaih",
        "file": "s-vaihingen-messfeld-uni.json",
    },
}

if __name__ == "__main__":
    german_timezone = zoneinfo.ZoneInfo("Europe/Berlin")
    for stationname in STATIONS:
        station = STATIONS[stationname]
        try:
            website_src = download_html(station["url"])
            observation = extract_data(website_src)
        except Exception as e:
            observation = {"error": str(e)}
        observation["crawltime"] = datetime.datetime.now(german_timezone).isoformat()
        with open(Path("data") / station["file"], "a") as f:
            print(json.dumps(observation), file=f)
