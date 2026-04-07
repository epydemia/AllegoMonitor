"""
Monitor colonnine Allego con controllo via Telegram.

Comandi disponibili da iPhone:
  /start  - avvia il monitoraggio
  /stop   - ferma il monitoraggio
  /stato  - mostra lo stato attuale delle colonnine

Dipendenze:
    pip install requests beautifulsoup4

Configurazione:
    Modifica le variabili nella sezione CONFIG qui sotto.
"""

import re
import requests
import time
import threading
import os
import subprocess
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


# ─────────────────────────────────────────────
#  CONFIG — legge le credenziali dal file .env
# ─────────────────────────────────────────────
def load_env(filepath):
    """Carica le variabili dal file .env senza dipendenze esterne."""
    env_path = Path(filepath)
    if not env_path.exists():
        raise FileNotFoundError(f"File .env non trovato in: {env_path.resolve()}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

load_env(Path(__file__).parent / ".env")

TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ALLEGO_URL         = "https://www.allego.eu/charging-station/wankelstrasse-3-ingolstadt/"
INTERVALLO_SECONDI = 60   # frequenza di controllo della pagina

try:
    _ts = subprocess.check_output(
        ["git", "log", "-1", "--format=%cd", "--date=format:%Y%m%d_%H%M"],
        cwd=Path(__file__).parent, stderr=subprocess.DEVNULL
    ).decode().strip()
    VERSION = _ts if _ts else "unknown"
except Exception:
    VERSION = "unknown"
# ─────────────────────────────────────────────

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
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# Stato globale
monitoraggio_attivo = False
stato_precedente: dict[str, str] = {}
ultimo_update_id = 0


# ──────────────────────────────────────────────────────
#  ALLEGO — scraping
# ──────────────────────────────────────────────────────

def fetch_charger_status() -> dict[str, str]:
    """Scrape la pagina Allego e restituisce {label: 'free/all'} per ogni tipo di connettore."""
    r = requests.get(ALLEGO_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    plugs = soup.find_all("div", class_="plug")
    if not plugs:
        raise ValueError("Nessuna colonnina trovata nella pagina Allego")

    groups: dict[str, dict] = {}

    for plug in plugs:
        # Velocità (es. div.speed-number contiene "11")
        speed_el = plug.find("div", class_="speed-number")
        speed = speed_el.get_text(strip=True) if speed_el else "?"

        # Tipo connettore dal nome file dell'icona (plug-type-2.svg → "Type 2")
        icon_img = plug.find("img", attrs={"data-src": True})
        conn_type = "AC"
        if icon_img:
            m = re.search(r"plug-type-(\w+)\.svg", icon_img["data-src"])
            if m:
                conn_type = f"Type {m.group(1)}"

        # Stato del connettore
        state = "Unknown"
        for prop in plug.find_all("div", class_="prop"):
            strong = prop.find("strong")
            span = prop.find("span")
            if strong and span and "State" in strong.get_text():
                state = span.get_text(strip=True)
                break

        label = f"{conn_type} {speed}kW"
        if label not in groups:
            groups[label] = {"free": 0, "total": 0}
        groups[label]["total"] += 1
        if state.lower() == "available":
            groups[label]["free"] += 1

    return {label: f"{g['free']}/{g['total']}" for label, g in groups.items()}


# ──────────────────────────────────────────────────────
#  TELEGRAM — invio messaggi e ricezione comandi
# ──────────────────────────────────────────────────────

def telegram_send(text: str):
    """Invia un messaggio al tuo iPhone."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[{ora()}] Errore invio Telegram: {e}")


def telegram_get_updates() -> list[dict]:
    """Recupera i nuovi messaggi ricevuti dal bot."""
    global ultimo_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": ultimo_update_id + 1, "timeout": 10, "limit": 10}
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        if data.get("ok"):
            return data.get("result", [])
    except Exception as e:
        print(f"[{ora()}] Errore ricezione Telegram: {e}")
    return []


# ──────────────────────────────────────────────────────
#  LOOP MONITORAGGIO (thread separato)
# ──────────────────────────────────────────────────────

def loop_monitoraggio():
    global monitoraggio_attivo, stato_precedente

    print(f"[{ora()}] Monitoraggio avviato.")
    stato_precedente = {}

    while monitoraggio_attivo:
        try:
            stato_attuale = fetch_charger_status()

            if not stato_precedente:
                # Prima lettura: mostra lo stato iniziale
                righe = [f"*Stato iniziale colonnine:*"]
                for cid, state in stato_attuale.items():
                    righe.append(f"• `{cid}`: {state}")
                telegram_send("\n".join(righe))
            else:
                # Controlla i cambiamenti
                cambiamenti = []
                for cid, state in stato_attuale.items():
                    prec = stato_precedente.get(cid)
                    if prec is None:
                        cambiamenti.append(f"🆕 *Nuova colonnina*\n`{cid}`: {state}")
                    elif prec != state:
                        cambiamenti.append(f"⚡ *Cambio stato*\n`{cid}`: {prec} → *{state}*")
                for cid in stato_precedente:
                    if cid not in stato_attuale:
                        cambiamenti.append(f"❌ *Colonnina rimossa*\n`{cid}` non più disponibile")

                if cambiamenti:
                    msg = "🔔 *Aggiornamento colonnine Allego*\n\n" + "\n\n".join(cambiamenti)
                    telegram_send(msg)
                    print(f"[{ora()}] Cambiamento rilevato, notifica inviata.")
                else:
                    print(f"[{ora()}] Nessun cambiamento.")

            stato_precedente = stato_attuale

        except Exception as e:
            print(f"[{ora()}] Errore nel monitoraggio: {e}")

        # Attendi a intervalli di 1s per poter rispondere allo stop rapidamente
        for _ in range(INTERVALLO_SECONDI):
            if not monitoraggio_attivo:
                break
            time.sleep(1)

    print(f"[{ora()}] Monitoraggio fermato.")


# ──────────────────────────────────────────────────────
#  LOOP COMANDI TELEGRAM (thread principale)
# ──────────────────────────────────────────────────────

def gestisci_comando(testo: str):
    global monitoraggio_attivo

    cmd = testo.strip().lower().split()[0]

    if cmd == "/start":
        if monitoraggio_attivo:
            telegram_send("ℹ️ Il monitoraggio è *già attivo*.")
        else:
            monitoraggio_attivo = True
            t = threading.Thread(target=loop_monitoraggio, daemon=True)
            t.start()
            telegram_send(
                f"✅ *Monitoraggio avviato!*\n"
                f"Controllo ogni {INTERVALLO_SECONDI} secondi.\n"
                f"Riceverai una notifica ad ogni cambio di stato."
            )

    elif cmd == "/stop":
        if not monitoraggio_attivo:
            telegram_send("ℹ️ Il monitoraggio è *già fermo*.")
        else:
            monitoraggio_attivo = False
            telegram_send("🛑 *Monitoraggio fermato.*")

    elif cmd == "/stato":
        try:
            chargers = fetch_charger_status()
            righe = ["📍 *Stato attuale colonnine:*"]
            for label, state in chargers.items():
                free, total = map(int, state.split("/"))
                emoji = "🟢" if free == total else "🔴" if free == 0 else "🟡"
                righe.append(f"{emoji} {label}: *{state}* libere")
            mon = "▶️ attivo" if monitoraggio_attivo else "⏹ fermo"
            righe.append(f"\n_Monitoraggio: {mon}_")
            telegram_send("\n".join(righe))
        except Exception as e:
            telegram_send(f"⚠️ Errore nel recupero dati: {e}")

    else:
        telegram_send(
            "❓ Comandi disponibili:\n"
            "/start — avvia il monitoraggio\n"
            "/stop  — ferma il monitoraggio\n"
            "/stato — mostra lo stato attuale"
        )


def main():
    global ultimo_update_id

    print("=" * 50)
    print("  Allego Monitor — Bot Telegram")
    print(f"  Versione: {VERSION}")
    print(f"  Intervallo controllo: {INTERVALLO_SECONDI}s")
    print("  In attesa di comandi da Telegram...")
    print("=" * 50)

    # Informa l'utente che il servizio è partito
    telegram_send(
        f"🤖 *Allego Monitor online!*  `v{VERSION}`\n\n"
        "Comandi disponibili:\n"
        "/start — avvia il monitoraggio\n"
        "/stop  — ferma il monitoraggio\n"
        "/stato — mostra lo stato attuale"
    )

    # Loop principale: ascolta i comandi Telegram
    while True:
        updates = telegram_get_updates()
        for update in updates:
            ultimo_update_id = update["update_id"]
            message = update.get("message", {})
            chat_id = str(message.get("chat", {}).get("id", ""))
            testo = message.get("text", "")

            # Risponde solo al tuo chat_id per sicurezza
            if chat_id != str(TELEGRAM_CHAT_ID):
                print(f"[{ora()}] Messaggio ignorato da chat_id sconosciuto: {chat_id}")
                continue

            if testo:
                print(f"[{ora()}] Comando ricevuto: {testo}")
                gestisci_comando(testo)

        time.sleep(2)


def ora() -> str:
    return datetime.now().strftime("%H:%M:%S")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServizio interrotto.")
