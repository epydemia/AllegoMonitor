# AllegoMonitor

Bot Telegram che monitora lo stato delle colonnine di ricarica [Allego](https://www.allego.eu/charging-station/wankelstrasse-3-ingolstadt/) e invia una notifica ogni volta che una colonnina cambia stato (libera ↔ occupata).

## Funzionamento

Il bot interroga ogni 60 secondi l'API interna di Allego e confronta il numero di colonnine libere con il rilevamento precedente. Se c'è un cambiamento, invia un messaggio Telegram.

Lo stato è espresso nel formato `libere/totali` — ad esempio `1/2` significa una colonnina libera su due.

## Comandi Telegram

| Comando | Descrizione |
|---------|-------------|
| `/start` | Avvia il monitoraggio |
| `/stop` | Ferma il monitoraggio |
| `/stato` | Mostra lo stato attuale delle colonnine |

---

## Installazione

### 1. Requisiti

- Python 3.9+
- Un account Telegram

### 2. Clona il repository

```bash
git clone https://github.com/epydemia/AllegoMonitor.git
cd AllegoMonitor
```

### 3. Crea il virtual environment e installa le dipendenze

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

> Le uniche dipendenze esterne sono `requests`. `beautifulsoup4` non è più necessaria.

---

## Configurazione

### 1. Crea il bot Telegram

1. Apri Telegram e cerca **[@BotFather](https://t.me/BotFather)**
2. Invia `/newbot` e segui le istruzioni
3. Al termine BotFather ti fornirà un **token** nel formato `123456789:ABCdef...` — conservalo

### 2. Ottieni il tuo Chat ID

1. Cerca **[@userinfobot](https://t.me/userinfobot)** su Telegram e invia `/start`
2. Ti risponderà con il tuo **ID numerico** (es. `123456789`)

### 3. Crea il file `.env`

Nella root del progetto crea un file `.env` con le tue credenziali:

```env
TELEGRAM_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=123456789
```

| Variabile | Descrizione |
|-----------|-------------|
| `TELEGRAM_TOKEN` | Token del bot fornito da BotFather |
| `TELEGRAM_CHAT_ID` | Il tuo ID Telegram numerico |

> Il file `.env` è escluso da git (`.gitignore`) — non verrà mai committato.

---

## Avvio

```bash
source venv/bin/activate
python3 allego_bot.py
```

All'avvio il bot invia un messaggio Telegram di conferma. Da quel momento puoi controllarlo con `/start`, `/stop` e `/stato` direttamente dalla chat.
