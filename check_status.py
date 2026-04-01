"""
Stampa su console lo stato attuale delle colonnine Allego.
Usa fetch_charger_status() da allego_bot.py per debuggare il bot.

Uso:
    python check_status.py           # output normale
    python check_status.py --raw     # stampa la risposta grezza dell'API
"""

import sys
import json
import requests
from datetime import datetime
from allego_bot import fetch_charger_status, ALLEGO_API_URL, ALLEGO_STATION_ID, HEADERS


def fetch_raw() -> dict:
    r = requests.get(ALLEGO_API_URL, params={"station_id": ALLEGO_STATION_ID}, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def main():
    if "--raw" in sys.argv:
        print("\n[DEBUG] Risposta grezza API Allego:")
        print(json.dumps(fetch_raw(), indent=2, ensure_ascii=False))
        return

    if "--debug" in sys.argv:
        data = fetch_raw()
        items = data.get("items", {})
        print(f"\n[DEBUG] Chiavi top-level: {list(data.keys())}")
        print(f"[DEBUG] Numero di items: {len(items)}")
        for key, item in items.items():
            print(f"\n  item[{key!r}]:")
            for k, v in item.items():
                print(f"    {k}: {v!r}")
            all_ = item.get("all", 0)
            print(f"    --> {'INCLUSA' if all_ != 0 else 'SCARTATA (all == 0)'}")
        return

    ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*45}")
    print(f"  Stato colonnine Allego — {ora}")
    print(f"{'='*45}")

    try:
        chargers = fetch_charger_status()
        for label, state in chargers.items():
            free, total = map(int, state.split("/"))
            if free == total:
                status = "[LIBERA]  "
            elif free == 0:
                status = "[OCCUPATA]"
            else:
                status = "[PARZIALE]"
            print(f"  {status}  {label}: {free}/{total} libere")
    except Exception as e:
        print(f"  ERRORE: {e}")
        print("  Prova: python check_status.py --raw  per vedere la risposta API")

    print(f"{'='*45}\n")


if __name__ == "__main__":
    main()
