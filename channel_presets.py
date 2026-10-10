"""Ready-to-use channel profiles for the AI Content Studio."""

WWII_STICKMAN_PRESET_NAME = "WWII Stickman"
WWII_STICKMAN_SAMPLE_TOPIC = (
    "Ghost Army: How a fake army fooled the enemy in World War II"
)

# App.apply_preset applies these defaults to the GUI and pipeline config.
WWII_STICKMAN_SETTINGS = {
    "CHANNEL_NAME": "Stickman: WWII Secrets",
    "CONTENT_STYLE": "Stickman History",
    "PODCAST_LANGUAGE": "English",
    "LANGUAGE_ENABLED": True,
    "TEXT_ENGINE": "Gemini API",
    "IMAGE_ENGINE": "Gemini API",
    "AUDIO_ENGINE": "Gemini API",
    "HOST_NAME": "The Historian",
    "HOST_PERSONA": (
        "An engaging, curious and responsible history narrator. Explain complex "
        "events clearly, build suspense without exaggeration, distinguish "
        "documented facts from disputed claims, and treat the human cost of war "
        "with respect."
    ),
    "VOICE_NAME": "Autonoe",
    "SPEAKER1": "Autonoe",
    "PODCAST_STYLE": "Documentary",
    "STORY_ARC": "Three-Act Structure",
    "SCRIPT_LENGTH": "Medium (~5 minutes)",
    "VIDEO_ASPECT_RATIO": "16:9 (Horizontal)",
    "VIDEO_PROMPT_BASE_STYLE": (
        "Consistent 2D hand-drawn stick-figure animation: simple black line "
        "characters with round heads and expressive poses, historically grounded "
        "WWII uniforms, maps and props, restrained charcoal, sepia and olive "
        "palette, cinematic framing, smooth readable motion. Educational and "
        "respectful; no gore, no glorification of war or extremist ideology."
    ),
    "IMAGE_PROMPT_STYLE": (
        "Consistent 2D hand-drawn WWII stickman illustration, simple black-line "
        "figures with expressive poses, historically grounded uniforms, maps and "
        "props, restrained sepia and olive palette, cinematic composition, "
        "educational and respectful, no gore or glorification."
    ),
    "BG_MODE": "Image Slideshow",
    "IMAGE_COUNT": 8,
    "IMAGE_GENERATION_INTERVAL": 0,
    "VIDEO_CLIP_COUNT": 1,
    "FACT_CHECK_ENABLED": True,
    "CAPTION_ENABLED": True,
    "GENERATE_METADATA": True,
    "GENERATE_THUMBNAIL": True,
    "GENERATE_TIMESTAMPS": True,
    "ADD_MUSIC": False,
    "GENERATE_SNIPPETS": False,
    "SINGLE_SPEAKER_CTA": True,
    "SUBSCRIBE_COUNT": 1,
    "SUBSCRIBE_MESSAGE": (
        "Subscribe to Stickman: WWII Secrets — let's uncover the next "
        "hidden story together!"
    ),
    "SUBSCRIBE_RANDOM": False,
}
