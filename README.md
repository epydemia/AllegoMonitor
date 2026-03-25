# AllegoMonitor

Bot Telegram che monitora lo stato delle colonnine di ricarica [Allego](https://www.allego.eu/charging-station/wankelstrasse-3-ingolstadt/) e invia una notifica ogni volta che una colonnina cambia stato (libera ↔ occupata).

## Funzionamento

Il bot fa scraping della pagina Allego ogni 60 secondi e confronta lo stato attuale con quello precedente. Se rileva un cambiamento, invia un messaggio Telegram.

## Comandi Telegram

| Comando | Descrizione |
|---------|-------------|
| `/start` | Avvia il monitoraggio |
| `/stop` | Ferma il monitoraggio |
| `/stato` | Mostra lo stato attuale delle colonnine |

## Installazione

```bash
git clone https://github.com/epydemia/AllegoMonitor.git
cd AllegoMonitor
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4
```

## Configurazione

Crea un file `.env` nella root del progetto:

```env
TELEGRAM_TOKEN=il_tuo_token_bot
TELEGRAM_CHAT_ID=il_tuo_chat_id
```

- **TELEGRAM_TOKEN**: ottenibile creando un bot con [@BotFather](https://t.me/BotFather)
- **TELEGRAM_CHAT_ID**: il tuo ID chat (usa [@userinfobot](https://t.me/userinfobot) per trovarlo)

## Avvio

```bash
python3 allego_bot.py
```

Il bot si mette in ascolto di comandi Telegram. Invia `/start` per avviare il monitoraggio.
