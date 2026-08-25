from types import SimpleNamespace

from ai.rag import _lexical_search
from repositories.summary_repository import SummaryRepository


def test_lexical_fallback_returns_relevant_transcript_chunks(monkeypatch):
    meeting = SimpleNamespace(id=42, title="Budget produit")
    transcript = SimpleNamespace(
        full_text=(
            "Le budget marketing est validé pour le prochain trimestre. "
            "La décision finale attribue la campagne à Marie. "
        ) * 12
    )
    monkeypatch.setattr(
        SummaryRepository,
        "get_transcript",
        staticmethod(lambda meeting_id: transcript if meeting_id == 42 else None),
    )

    results = _lexical_search([meeting], "Quelle décision concerne le budget marketing ?", 3)

    assert results
    assert results[0]["meeting_id"] == 42
    assert "budget marketing" in results[0]["text"]
    assert results[0]["relevance"] > 0
