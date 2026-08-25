from types import SimpleNamespace

import pytest

from ai import nvidia_client


class _FakeCompletions:
    def __init__(self, content: str):
        self.content = content
        self.options = None

    def create(self, **options):
        self.options = options
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeClient:
    def __init__(self, content: str):
        self.completions = _FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


def test_generate_uses_nemotron_and_thinking_options(monkeypatch):
    fake_client = _FakeClient("Compte rendu généré")
    monkeypatch.setattr(nvidia_client, "_client", lambda: fake_client)

    result = nvidia_client.generate("Transcription", system="Assistant", temperature=0.1)

    assert result == "Compte rendu généré"
    options = fake_client.completions.options
    assert options["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert options["messages"] == [
        {"role": "system", "content": "Assistant"},
        {"role": "user", "content": "Transcription"},
    ]
    assert options["stream"] is False
    assert options["extra_body"]["chat_template_kwargs"]["enable_thinking"] is True
    assert options["extra_body"]["reasoning_budget"] == 16384


def test_client_requires_nvidia_api_key(monkeypatch):
    monkeypatch.setattr(nvidia_client, "NVIDIA_API_KEY", "")

    with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
        nvidia_client._client()


def test_generate_can_disable_thinking_for_structured_tasks(monkeypatch):
    fake_client = _FakeClient("{}")
    monkeypatch.setattr(nvidia_client, "_client", lambda: fake_client)

    nvidia_client.generate(
        "Rapport JSON",
        max_tokens=4096,
        enable_thinking=False,
        reasoning_budget=0,
    )

    options = fake_client.completions.options
    assert options["max_tokens"] == 4096
    assert options["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False
    assert options["extra_body"]["reasoning_budget"] == 0


def test_generate_json_removes_markdown_fence(monkeypatch):
    monkeypatch.setattr(
        nvidia_client,
        "generate",
        lambda *args, **kwargs: '```json\n{"decisions": []}\n```',
    )

    assert nvidia_client.generate_json("prompt") == {"decisions": []}
