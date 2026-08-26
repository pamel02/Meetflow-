"""
services/chat_service.py - Assistant IA conversationnel (RAG)
Répond aux questions sur l'ensemble des réunions ou sur une réunion spécifique.
"""

from ai.nvidia_client import NvidiaNimClient
from ai.rag import RAGService
from repositories.meeting_repository import MeetingRepository


class ChatService:

    @staticmethod
    def chat_global(user, data: dict) -> tuple[dict, int]:
        """
        Répond à une question portant sur TOUTES les réunions de l'utilisateur.
        Exemple : "Quels sujets reviennent le plus souvent ?"
        """
        from services.billing_service import BillingService

        entitlement = BillingService.entitlement(user, "chat")
        if entitlement:
            return entitlement

        question = (data.get("question") or "").strip()
        if not question:
            return {"error": "La question est requise."}, 400

        # Récupère le contexte pertinent via RAG (ChromaDB)
        context_chunks = RAGService.search_global(
            user_id=user.id,
            query=question,
            n_results=5
        )

        # Construit la réponse avec NVIDIA NIM
        answer = NvidiaNimClient.answer_with_context(
            question=question,
            context_chunks=context_chunks,
            scope="global"
        )

        return {
            "question": question,
            "answer":   answer,
            "sources":  [c["meeting_id"] for c in context_chunks if "meeting_id" in c],
        }, 200

    @staticmethod
    def chat_meeting(user, meeting_id: int, data: dict) -> tuple[dict, int]:
        """
        Répond à une question sur UNE réunion spécifique.
        Exemple : "Qui devait finir le backend ?"
        """
        from services.billing_service import BillingService

        entitlement = BillingService.entitlement(user, "chat")
        if entitlement:
            return entitlement

        question = (data.get("question") or "").strip()
        if not question:
            return {"error": "La question est requise."}, 400

        meeting = MeetingRepository.find_by_id_and_user(meeting_id, user.id)
        if not meeting:
            return {"error": "Réunion introuvable."}, 404

        # Récupère le contexte pertinent uniquement pour cette réunion
        context_chunks = RAGService.search_meeting(
            meeting_id=meeting_id,
            query=question,
            n_results=5
        )

        answer = NvidiaNimClient.answer_with_context(
            question=question,
            context_chunks=context_chunks,
            scope="meeting",
            meeting_title=meeting.title
        )

        return {
            "meeting_id": meeting_id,
            "question":   question,
            "answer":     answer,
        }, 200
