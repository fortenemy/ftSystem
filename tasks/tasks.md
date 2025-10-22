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

---

## Aktualizacja 2025-10-22

- Dodano kompleksowe docstringi do publicznych metod w `src/agents`, `src/core` i pomocach CLI.
- Uzupełniono adnotacje typów w funkcjach pomocniczych; doprecyzowano sygnatury.
- Poprawiono komunikaty błędów (typ wyjątku + kontekst: ścieżki plików, nazwy agentów); bez ujawniania sekretów.
- README zyskało sekcję "Developer Guide"; zaktualizowano "Code Review Summary" (status wykonania rekomendacji).
- Rozbudowano logowanie debug w krytycznych ścieżkach (`MasterAgent`, `_build_agent_config`, CLI `run`).
- Poszerzono testy orkiestracji o scenariusze allowlist oraz obsługę błędów subagentów.
- Dodano `docs/architecture.md` z diagramami Mermaid i link w README.
- Dodano profilowanie `perf profile` do CLI (wielokrotne uruchomienia, statystyki czasu).
- Eksport metryk Prometheus (`--metrics-path`) z danymi o rundach i subagentach.
- Warstwa i18n: globalny `--lang` (en/pl) + tłumaczenia komunikatów CLI.
