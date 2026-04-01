"""
Stampa su console lo stato attuale delle colonnine Allego.

Uso:
    python check_status.py
"""

from datetime import datetime
import requests

ALLEGO_STATION_ID = 10944184
ALLEGO_API_URL    = "https://www.allego.eu/wp-content/themes/happyhorizon/functions/ajax_station.php"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
}


def fetch_charger_status() -> dict[str, str]:
    """Chiama l'API interna Allego e restituisce {label: 'libere/totali'} per ogni connettore attivo."""
    r = requests.get(ALLEGO_API_URL, params={"station_id": ALLEGO_STATION_ID}, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()

    chargers = {}
    for item in data.get("items", {}).values():
        if item.get("all", 0) == 0:
            continue
        label = f"{item['label']} {item['speed']}kW"
        chargers[label] = f"{item['free']}/{item['all']}"

    if not chargers:
        raise ValueError("Nessuna colonnina trovata nella risposta API Allego")
    return chargers


def main():
    ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*45}")
    print(f"  Stato colonnine Allego — {ora}")
    print(f"{'='*45}")

    try:
        chargers = fetch_charger_status()
        for label, state in chargers.items():
            free, total = map(int, state.split("/"))
            if free == total:
                emoji = "[LIBERA]  "
            elif free == 0:
                emoji = "[OCCUPATA]"
            else:
                emoji = "[PARZIALE]"
            print(f"  {emoji}  {label}: {free}/{total} libere")
    except Exception as e:
        print(f"  ERRORE: {e}")

    print(f"{'='*45}\n")


if __name__ == "__main__":
    main()
