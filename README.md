# Stage Watcher (MVP)

Veille des stages **robota.ua** (стажування, rubriques 18 + 14 : banques / investissement / leasing et consulting / analytique / audit). GitHub Actions met à jour la base ; le bot Telegram répond à `/stage`.

## Architecture

```
config/sources.yaml   → liste des plateformes
main.py               → scrape + update data/jobs.json
bot.py                → Telegram /stage
scrapers/registry.py  → brancher une nouvelle plateforme ici
```

Ajouter une plateforme : nouveau fichier dans `scrapers/`, une ligne dans `registry.py`, une entrée `type:` dans `sources.yaml`.

## Guide d’exploitation

**1. Une fois**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Dans `.env` : token BotFather (`TELEGRAM_BOT_TOKEN`) et ton chat id (`TELEGRAM_CHAT_ID`).

Premier scrape (constitue la base, **sans** tout envoyer sur Telegram) :

```bash
python main.py
```

**2. Bot (reste ouvert)**

```bash
python bot.py
```

Sur Telegram : `/start` puis `/stage` → tableau `Titre | Source | LINK`. Seules les offres **nouvelles depuis le dernier /stage** sont envoyées.

**3. GitHub Actions**

Secrets inutiles pour le scrape. Active le workflow *Scrape stages* (toutes les 6 h + Run workflow). Il commit `data/jobs.json`. En local, `git pull` avant `/stage` si tu ne scrapes pas toi-même (le bot relance aussi un scrape à chaque `/stage`).

**4. Commandes**

| Commande | Rôle |
|---|---|
| `python main.py` | Scrape robota.ua, met à jour la DB |
| `python bot.py` | Écoute Telegram |
| `/stage` | Scrape + envoie les nouveautés |
