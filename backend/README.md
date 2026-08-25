# Assistant IA de Réunion – Backend

Backend Flask pour l'application d'assistant intelligent de réunion.  
Transcription automatique, résumé IA, extraction structurée, RAG conversationnel.

---

## Stack technique

| Composant        | Technologie              | Rôle                              |
|-----------------|--------------------------|-----------------------------------|
| Framework       | Flask 3                  | API REST                          |
| Base de données | SQLite (ou MySQL)        | Stockage des réunions et données  |
| Transcription   | Faster-Whisper (small)   | Audio → texte multilingue         |
| LLM             | NVIDIA NIM + Nemotron 3.5  | Résumé, extraction, chat          |
| Embeddings      | nomic-embed-text (Ollama)| Vectorisation pour le RAG         |
| Base vectorielle| ChromaDB                 | Recherche sémantique (RAG)        |
| PDF             | ReportLab                | Génération des comptes rendus     |
| Auth            | JWT (PyJWT)              | Sessions 12h                      |

---

## Installation

### Prérequis

- Python 3.11+
- Une clé d'API NVIDIA NIM
- [Ollama](https://ollama.ai) pour les embeddings locaux uniquement
- Docker (optionnel)

### 1. Cloner et configurer

```bash
cd backend
cp .env.example .env
# Éditez .env et renseignez notamment NVIDIA_API_KEY
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Télécharger les modèles locaux

```bash
ollama pull nomic-embed-text
```

Faster-Whisper télécharge son modèle au premier usage. Nemotron est appelé via
NVIDIA NIM : aucun modèle LLM n'est téléchargé ou exécuté dans Docker.

### 4. Initialiser la base de données

```bash
python ../scripts/init_database.py
```

### 5. Lancer le serveur

```bash
python app.py
```

Le backend est accessible sur `http://localhost:5000`.

---

## Lancement avec Docker

```bash
# À la racine du projet
docker compose up --build
```

> Seuls les embeddings utilisent Ollama sur la machine hôte. Le LLM utilise
> l'API NVIDIA NIM via HTTPS.

---

## Architecture du backend

```
backend/
├── app.py                  Point d'entrée Flask
├── config.py               Configuration centralisée
├── requirements.txt
├── Dockerfile
│
├── api/                    Routes HTTP (aucune logique métier)
│   ├── auth_routes.py
│   ├── meeting_routes.py
│   ├── audio_routes.py
│   ├── summary_routes.py
│   ├── chat_routes.py
│   ├── export_routes.py
│   └── health_routes.py
│
├── services/               Logique métier
│   ├── auth_service.py
│   ├── meeting_service.py
│   ├── audio_service.py
│   ├── summary_service.py
│   ├── chat_service.py
│   └── export_service.py
│
├── ai/                     Traitements IA
│   ├── whisper_model.py    Transcription (Faster-Whisper)
│   ├── nvidia_client.py    Inférence LLM (NVIDIA NIM)
│   ├── chunker.py          Découpage texte + fusion segments
│   ├── summarizer.py       Résumé + extraction + titre
│   ├── embeddings.py       Génération vecteurs
│   └── rag.py              ChromaDB – indexation et recherche
│
├── repositories/           Accès base de données (SQL uniquement)
│   ├── user_repository.py
│   ├── meeting_repository.py
│   ├── audio_repository.py
│   └── summary_repository.py
│
├── models/                 Entités SQLAlchemy
│   ├── User.py
│   ├── Meeting.py
│   ├── AudioSegment.py
│   ├── Transcript.py
│   ├── Summary.py
│   ├── Decision.py
│   ├── Action.py
│   ├── Question.py
│   └── Risk.py
│
├── middleware/
│   ├── jwt.py              Génération + décorateur @jwt_required
│   └── error_handler.py    Gestionnaires d'erreurs globaux
│
├── schemas/
│   ├── auth_schema.py      Validation inscription/connexion
│   └── meeting_schema.py   Validation création/mise à jour réunion
│
├── workers/
│   └── transcription_worker.py   Pipeline asynchrone (thread)
│
├── prompts/                Prompts LLM externalisés
│   ├── summary.txt
│   ├── extract.txt
│   ├── title.txt
│   └── chat.txt
│
└── utils/
    ├── audio.py            Durée des fichiers audio
    ├── file.py             Gestion dossiers et fichiers
    └── pdf.py              Génération PDF (ReportLab)
```

---

## Endpoints API

### Authentification (`/api/auth`)

| Méthode | Endpoint             | Description                       |
|---------|---------------------|-----------------------------------|
| POST    | `/register`          | Inscription                       |
| POST    | `/login`             | Connexion → JWT 12h               |
| POST    | `/logout`            | Déconnexion (côté client)         |
| GET     | `/me`                | Infos utilisateur connecté        |
| POST    | `/refresh`           | Renouvellement token JWT          |
| PUT     | `/profile`           | Mise à jour nom / email / langue |

<!--
Exemple d'utilisation dans Postman pour modifier le profil :
- Méthode : PUT
- URL : http://localhost:5000/api/auth/profile
- Headers : Authorization = Bearer <token>
- Body (raw JSON) :
{
  "name": "Nouveau nom",
  "email": "nouvel@email.com",
  "language": "fr"
}
-->
| PUT     | `/password`          | Changement de mot de passe        |
| DELETE  | `/account`           | Suppression du compte             |

### Réunions (`/api`)

| Méthode | Endpoint                          | Description                       |
|---------|----------------------------------|-----------------------------------|
| POST    | `/meetings`                       | Créer une réunion                 |
| GET     | `/meetings`                       | Lister les réunions               |
| GET     | `/meetings/{id}`                  | Détail d'une réunion              |
| PUT     | `/meetings/{id}`                  | Modifier titre / description      |
| DELETE  | `/meetings/{id}`                  | Supprimer (cascade)               |
| GET     | `/meetings/{id}/status`           | Progression du traitement         |
| GET     | `/stats`                          | Statistiques du tableau de bord   |
| POST    | `/reprocess/{id}`                 | Retraiter sans réenregistrer      |

### Audio (`/api/audio`)

| Méthode | Endpoint                          | Description                       |
|---------|----------------------------------|-----------------------------------|
| POST    | `/upload-segment`                 | Segment audio 60s (multipart)     |
| POST    | `/end-meeting`                    | Déclenche le pipeline IA          |
| GET     | `/status/{meeting_id}`            | État de la réception audio        |

### Données IA (`/api`)

| Méthode | Endpoint                          | Description                       |
|---------|----------------------------------|-----------------------------------|
| GET     | `/transcript/{id}`                | Transcription complète            |
| GET     | `/summary/{id}`                   | Résumé structuré                  |
| GET     | `/actions/{id}`                   | Actions identifiées               |
| GET     | `/decisions/{id}`                 | Décisions prises                  |
| GET     | `/questions/{id}`                 | Questions ouvertes                |
| GET     | `/risks/{id}`                     | Risques identifiés                |
| GET     | `/report/{id}`                    | Toutes les données en une requête |

### Assistant IA (`/api/chat`)

| Méthode | Endpoint                          | Description                       |
|---------|----------------------------------|-----------------------------------|
| POST    | `/`                               | Question sur toutes les réunions  |
| POST    | `/{meeting_id}`                   | Question sur une réunion          |

### Export (`/api/export`)

| Méthode | Endpoint                          | Description                       |
|---------|----------------------------------|-----------------------------------|
| GET     | `/pdf/{meeting_id}`               | Télécharger le PDF                |
| GET     | `/json/{meeting_id}`              | Export JSON complet               |
| POST    | `/send-report`                    | Génère le PDF puis l'envoie par email via Resend |

<!--
Exemple d'utilisation dans Postman pour l'envoi automatique de mail :
- Méthode : POST
- URL : http://localhost:5000/api/export/send-report
- Headers : Authorization = Bearer <token>
- Body (raw JSON) :
{
  "meeting_id": 1,
  "emails": ["alice@example.com", "bob@example.com"],
  "subject": "Compte rendu de réunion",
  "html": "<p>Bonjour,</p><p>Veuillez trouver ci-joint le compte rendu.</p>"
}
-->

### Santé (`/api`)

| Méthode | Endpoint   | Description                             |
|---------|-----------|----------------------------------------|
| GET     | `/health`  | État de tous les composants            |
| GET     | `/models`  | Modèles IA configurés et disponibles   |

---

## Pipeline de traitement d'une réunion

```
Frontend (segments audio 60s, chevauchement 5s)
        ↓
POST /api/audio/upload-segment  (×N)
        ↓
POST /api/audio/end-meeting
        ↓ (thread asynchrone)
[Whisper] Transcription de chaque segment
        ↓
[Chunker] Fusion + suppression des chevauchements
        ↓
[NVIDIA NIM] Génération du titre automatique (si absent)
        ↓
[NVIDIA NIM] Résumé général + participants + conclusion
        ↓
[NVIDIA NIM] Extraction : décisions, actions, questions, risques
        ↓
[ChromaDB] Indexation pour la recherche RAG
        ↓
[ReportLab] Génération du PDF
        ↓
Statut → COMPLETED
```

Le frontend suit la progression via **polling** sur `GET /api/meetings/{id}/status`.

---

## Statuts d'une réunion

| Statut       | Signification                           |
|-------------|----------------------------------------|
| `pending`    | Créée, en attente d'enregistrement     |
| `recording`  | Enregistrement en cours                |
| `transcribing` | Pipeline Whisper en cours            |
| `analyzing`  | Résumé et extraction IA en cours       |
| `completed`  | Traitement terminé                     |
| `error`      | Erreur pendant le traitement           |
