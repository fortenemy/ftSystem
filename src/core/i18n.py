"""
Lightweight internationalisation helper for CLI messages.

The project does not rely on external gettext tooling; instead we keep a small
dictionary of translated message templates and expose a simple translation
function. Default language is English, with optional Polish strings.
"""

from __future__ import annotations

from typing import Dict


class I18N:
    """Simple runtime-configurable translation registry."""

    _lang: str = "en"
    _messages: Dict[str, Dict[str, str]] = {
        "agent_not_found": {
            "en": "Agent '{agent}' not found. Available: {available}",
            "pl": "Agent '{agent}' nie został znaleziony. Dostępni: {available}",
        },
        "no_history": {
            "en": "No history for date: {date}",
            "pl": "Brak historii dla daty: {date}",
        },
        "clearing_refused": {
            "en": "Refusing to clear without --yes",
            "pl": "Odmowa czyszczenia bez parametru --yes",
        },
        "pruning_refused": {
            "en": "Refusing to prune without --yes",
            "pl": "Odmowa przycinania bez parametru --yes",
        },
    }

    @classmethod
    def set_language(cls, lang: str) -> None:
        """Switch the active language (defaults to English)."""
        if not lang:
            cls._lang = "en"
            return
        norm = lang.lower()
        if norm not in {"en", "pl"}:
            norm = "en"
        cls._lang = norm

    @classmethod
    def get_language(cls) -> str:
        """Return the current language code."""
        return cls._lang

    @classmethod
    def translate(cls, key: str, **kwargs) -> str:
        """Translate the message template for the current language."""
        bundle = cls._messages.get(key, {})
        template = bundle.get(cls._lang) or bundle.get("en") or key
        try:
            return template.format(**kwargs)
        except Exception:
            return template


def t(key: str, **kwargs) -> str:
    """Shortcut for I18N.translate()."""
    return I18N.translate(key, **kwargs)

