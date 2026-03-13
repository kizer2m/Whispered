"""
Post-transcription translation engine.

Translates transcription segments into a target language using
deep-translator (free, no API key required, uses Google Translate).
"""
from __future__ import annotations

import traceback
from typing import Optional

from ui import info, success, warning, error, BRIGHT, CYAN, GREEN, YELLOW, RED, RESET, DIM

# ---------------------------------------------------------------------------
# Supported target languages (curated list for the menu)
# ---------------------------------------------------------------------------

# fmt: off
SUPPORTED_LANGUAGES: list[tuple[str, str]] = [
    ("ru",    "Russian"),
    ("en",    "English"),
    ("uk",    "Ukrainian"),
    ("de",    "German"),
    ("fr",    "French"),
    ("es",    "Spanish"),
    ("it",    "Italian"),
    ("pt",    "Portuguese"),
    ("pl",    "Polish"),
    ("nl",    "Dutch"),
    ("sv",    "Swedish"),
    ("no",    "Norwegian"),
    ("fi",    "Finnish"),
    ("cs",    "Czech"),
    ("sk",    "Slovak"),
    ("ro",    "Romanian"),
    ("hu",    "Hungarian"),
    ("bg",    "Bulgarian"),
    ("tr",    "Turkish"),
    ("ar",    "Arabic"),
    ("he",    "Hebrew"),
    ("ja",    "Japanese"),
    ("zh-CN", "Chinese (Simplified)"),
    ("zh-TW", "Chinese (Traditional)"),
    ("ko",    "Korean"),
    ("hi",    "Hindi"),
    ("fa",    "Persian"),
    ("id",    "Indonesian"),
    ("vi",    "Vietnamese"),
    ("th",    "Thai"),
]
# fmt: on

# Map BCP-47 / Whisper codes → deep-translator / Google codes
_LANG_CODE_MAP: dict[str, str] = {
    "zh":    "zh-CN",   # Whisper returns "zh" — map to Simplified
    "iw":    "he",      # Google historically used "iw" for Hebrew
}


def _normalize_code(code: str) -> str:
    """Normalise a language code for deep-translator."""
    return _LANG_CODE_MAP.get(code, code)


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

def _get_translator_cls():
    """Lazy import so missing dependency gives a friendly error."""
    try:
        from deep_translator import GoogleTranslator  # type: ignore
        return GoogleTranslator
    except ImportError:
        return None


def is_translation_available() -> bool:
    """Return True if deep-translator is installed."""
    return _get_translator_cls() is not None


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
) -> Optional[str]:
    """Translate *text* from *source_lang* to *target_lang*.

    Args:
        text:        The text to translate.
        source_lang: BCP-47 / ISO 639-1 source language code or 'auto'.
        target_lang: BCP-47 / ISO 639-1 target language code.

    Returns:
        Translated string, or None on failure.
    """
    if not text.strip():
        return text

    GoogleTranslator = _get_translator_cls()
    if GoogleTranslator is None:
        error("deep-translator is not installed. Run:  pip install deep-translator")
        return None

    src = _normalize_code(source_lang) if source_lang and source_lang != "auto" else "auto"
    tgt = _normalize_code(target_lang)

    try:
        translated = GoogleTranslator(source=src, target=tgt).translate(text)
        return translated
    except Exception as exc:  # noqa: BLE001
        error(f"Translation error: {exc}")
        return None


def translate_segments(
    segments: list[dict],
    source_lang: str,
    target_lang: str,
) -> list[dict]:
    """Translate every segment's text in-place (returns new list of dicts).

    Segments that fail translation keep their original text.
    """
    GoogleTranslator = _get_translator_cls()
    if GoogleTranslator is None:
        error("deep-translator is not installed. Run:  pip install deep-translator")
        return segments

    src = _normalize_code(source_lang) if source_lang and source_lang != "auto" else "auto"
    tgt = _normalize_code(target_lang)

    try:
        translator = GoogleTranslator(source=src, target=tgt)
    except Exception as exc:
        error(f"Failed to initialise translator: {exc}")
        return segments

    translated_segments: list[dict] = []
    total = len(segments)

    for idx, seg in enumerate(segments, 1):
        original_text = seg.get("text", "").strip()
        if not original_text:
            translated_segments.append(dict(seg))
            continue

        try:
            translated_text = translator.translate(original_text)
        except Exception as exc:  # noqa: BLE001
            warning(f"Segment {idx}/{total} translation failed: {exc}. Keeping original.")
            translated_text = original_text

        new_seg = dict(seg)
        new_seg["text"] = " " + (translated_text or original_text)
        translated_segments.append(new_seg)

        # Simple inline progress every 20 segments
        if idx % 20 == 0 or idx == total:
            print(f"\r  {DIM}Translating segments… {idx}/{total}{RESET}", end="", flush=True)

    if total > 0:
        print()  # newline after progress

    return translated_segments


# ---------------------------------------------------------------------------
# Language selection menu
# ---------------------------------------------------------------------------

def select_translation_language(current: Optional[str]) -> Optional[str]:
    """Interactive menu for selecting the post-transcription translation target.

    Returns the chosen language code, or None if translation should be disabled.
    """
    from ui import header, bullet, confirm  # local import to avoid circular deps

    header("Post-Transcription Translation")

    if not is_translation_available():
        error("deep-translator is not installed.")
        info("Install it with:  pip install deep-translator")
        info("Then restart the application.")
        return current

    current_display = current if current else "disabled"
    info(f"Current translation target: {BRIGHT}{current_display}{RESET}")
    info("This translation runs AFTER Whisper transcription.")
    info("The original transcription is preserved; translated files get a")
    info(f"  {DIM}_<lang>{RESET} suffix (e.g. output_ru.srt).")
    print()

    print(f"  {BRIGHT}{CYAN}[0]{RESET}  Disable translation (keep original language)")
    print()

    for i, (code, name) in enumerate(SUPPORTED_LANGUAGES, 1):
        marker = f"  {GREEN}← current{RESET}" if code == current else ""
        bullet(f"{name}  ({code}){marker}", i)

    print()
    try:
        raw = input("  Select target language (0 to disable): ").strip()
        choice = int(raw)
    except ValueError:
        warning("Invalid input. Translation target unchanged.")
        return current

    if choice == 0:
        success("Post-transcription translation disabled.")
        return None

    if 1 <= choice <= len(SUPPORTED_LANGUAGES):
        code, name = SUPPORTED_LANGUAGES[choice - 1]
        success(f"Translation target set: {name} ({code})")
        return code

    warning("Invalid selection. Translation target unchanged.")
    return current
