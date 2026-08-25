# Assistant IA de réunion

Application web de transcription et de synthèse de réunions. Le frontend React
enregistre des segments audio, le backend Flask les transcrit avec Whisper puis
génère un compte rendu avec NVIDIA Nemotron via NIM, indexé dans ChromaDB.

## Structure

```text
.
├── backend/
│   ├── api/              # Contrôleurs HTTP
│   ├── services/         # Cas d’usage et règles métier
│   ├── repositories/     # Accès aux données
│   ├── models/           # Entités SQLAlchemy
│   ├── schemas/          # Validation des entrées
│   ├── ai/               # Whisper, NVIDIA NIM et RAG
│   ├── workers/          # Traitements asynchrones bornés
│   ├── middleware/       # JWT, erreurs et journalisation
│   ├── tests/            # Tests backend
│   ├── app.py            # Application factory Flask
│   └── config.py         # Configuration centralisée
├── frontend/
│   └── src/
│       ├── pages/        # Écrans liés au routage
│       ├── components/   # Composants réutilisables
│       ├── services/     # Accès HTTP
│       ├── hooks/        # État et capacités navigateur
│       ├── context/      # État partagé
│       └── utils/        # Fonctions pures
├── docker/               # Reverse proxy Nginx
├── docs/                 # Architecture et sécurité
└── docker-compose.yml
```

Les règles de dépendance sont détaillées dans
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Démarrage Docker

Prérequis : Docker Compose V2, une clé NVIDIA NIM et Ollama accessible depuis
Docker pour les embeddings locaux uniquement.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Générez deux secrets différents d’au moins 32 caractères et placez-les dans
`SECRET_KEY` et `JWT_SECRET_KEY`. Renseignez aussi `NVIDIA_API_KEY`, puis
configurez Ollama pour `nomic-embed-text` et, si nécessaire, SMTP.

```bash
docker compose up --build
```

L’application est exposée sur `http://localhost`. En production, seul Nginx est
publié sur l’hôte. Pour exposer également le backend en développement, copiez
`docker-compose.override.yml.example` vers `docker-compose.override.yml`.

## Développement local

### Backend

```bash
cd backend
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Vite redirige `/api` vers `http://localhost:5000` en développement.

## Qualité

```bash
cd backend
pytest
ruff check .
python -m pip_audit -r requirements.txt

cd ../frontend
npm run check
npm audit
```

## Configuration

Toutes les variables backend documentées figurent dans `backend/.env.example`.
Les vrais secrets restent uniquement dans `backend/.env`, ignoré par Git et par
le contexte de build Docker. Le démarrage en mode production échoue si les clés
Flask/JWT sont absentes, courtes ou laissées à leur valeur par défaut.

### Paiements MTN MoMo et Orange Money

La facturation utilise l'API Riserva uniquement depuis le backend. Configurez
`RISERVA_API_KEY` avec une cle `rsk_test_...`, `RISERVA_WEBHOOK_SECRET` et
`RISERVA_MODE=SANDBOX`. Le webhook du fournisseur doit pointer vers :

```text
https://votre-api.example/api/webhooks/riserva
```

Utilisez `PAYMENT_WEBHOOK_URL` si vous souhaitez aussi recevoir le webhook sur
une URL propre a chaque encaissement. En local, laissez cette valeur vide si
l'URL n'est pas publiquement joignable. Les suffixes sandbox sont `0000`
(echec immediat), `0001` (echec apres attente) et toute autre valeur (succes).

`BILLING_ENFORCEMENT_ENABLED=true` impose le parcours SaaS : après la création
du compte et de l'entreprise, l'utilisateur reste sur la facturation tant que
le paiement n'est pas confirmé. Le backend renvoie aussi `402 Payment Required`
sur les fonctions métier afin que le contrôle ne dépende jamais du frontend.

## Limite actuelle

Les tâches IA utilisent un exécuteur local borné. Pour garantir la reprise des
tâches après redémarrage ou déployer plusieurs instances backend, remplacez-le
par une file durable telle que Celery ou RQ avec Redis.
