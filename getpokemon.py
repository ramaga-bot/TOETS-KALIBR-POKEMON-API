"""Dit script is bedoeld om Pokemon-gegevens op te halen, te verwerken en weg te schrijven naar JSON en CSV."""

import csv
import json
import os
import sys
import time

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
