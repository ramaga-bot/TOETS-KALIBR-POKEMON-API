"""Dit script is bedoeld om Pokemon-gegevens op te halen, te verwerken en weg te schrijven naar JSON en CSV."""

import csv
import json
import os
import sys
import time
from operator import truediv

import requests

# ---------------------------------------------------------------- instellingen
BASIS_URL = "https://pokeapi.co/api/v2"
STANDAARD_AANTAL = 20
MAX_AANTAL = 1000

TIMEOUT = (5, 15)  # seconden
MAX_POGINGEN = 3
WACHT_BASIS = 2  # seconden
HERSTELBARE_CODES = {429, 500, 502, 503, 504}

FOUTMELDINGEN = {
    401: "Geen toegang (401): controleer je API-sleutel.",
    403: "Geen toegang (403): controleer je API-sleutel.",
    404: "Niet gevonden (404): controleer de URL.",
}

UITVOER_CSV = "pokemon.csv"
UITVOER_JSON = "pokemon.json"


class ApiFout(Exception):
    """Eigen foutklasse met een leesbare melding voor de gebruiker."""

#---Sleutel (API-KEY)
"""Zorgen ervoor dat de key wordt opgehaald en gebruikt"""

def haal_api_sleutel():
    return os.environ.get("API_KEY")

def maak_headers(sleutel):
    return {"Authorization": f"Bearer {sleutel}"} if sleutel else {}

#---Ophalen
def controleer_status(response):
    if response.status_code in HERSTELBARE_CODES:
        return False
    if response.status_code in FOUTMELDINGEN:
        raise ApiFout(FOUTMELDINGEN[response.status_code])
    if not response.ok:
        raise ApiFout(f"Onverwachte statuscode {response.status_code}.")
    return True

def lees_json(response :{json} ):
    try:
        return response.json()
    except ValueError:
        raise ApiFout("De API gaf geen geldige JSON terug")

def wacht_voor_nieuwe_poging(poging ):
    wacht= WACHT_BASIS *2 ** (poging - 1)
    print(f"Poging mislukt. Opnieuw proberen")

def haal_json_op(url, headers=None, params=None):
    laatste_fout = None

    for poging in range(1, MAX_POGINGEN + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            if controleer_status(response):
                return lees_json(response)
            laatste_fout = f"Server gaf statuscode {response.status_code}"
        except requests.Timeout:
            laatste_fout = "De API reageert te traag (timeout)"
        except requests.ConnectionError:
            laatste_fout = "Geen verbinding met de API (connection error)"
        except (requests.exceptions.InvalidURL,
                requests.exceptions.InvalidSchema):
            raise ApiFout("De URL is ongeldig")
        except requests.RequestException as e:
            raise ApiFout("Onbekende netwerkfout")
        if poging < MAX_POGINGEN:
            wacht_voor_nieuwe_poging(poging, laatste_fout)

    raise ApiFout(f"Ophalen mislukt na max aantal pogingen")

def haal_pokemon_lijst(aantal, headers=None):
    data = haal_json_op(f"{BASIS_URL}/pokemon", headers=headers,
                        params={"limit": aantal, "offset": 0})
    resultaten = data.get("results") if isinstance(data, dict) else None
    if not isinstance(resultaten, list):
        raise ApiFout("Onbekende pokemon_lijst")
    return resultaten

def haal_pokemon_details(lijst , headers=None):
    details = []
    totaal = len(lijst)

    for nummer, item in enumerate(lijst, start=1):
        try:
            details.append(haal_json_op(f"{BASIS_URL}/pokemon/{nummer}", headers=headers,))
        except (ApiFout, KeyError, TypeError) as e:
            print('Er ging iets fout probeer A.U.B opnieuw')

    print()
    return details

#---verwerken
def vereenvoudig_pokemon(p):
    rij = { "id": p["id"],
        "naam": p["name"]
     }
    return rij


#---wegschrijven

def bepaal_kolommen(data ):
    kolommen = []
    for rij in data:
        for k in rij:
            if k not in kolommen:
                kolommen.append(k)
    return kolommen

def schrijf_bestand(bestandsnaam, schrijf_functie, encoding : str):
    with open(bestandsnaam, "w", encoding=encoding) as f:
            schrijf_functie(f)

def schrijf_csv(data, bestandsnaam):
    def schrijf(f):
        writer = csv.writer(f)

def schrijf_json(data, bestandsnaam):
    def schrijf(f):
        json.dump(data, f)

# --- main

def vraag_aantal():
    """"main function voor vragen"""
    antwoord = input(f"hoeveel pokemon ophalen? [{STANDAARD_AANTAL}]")
    if not antwoord:
        return STANDAARD_AANTAL
    try:
        aantal = int(antwoord)
    except ValueError:
        raise ApiFout("vul een valide getal in")
    if not 1 <= aantal <= MAX_AANTAL:
        raise ApiFout("Kies een aantal tussen 1 en {MAX_AANTAL}.")
    return aantal

def main():
    headers = maak_headers(haal_api_sleutel())

    try:
        aantal = vraag_aantal()
        lijst = (haal_pokemon_lijst (aantal, headers=headers))
        ruw = (haal_pokemon_lijst(lijst, headers=headers))
        verwerk = (vereenvoudig_pokemon(p) for p in ruw)

        if not verwerk:
            print("geen bruikbare gegevens")
            return  1

        schrijf_csv(verwerk, UITVOER_CSV)
        schrijf_json(lijst, UITVOER_JSON)
        print(f"weggeschreven naar {UITVOER_JSON} en {UITVOER_CSV}")
        return 0

    except ApiFout as e:
        print("Fout")
    except PermissionError:
        print("geen schrijfrechten")
    except OSError as e:
        print("Fout bij wegschrijven")
    return 1

if __name__ == "__main__":
    sys.exit(main())
