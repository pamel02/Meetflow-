import json

from ai.nvidia_client import NvidiaNimClient
from ai.summarizer import generate_full_report


def test_report_prompt_prioritizes_synthesis_and_normalizes_output(monkeypatch):
    captured = {}
    verbose_summary = " ".join(f"mot{i}" for i in range(220))
    duplicate = {"content": "Organiser le contrôle qualité", "responsible": None, "deadline": "dans trois semaines"}
    raw = json.dumps({
        "general_summary": verbose_summary,
        "participants": ["Collin"],
        "conclusion": "La production doit être sécurisée avant la livraison.",
        "decisions": [{"content": "Réaliser un contrôle qualité avant la livraison", "context": "Éviter un contrôle direct par le client"}],
        "actions": [duplicate, duplicate],
        "questions": [],
        "risks": [{"content": "Une livraison tardive réduirait la marge", "severity": "élevé", "mitigation": None}],
    }, ensure_ascii=False)

    def fake_generate(prompt, system=None, **_kwargs):
        captured["prompt"] = prompt
        captured["system"] = system
        return raw

    monkeypatch.setattr(NvidiaNimClient, "generate", staticmethod(fake_generate))
    report = generate_full_report("Discussion sur la production des instruments et le contrôle qualité.")

    assert "Ne recopie jamais la transcription" in captured["system"]
    assert len(report["general_summary"].split()) == 160
    assert len(report["actions"]) == 1
    assert report["decisions"][0]["content"].startswith("Réaliser un contrôle")
    assert report["risks"][0]["severity"] == "élevé"
