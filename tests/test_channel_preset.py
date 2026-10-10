import ast
from pathlib import Path
import unittest

from channel_presets import (
    WWII_STICKMAN_PRESET_NAME,
    WWII_STICKMAN_SAMPLE_TOPIC,
    WWII_STICKMAN_SETTINGS,
)
from language_utils import effective_output_language, format_language_instruction, whisper_language_code


ROOT = Path(__file__).resolve().parents[1]


def load_module_constant(filename, name):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Could not find constant {name!r} in {filename}")


class ChannelPresetTests(unittest.TestCase):
    def test_wwii_stickman_preset_is_fact_first_and_in_english(self):
        self.assertEqual(WWII_STICKMAN_PRESET_NAME, "WWII Stickman")
        self.assertEqual(WWII_STICKMAN_SETTINGS["CONTENT_STYLE"], "Stickman History")
        self.assertEqual(WWII_STICKMAN_SETTINGS["PODCAST_LANGUAGE"], "English")
        self.assertTrue(WWII_STICKMAN_SETTINGS["LANGUAGE_ENABLED"])
        self.assertEqual(WWII_STICKMAN_SETTINGS["TEXT_ENGINE"], "Gemini API")
        self.assertEqual(WWII_STICKMAN_SETTINGS["IMAGE_ENGINE"], "Gemini API")
        self.assertEqual(WWII_STICKMAN_SETTINGS["AUDIO_ENGINE"], "Gemini API")
        self.assertTrue(WWII_STICKMAN_SETTINGS["FACT_CHECK_ENABLED"])
        self.assertTrue(WWII_STICKMAN_SETTINGS["SINGLE_SPEAKER_CTA"])
        self.assertIn("Ghost Army", WWII_STICKMAN_SAMPLE_TOPIC)
        self.assertIn("subscribe", WWII_STICKMAN_SETTINGS["SUBSCRIBE_MESSAGE"].casefold())

    def test_stickman_history_always_generates_english(self):
        config = {
            "CONTENT_STYLE": "Stickman History",
            "LANGUAGE_ENABLED": True,
            "PODCAST_LANGUAGE": "Uzbek (Cyrillic)",
        }
        self.assertEqual(effective_output_language(config), "English")

    def test_style_is_available_in_the_gui_and_defines_stickman_visuals(self):
        content_styles = load_module_constant("main.py", "CONTENT_STYLES")
        style_profiles = load_module_constant("api_clients.py", "STYLE_PROFILES")
        self.assertIn("Stickman History", content_styles)
        self.assertIn("Stickman History", style_profiles)
        self.assertIn("stick-figure", style_profiles["Stickman History"]["video"])
        self.assertIn("reputable", style_profiles["Stickman History"]["research"])

    def test_uzbek_instruction_requires_cyrillic_not_latin_transliteration(self):
        instruction = format_language_instruction("Uzbek (Cyrillic)", "entire script")
        self.assertIn("Cyrillic", instruction)
        self.assertIn("Do not use Latin transliteration", instruction)

    def test_whisper_language_labels_are_normalized(self):
        self.assertEqual(whisper_language_code("Uzbek (Cyrillic)"), "uz")
        self.assertEqual(whisper_language_code("Urdu"), "ur")
        self.assertEqual(whisper_language_code("English"), "en")
        self.assertIsNone(whisper_language_code("Auto"))


if __name__ == "__main__":
    unittest.main()
