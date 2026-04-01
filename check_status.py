"""
Stampa su console lo stato attuale delle colonnine Allego.
Usa fetch_charger_status() da allego_bot.py per debuggare il bot.

Uso:
    python check_status.py
"""

from datetime import datetime
from allego_bot import fetch_charger_status


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
                status = "[LIBERA]  "
            elif free == 0:
                status = "[OCCUPATA]"
            else:
                status = "[PARZIALE]"
            print(f"  {status}  {label}: {free}/{total} libere")
    except Exception as e:
        print(f"  ERRORE: {e}")

    print(f"{'='*45}\n")


if __name__ == "__main__":
    main()
