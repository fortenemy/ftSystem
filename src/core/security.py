import os
import re
from typing import Iterable, List, Optional


class SecurityPolicy:
    """
    Simple security policy: allow-list of agent names and max rounds cap.
    Values can be sourced from environment variables for global defaults.
    """

    def __init__(self, allowed_agents: Optional[Iterable[str]] = None, max_rounds: int = 5) -> None:
        """Create a policy with optional allow-list and rounds cap."""
        self.allowed = set(a for a in (allowed_agents or [])) or None
        self.max_rounds = max(1, int(max_rounds))

    @classmethod
    def from_env(cls) -> "SecurityPolicy":
        """Instantiate a policy using environment variables for defaults."""
        allowed_env = os.environ.get("FTSYSTEM_ALLOWED_AGENTS")
        allowed = None
        if allowed_env:
            allowed = [a.strip() for a in allowed_env.split(",") if a.strip()]
        max_rounds = int(os.environ.get("FTSYSTEM_MAX_ROUNDS", "5"))
        return cls(allowed_agents=allowed, max_rounds=max_rounds)

    def filter_subagents(self, names: List[str]) -> List[str]:
        """Restrict the provided agent list based on the allow-list."""
        if self.allowed is None:
            return names
        return [n for n in names if n in self.allowed]

    def cap_rounds(self, rounds: int) -> int:
        """Clamp the requested rounds to the configured maximum."""
        try:
            r = int(rounds)
        except Exception:
            r = 1
        return max(1, min(r, self.max_rounds))


class Redactor:
    """
    Redact sensitive patterns from text for logs/history.

    Levels:
    - normal: basic patterns (API keys, emails)
    - strict: adds tokens, IPs, and long numeric sequences (e.g., CC numbers)
    """

    _level: str = "normal"

    # Base (normal) patterns
    _base_patterns = [
        # OpenAI-style keys: sk-XXXXX...
        (re.compile(r"sk-[A-Za-z0-9]{8,}"), "sk-<redacted>"),
        # Email addresses
        (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "<redacted-email>"),
    ]

    # Strict-only patterns (applied in addition to base)
    _strict_patterns = [
        # Bearer tokens
        (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{10,}\b"), "Bearer <redacted-token>"),
        # AWS Access Key ID
        (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<redacted-aws-key>"),
        # IPv4 addresses
        (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<redacted-ip>"),
        # Long numeric sequences (credit cards etc.) allowing spaces/dashes between digits
        (re.compile(r"\b(?:\d[ \-]?){13,19}\b"), "<redacted-number>"),
        # Generic secrets: api/secret/token/password=value (but skip 'Bearer ...')
        (re.compile(r"(?i)(api|secret|token|password)[=:]\s*(?!Bearer\b)([^\s,;]{6,})"), r"\1=<redacted>"),
        # Polish IBAN (PL + 26 digits)
        (re.compile(r"\bPL\d{26}\b"), "<redacted-iban>"),
        # Polish PESEL (11 digits)
        (re.compile(r"\b\d{11}\b"), "<redacted-pesel>"),
        # Polish NIP (10 digits, with optional separators) or EU VAT 'PL'+10 digits
        (re.compile(r"\b(?:\d{3}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}|PL\d{10})\b", re.IGNORECASE), "<redacted-nip>"),
    ]

    @classmethod
    def set_level(cls, level: str) -> None:
        """Persist the desired redaction level (normal or strict)."""
        val = (level or "").strip().lower()
        if val not in {"normal", "strict"}:
            val = "normal"
        cls._level = val

    @classmethod
    def get_level(cls) -> str:
        """Return the currently active redaction level."""
        return cls._level

    @classmethod
    def redact(cls, text: Optional[str]) -> Optional[str]:
        """Mask sensitive patterns in the provided text."""
        if text is None:
            return None
        out = str(text)
        patterns = list(cls._base_patterns)
        if cls._level == "strict":
            patterns.extend(cls._strict_patterns)
        for pat, repl in patterns:
            out = pat.sub(repl, out)
        return out
