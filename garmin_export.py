"""
Garmin Connect – persönlicher Datenexport
==========================================

Nutzt die inoffizielle Python-Bibliothek 'garminconnect', um mit deinem
normalen Garmin-Connect-Account Aktivitäts- und Gesundheitsdaten abzurufen
und lokal als JSON/CSV zu speichern.

WICHTIG:
- Das ist KEINE offizielle Garmin-API-Integration, sondern nutzt dieselben
  Endpunkte wie die Garmin-Connect-Website/App. Garmin kann das jederzeit
  ändern; nutze es nur für persönliche, nicht-kommerzielle Zwecke.
- Deine Zugangsdaten werden NUR lokal verwendet, um dich bei Garmin
  einzuloggen. Sie werden nirgendwohin sonst geschickt.

Installation:
    pip install garminconnect --break-system-packages

Nutzung:
    export GARMIN_EMAIL="deine@email.de"
    export GARMIN_PASSWORD="deinPasswort"
    python garmin_export.py --days 30
"""

import argparse
import getpass
import json
import os
from datetime import date, timedelta

from garminconnect import Garmin, GarminConnectAuthenticationError

# Ort, an dem die Login-Session zwischengespeichert wird, damit nicht bei
# jedem Skriptlauf ein neuer Login (= Rate-Limit-Risiko) nötig ist.
TOKEN_DIR = os.path.join(os.path.expanduser("~"), ".garminconnect")


def login() -> Garmin:
    email = os.environ.get("GARMIN_EMAIL") or input("Garmin E-Mail: ")
    password = os.environ.get("GARMIN_PASSWORD") or getpass.getpass("Garmin Passwort: ")

    client = Garmin(email, password)

    # 1. Versuch: gespeicherte Session wiederverwenden (kein neuer Login nötig)
    try:
        client.login(TOKEN_DIR)
        print("Angemeldet über gespeicherte Session (kein neuer Login nötig).")
        return client
    except Exception:
        pass  # keine gültige Session vorhanden -> normaler Login

    # 2. Versuch: frischer Login, danach Session für nächstes Mal speichern
    try:
        client.login()
        os.makedirs(TOKEN_DIR, exist_ok=True)
        client.garth.dump(TOKEN_DIR)
        print(f"Login erfolgreich. Session gespeichert in: {TOKEN_DIR}")
        return client
    except GarminConnectAuthenticationError as e:
        msg = str(e)
        if "429" in msg or "rate limit" in msg.lower():
            raise SystemExit(
                "Garmin blockiert deine IP gerade wegen zu vieler Login-"
                "Versuche (HTTP 429). Das liegt NICHT an falschem Passwort.\n"
                "-> Warte 30-60 Minuten und versuch es dann erneut.\n"
                "-> Starte das Skript in der Zwischenzeit nicht mehrfach neu,"
                " das verlängert die Sperre."
            )
        raise SystemExit(
            "Login fehlgeschlagen. Prüfe E-Mail/Passwort oder bestätige "
            "ggf. die Multi-Faktor-Anmeldung in der Garmin-App.\n"
            f"Details: {msg}"
        )
    except Exception as e:
        raise SystemExit(f"Unerwarteter Fehler beim Login: {e}")


def export_activities(client: Garmin, days: int, out_dir: str):
    start = (date.today() - timedelta(days=days)).isoformat()
    activities = client.get_activities_by_date(start, date.today().isoformat())
    path = os.path.join(out_dir, f"activities_{days}d.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(activities, f, ensure_ascii=False, indent=2)
    print(f"{len(activities)} Aktivitäten gespeichert -> {path}")


def export_daily_health(client: Garmin, days: int, out_dir: str):
    records = []
    for i in range(days):
        day = (date.today() - timedelta(days=i)).isoformat()
        entry = {"date": day}
        try:
            entry["steps"] = client.get_steps_data(day)
            entry["heart_rate"] = client.get_heart_rates(day)
            entry["sleep"] = client.get_sleep_data(day)
            entry["stress"] = client.get_stress_data(day)
        except Exception as e:
            entry["error"] = str(e)
        records.append(entry)

    path = os.path.join(out_dir, f"daily_health_{days}d.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Gesundheitsdaten für {days} Tage gespeichert -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Garmin Connect Datenexport")
    parser.add_argument("--days", type=int, default=30, help="Anzahl Tage rückwirkend")
    parser.add_argument("--out", default="garmin_data", help="Ausgabeverzeichnis")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    client = login()

    export_activities(client, args.days, args.out)
    export_daily_health(client, args.days, args.out)

    print("\nFertig! Du kannst die JSON-Dateien im Ordner jetzt bei Claude hochladen.")


if __name__ == "__main__":
    main()
