#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# deploy.sh — Script de redéploiement MeetFlow AI en production
# Usage : bash deploy.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e   # Stop on first error

PROJECT_DIR="/root/Management-meeting-project"   # ← Adapter si besoin
COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║     MeetFlow AI — Déploiement Production     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Aller dans le dossier projet ──────────────────────────────────────────
cd "$PROJECT_DIR"
echo "📁 Dossier : $(pwd)"

# ── 2. Récupérer le dernier code ──────────────────────────────────────────────
echo ""
echo "📥 Récupération du code depuis GitHub..."
git pull origin main

# ── 3. Build des images ───────────────────────────────────────────────────────
echo ""
echo "🔨 Build des images Docker (backend + frontend)..."
docker compose -f "$COMPOSE_FILE" -f "$PROD_COMPOSE_FILE" build --no-cache backend frontend

# ── 4. Redémarrer les conteneurs ──────────────────────────────────────────────
echo ""
echo "🔄 Redémarrage des conteneurs..."
docker compose -f "$COMPOSE_FILE" -f "$PROD_COMPOSE_FILE" up -d

# ── 5. Attendre que le backend soit healthy ───────────────────────────────────
echo ""
echo "⏳ Attente du démarrage du backend (90s max)..."
RETRIES=18
for i in $(seq 1 $RETRIES); do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' reunion-backend 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "healthy" ]; then
        echo "   ✅ Backend healthy !"
        break
    fi
    echo "   [$i/$RETRIES] Status: $STATUS — attente 5s..."
    sleep 5
    if [ "$i" = "$RETRIES" ]; then
        echo "   ⚠️  Backend pas encore healthy après 90s. Vérifiez les logs :"
        echo "      docker logs reunion-backend --tail 30"
    fi
done

# ── 6. Seed des plans tarifaires ──────────────────────────────────────────────
echo ""
echo "💳 Synchronisation des plans tarifaires..."
docker exec reunion-backend python3 -c "
from database.seed_plans import seed_plans
seed_plans()
"

# ── 7. Rechargement nginx ─────────────────────────────────────────────────────
echo ""
echo "🔁 Rechargement de la configuration Nginx..."
docker exec reunion-nginx nginx -t && docker exec reunion-nginx nginx -s reload

# ── 8. Bilan final ────────────────────────────────────────────────────────────
echo ""
echo "🐳 État des conteneurs MeetFlow :"
docker ps --filter "name=reunion" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "🌐 URL : https://digireunionai.lynx-aiservice.online"
echo "📋 Logs backend : docker logs reunion-backend --tail 50"
echo ""
