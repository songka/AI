"""User-confirmed client mappings for this NewAPI gateway.

These are intentionally declarative and distinct from protocol probe results.
They represent the user's stated gateway mapping, not inferred model abilities.
"""
from .models import ModelCapability

CODEX_MODELS = {"gpt-5.4-mini", "gpt-5.4", "gpt-5.6-luna"}
REAL_CLIENT_MODELS = {"gpt-5.6-luna", "deepseek-v4-pro", "deepseek-v4-flash"}


def apply_user_confirmed_mapping(model: ModelCapability) -> ModelCapability:
    model_id = model.model_id.strip().lower()
    confirmed: list[str] = []
    if model_id in CODEX_MODELS:
        confirmed.append("codex")
    if model_id in REAL_CLIENT_MODELS:
        confirmed.extend(("claude", "opencode"))
    model.manual_clients = confirmed
    return model
