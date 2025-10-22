from __future__ import annotations

import queue
from dataclasses import dataclass
import time
from pathlib import Path
from typing import Optional


@dataclass
class STTConfig:
    model_dir: Path
    lang: str = "pl-PL"
    samplerate: int = 16000
    max_seconds: int = 8
    device_index: Optional[int] = None
    beep: bool = True
    silence_timeout_sec: Optional[float] = None  # if set, stop after this many seconds of silence


class VoskSTT:
    """
    Offline STT using Vosk engine. Imports heavy deps lazily.
    """

    def __init__(self, cfg: STTConfig) -> None:
        """Store configuration used for subsequent recordings."""
        self.cfg = cfg

    def _ensure(self) -> None:
        """Verify that required STT dependencies are available."""
        try:
            import vosk  # type: ignore
        except Exception as e:
            raise RuntimeError(
                f"Vosk is not available. Install 'vosk' and download a PL model. Error: {e}"
            )
        try:
            import sounddevice  # type: ignore # noqa: F401
        except Exception as e:
            raise RuntimeError(f"sounddevice is required for STT. Error: {e}")

    @staticmethod
    def _beep() -> None:
        """Best-effort short beep without extra deps."""
        try:
            import sys
            if sys.platform.startswith("win"):
                try:
                    import winsound  # type: ignore
                    winsound.Beep(1000, 120)
                    return
                except Exception:
                    pass
            # Fallback ASCII bell (may be ignored by some terminals)
            print("\a", end="", flush=True)
        except Exception:
            # Never crash on beep
            pass

    def listen_once(self) -> str:
        """Record up to max_seconds from mic and return recognized text (may be empty).

        If `silence_timeout_sec` is set, recording will stop early after that many seconds
        of (approximate) silence. Uses Vosk partial results as a crude VAD signal.
        """
        self._ensure()
        import sounddevice as sd  # type: ignore
        import vosk  # type: ignore
        import json

        model_path = str(self.cfg.model_dir)
        if not Path(model_path).exists():
            raise RuntimeError(
                f"Vosk model directory not found: {model_path}. Set --stt-model-dir or FTSYSTEM_VOSK_MODEL."
            )

        model = vosk.Model(model_path)
        q: "queue.Queue[bytes]" = queue.Queue()

        def callback(indata, frames, time, status):  # noqa: ANN001, ANN201
            if status:
                # non-fatal
                pass
            q.put(bytes(indata))

        if self.cfg.beep:
            self._beep()
        start_time = time.monotonic()
        with sd.RawInputStream(
            samplerate=self.cfg.samplerate,
            blocksize=8000,
            device=self.cfg.device_index,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            rec = vosk.KaldiRecognizer(model, self.cfg.samplerate)
            text_parts = []
            seconds = 0.0
            silence_for = 0.0
            speech_started = False
            # Rough estimate per q.get() block (depends on blocksize/samplerate)
            est_block_sec = 0.5
            while seconds < float(self.cfg.max_seconds):
                data = q.get()
                seconds += est_block_sec
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    if res.get("text"):
                        text_parts.append(res["text"])
                        speech_started = True
                        silence_for = 0.0
                else:
                    # consider partial result as voice activity if non-empty
                    try:
                        pres = json.loads(rec.PartialResult())
                        if pres.get("partial"):
                            speech_started = True
                            silence_for = 0.0
                        else:
                            silence_for += est_block_sec
                    except Exception:
                        silence_for += est_block_sec
                # Optional early stop on silence once speech has started
                if (
                    speech_started
                    and self.cfg.silence_timeout_sec is not None
                    and silence_for >= float(self.cfg.silence_timeout_sec)
                ):
                    break
            final = rec.FinalResult()
            try:
                res_final = json.loads(final)
                if res_final.get("text"):
                    text_parts.append(res_final["text"])
            except Exception:
                pass
        if self.cfg.beep:
            self._beep()
        return " ".join(tp.strip() for tp in text_parts if tp.strip())


class SapiTTS:
    """
    TTS via pyttsx3 (SAPI5 on Windows). Imports lazily.
    """

    def __init__(self, lang: str = "pl-PL") -> None:
        """Initialise the engine and pick a best-effort matching voice."""
        self.lang = lang
        try:
            import pyttsx3  # type: ignore
        except Exception as e:
            raise RuntimeError(f"pyttsx3 not available for TTS. Install it. Error: {e}")
        self.engine = pyttsx3.init()
        # Try to select a voice matching language
        try:
            voices = self.engine.getProperty("voices")
            for v in voices:
                if self.lang.split("-")[0].lower() in (v.name or "").lower() or (
                    v.languages and self.lang.encode() in v.languages
                ):
                    self.engine.setProperty("voice", v.id)
                    break
        except Exception:
            pass

    def speak(self, text: str) -> None:
        """Vocalise the supplied text if it is non-empty."""
        if not text:
            return
        self.engine.say(text)
        self.engine.runAndWait()
