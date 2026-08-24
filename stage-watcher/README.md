# Stage Watcher — veille automatique des offres de stage (Big4 Ukraine)

Système qui vérifie chaque jour, tout seul, les job boards des Big4 en
Ukraine et t'envoie une notification Telegram pour chaque **nouvelle**
offre de stage/junior détectée. Zéro serveur à payer (GitHub Actions
gratuit), zéro IA dans la boucle (filtrage par mots-clés déterministe).

## 1. Architecture — vue d'ensemble

```
config/companies.yaml   ← LE fichier à éditer pour ajouter boîtes/plateformes
        │
        ▼
   main.py (orchestrateur)
        │
        ├─► scrapers/registry.py ──► scrapers/dou_rss.py         (RSS natif)
        │                        ──► scrapers/workable_api.py    (API JSON)
        │                        ──► scrapers/robota_html.py     (HTML statique)
        │                        ──► scrapers/workua_html.py     (HTML statique)
        │                        ──► scrapers/jooble_html.py     (HTML statique)
        │                        ──► scrapers/html_generic.py    (HTML statique, réutilisable)
        │                        ──► scrapers/html_js_playwright.py (JS lourd, désactivé par défaut)
        │
        ├─► keyword_filter.py   (garde uniquement stage/junior/intern...)
        ├─► state.py            (dédup: quelles offres déjà notifiées ?)
        └─► notifier/           (envoi Telegram)

.github/workflows/daily_watch.yml  ← exécute main.py chaque jour, tout seul
data/seen_jobs.json                 ← mémoire persistante (commitée par le bot)
```

Chaque scraper est **indépendant** : si celui de robota.ua casse (site
qui change de design), les autres continuent de tourner normalement.

## 2. Setup initial (à faire une fois)

### a) Créer le repo GitHub
1. Crée un nouveau repo GitHub (peut être privé).
2. Pousse tout ce dossier dedans :
   ```bash
   git init
   git add .
   git commit -m "Initial setup"
   git branch -M main
   git remote add origin https://github.com/TON_USER/TON_REPO.git  https://github.com/fokenstart/ua_stage_watch
   git push -u origin main
   ```

### b) Configurer le bot Telegram (PLACEHOLDER — voir notifier/)
1. Sur Telegram, cherche `@BotFather`, envoie `/newbot`, suis les
   instructions → tu obtiens un **TOKEN**.
2. Démarre une conversation avec ton nouveau bot (cherche son
   `@username`, clique Start).
3. Va sur `https://api.telegram.org/bot<TOKEN>/getUpdates` dans un
   navigateur juste après avoir envoyé un message au bot → cherche
   `"chat":{"id": XXXXXXXXX}` → c'est ton **CHAT_ID**.
4. Dans GitHub : `Settings > Secrets and variables > Actions > New
   repository secret`, ajoute :
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

### c) Lancer un premier test manuel
Dans l'onglet **Actions** de ton repo GitHub → sélectionne le workflow
"Veille quotidienne des stages" → bouton **"Run workflow"** (disponible
grâce à `workflow_dispatch` dans le YAML). Regarde les logs pour voir
quels scrapers fonctionnent déjà et lesquels nécessitent le travail
décrit ci-dessous.

## 3. Placeholders à compléter — résumé de tout ce qui nécessite ton intervention

| # | Fichier | Ce qu'il faut faire |
|---|---|---|
| 1 | `notifier/` | Créer le bot Telegram + secrets GitHub (voir 2.b ci-dessus) |
| 2 | `scrapers/robota_html.py` | Vérifier/ajuster `JOB_LINK_SELECTOR` en inspectant le HTML réel dans le navigateur |
| 3 | `scrapers/workua_html.py` | Idem, vérifier/ajuster `JOB_LINK_SELECTOR` |
| 4 | `scrapers/jooble_html.py` | Idem, vérifier/ajuster `JOB_LINK_SELECTOR` |
| 5 | `scrapers/workable_api.py` | Confirmer l'endpoint JSON exact via DevTools (méthode détaillée dans le fichier) |
| 6 | `config/companies.yaml` — EY | Trouver l'ID entreprise EY sur robota.ua et work.ua (actuellement basé sur une recherche générique, moins précis) |
| 7 | `config/companies.yaml` — Deloitte/PwC/EY sites propres | Ces 3 sites carrière semblent nécessiter du JS → voir `scrapers/html_js_playwright.py` pour la marche à suivre (chercher d'abord un endpoint JSON caché avant de sortir Playwright) |
| 8 | `.github/workflows/daily_watch.yml` | Ajuster l'heure du cron si tu veux un autre horaire que 07h00 UTC |

**Comment trouver/ajuster un sélecteur CSS (technique commune aux points 2, 3, 4) :**
1. Ouvre la page dans Chrome/Firefox.
2. Clic droit sur le titre d'une offre → "Inspecter".
3. Repère la balise `<a>` et sa classe CSS exacte.
4. Remplace la valeur de `JOB_LINK_SELECTOR` dans le fichier concerné.
5. Relance le workflow manuellement (voir 2.c) pour vérifier que ça matche.

## 4. Ajouter une nouvelle entreprise (hors Big4)

Un seul fichier à toucher : `config/companies.yaml`. Un exemple commenté
(BDO) est déjà présent en bas du fichier — décommente-le et adapte les
IDs. Aucune ligne de code à écrire tant que la plateforme (DOU, robota.ua,
work.ua, Workable...) est déjà couverte par un scraper existant.

## 5. Ajouter une nouvelle plateforme (job board pas encore couvert)

1. Crée `scrapers/mon_nouveau_scraper.py`, hérite de `BaseScraper`
   (voir `scrapers/base.py` pour le contrat exact à respecter).
2. Enregistre-le dans `scrapers/registry.py` (2 lignes à ajouter).
3. Utilise ce nouveau `type:` dans `companies.yaml`.

## 6. Lancer en local (pour débugger un scraper)

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="ton_token"
export TELEGRAM_CHAT_ID="ton_chat_id"
python main.py
```

Sans les variables Telegram définies, le script tourne quand même et
affiche dans le terminal les messages qui auraient été envoyés (utile
pour tester les scrapers sans spammer ton Telegram).

## 7. Limites connues / choix assumés

- **LinkedIn est volontairement exclu** : leurs CGU interdisent le
  scraping et ils détectent/bannissent agressivement — pas un bon
  rapport risque/bénéfice. Utilise plutôt les alertes email natives
  LinkedIn en complément de ce système.
- **Instagram exclu** pour la même raison (pas d'API publique fiable
  sans validation Meta Business).
- **Doublons possibles** entre Jooble et robota.ua/work.ua (Jooble
  agrège ces mêmes sources) — mieux vaut un doublon qu'une offre
  manquée, mais sache que ça arrivera occasionnellement.
- **Filtrage 100% mots-clés, pas d'IA** : rapide, gratuit, prévisible,
  mais moins "intelligent" qu'un LLM — si tu rates des offres à cause
  d'un titre inhabituel, enrichis `keywords_include` dans
  `companies.yaml`.
