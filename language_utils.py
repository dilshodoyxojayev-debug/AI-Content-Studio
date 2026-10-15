"""Small language helpers shared by script generation and transcription."""


def effective_output_language(config: dict) -> str:
    """Return the language required for generated narration and related assets."""
    if config.get("CONTENT_STYLE") == "Stickman History":
        return "English"
    if not config.get("LANGUAGE_ENABLED", False):
        return "English"
    return config.get("PODCAST_LANGUAGE", "English") or "English"


_LANGUAGE_CODES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "urdu": "ur",
    "uzbek": "uz",
}


def format_language_instruction(language: str, output_name: str = "output text") -> str:
    """Return an explicit language instruction, including script constraints."""
    label = (language or "English").strip()
    normalized = label.casefold().replace("_", " ")

    if normalized.startswith("uzbek"):
        return (
            f"The {output_name} must be written in natural Uzbek using Cyrillic "
            "script only (Ўзбек тили, кирилл ёзуви). Do not use Latin transliteration."
        )
    if normalized == "urdu":
        return f"The {output_name} must be written in Roman Urdu."
    return f"The {output_name} must be written in {label}."


def whisper_language_code(language: str | None) -> str | None:
    """Convert the app's language labels to Whisper's language-code form."""
    if not language or language.strip().casefold() in {"auto", "automatic"}:
        return None

    label = language.strip()
    normalized = label.casefold().replace("_", " ")
    for name, code in _LANGUAGE_CODES.items():
        if normalized == name or normalized.startswith(f"{name} ("):
            return code
    return label
