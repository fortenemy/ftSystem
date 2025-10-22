# Plan Działań (aktualny)

Data: 2025-09-10

## Zrealizowane
- Orkiestracja: forum wiadomości (system/user/agent), transcript w wynikach `MasterAgent`, metryki (latency/success), rundy i timeouty.
- Bezpieczeństwo: allowlista (`FTSYSTEM_ALLOWED_AGENTS`), limit rund (`FTSYSTEM_MAX_ROUNDS`), redakcja wrażliwych wzorców w transkryptach i historii.
- Voice S2S (MVP): `interactive --voice-in vosk --voice-out sapi5` + komenda `/rec`; brak zapisu audio; redakcja tekstu.
- Warstwowa konfiguracja: plik → ENV (`FTSYSTEM_*`) → CLI `--param key=value`; proste profile (`--profile`, `FTSYSTEM_PROFILE`).
- Wtyczki: ładowanie agentów przez entry points (`ftsystem.agents`), przewodnik `docs/plugins.md`.

## W toku / uwagi
- Jakość głosu: rozważyć Piper TTS (offline, PL) jako alternatywę dla SAPI5.
- UX nagrywania: beep start/stop, opcjonalny VAD i `--silence-timeout`.
- Rozszerzenie redakcji: poziomy (strict/normal), dodatkowe wzorce.

## Proponowane (do zatwierdzenia)
1) Voice UX & VAD: dodać beep i VAD, bez zapisu audio (domyślnie).
2) Redaction Levels: `--redact-level` + szerszy zestaw wzorców, testy.
3) Dokumentacja Voice: instrukcja instalacji Vosk/Piper w README z przykładami.

