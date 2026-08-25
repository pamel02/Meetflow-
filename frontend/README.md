# Assistant IA de Reunion — Frontend

Frontend React + Vite + Tailwind CSS v4 pour l'Assistant IA de Reunion, connecte aux 32 endpoints
du backend Flask decrits dans la documentation API (auth, reunions, audio, donnees IA, chat RAG,
export, monitoring).

## Demarrage

```bash
npm install
cp .env.example .env   # ajustez VITE_API_BASE_URL si besoin
npm run dev
```

## Build de production

```bash
npm run build
npm run preview
```

## Structure

```
src/
  components/   Composants reutilisables (Button, Card, Modal, MeetingCard, AudioRecorder, ChatBox...)
  pages/        Login, Register, Dashboard, MeetingDetail, Assistant, History, Settings
  hooks/        useAudioRecorder (segmentation 60s / chevauchement 5s), useMeetingStatus (polling), useBackendHealth
  context/      AuthContext (session JWT 12h), ToastContext (notifications)
  services/     Un module par domaine d'API (7 domaines, 32 endpoints)
  utils/        Formatage de dates/durees, libelles de statuts
```

## Palette

Bordeaux / brun / taupe fonce exclusivement — aucune couleur vive, aucun bleu, aucun or. Aucune
bibliotheque d'icones ni d'animation : la hierarchie visuelle repose sur la typographie
(Fraunces / IBM Plex Sans / IBM Plex Mono), les bordures et les espacements.
