from typing import Union
import requests
import datetime

from bs4 import BeautifulSoup


def extract_data(html: str) -> dict[str, Union[str, datetime.datetime]]:
    # Extrahiert Luft- und Wetteraten aus HTML-String
    soup = BeautifulSoup(html)

    # Content holen
    content = soup.find(id="contentpos")

    # Alle Tabellen im Inhalt suchen, die "Aktuelle Luftdaten beinhalten"
    tables = content.find_all(
        lambda tag: tag.name == "table" and "Aktuelle Luftdaten" in tag.text
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

        observation["last_update"] = last_update_as_datetime

    # Dictionary zurückgeben
    return observation


def download_html(website_url: str) -> str:
    return requests.get(website_url).text


src = download_html(
    "https://www.stadtklima-stuttgart.de/index.php?klima_messdaten_station_afu"
)
print(extract_data(src))
