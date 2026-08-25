"""Client serveur-vers-serveur pour l'API Riserva/Reeserva."""

import requests
from flask import current_app


class RiservaError(Exception):
    def __init__(self, message, status=502, code="PAYMENT_PROVIDER_ERROR", payload=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.payload = payload or {}


class RiservaClient:
    @staticmethod
    def is_configured():
        return bool(current_app.config.get("RISERVA_API_KEY", "").strip())

    @staticmethod
    def configuration_error():
        api_key = current_app.config.get("RISERVA_API_KEY", "").strip()
        if not api_key:
            return "Clé API Riserva absente."
        expected_mode = current_app.config.get("RISERVA_MODE", "SANDBOX").upper()
        key_mode = "SANDBOX" if api_key.startswith("rsk_test_") else "LIVE" if api_key.startswith("rsk_live_") else None
        if key_mode is None:
            return "Le format de la clé API Riserva n'est pas reconnu."
        if key_mode != expected_mode:
            return f"La clé Riserva est en mode {key_mode}, mais l'application est en mode {expected_mode}."
        return None

    @classmethod
    def is_ready(cls):
        return cls.configuration_error() is None

    @staticmethod
    def _request(method, path, payload=None, idempotency_key=None):
        api_key = current_app.config.get("RISERVA_API_KEY", "").strip()
        if not api_key:
            raise RiservaError(
                "Le fournisseur de paiement n'est pas encore configuré.",
                503,
                "PAYMENT_NOT_CONFIGURED",
            )
        configuration_error = RiservaClient.configuration_error()
        if configuration_error:
            raise RiservaError(configuration_error, 503, "PAYMENT_MODE_MISMATCH")
        headers = {"X-Api-Key": api_key, "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        try:
            response = requests.request(
                method,
                f"{current_app.config['RISERVA_BASE_URL'].rstrip('/')}/{path.lstrip('/')}",
                json=payload,
                headers=headers,
                timeout=current_app.config.get("RISERVA_TIMEOUT", 30),
            )
        except requests.RequestException as exc:
            raise RiservaError("Le service de paiement est temporairement indisponible.") from exc

        data = response.json() if response.content else {}
        if not response.ok:
            error = data.get("error") or {}
            message = data.get("message") or (error.get("message") if isinstance(error, dict) else error) or "Le paiement a été refusé par le fournisseur."
            code = error.get("code", "PAYMENT_PROVIDER_REJECTED") if isinstance(error, dict) else "PAYMENT_PROVIDER_REJECTED"
            raise RiservaError(str(message), 502, code, data)
        return data.get("data", data)

    @classmethod
    def quote(cls, payload):
        return cls._request("POST", "/payments/quote", payload)

    @classmethod
    def collect(cls, payload, idempotency_key):
        return cls._request("POST", "/payments/collect", payload, idempotency_key)

    @classmethod
    def get_payment(cls, payment_id):
        return cls._request("GET", f"/payments/{payment_id}")
