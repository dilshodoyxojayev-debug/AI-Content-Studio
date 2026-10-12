import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from api_clients import GoogleClient
from channel_presets import WWII_STICKMAN_SETTINGS
from config import load_config


ROOT = Path(__file__).resolve().parents[1]


class SearchFreeModeTests(unittest.TestCase):
    def _client(self, content_style="Stickman History", **extra_config):
        config = {
            "CONTENT_STYLE": content_style,
            "TEXT_ENGINE": "Gemini API",
            "LANGUAGE_ENABLED": True,
            "PODCAST_LANGUAGE": "English",
        }
        config.update(extra_config)
        return GoogleClient(config)

    @staticmethod
    def _research_response():
        response = Mock()
        response.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "Preliminary analysis for the topic."}]}}
            ]
        }
        return response

    def test_general_styles_default_to_live_search_but_wwii_preset_is_search_free(self):
        with (
            patch("config.os.path.exists", return_value=False),
            patch("config.save_config"),
        ):
            fresh_config = load_config()
        self.assertTrue(fresh_config["GOOGLE_SEARCH_GROUNDING"])

        with (
            patch("config.os.path.exists", return_value=True),
            patch("builtins.open", return_value=StringIO('{"CONTENT_STYLE": "Stickman History"}')),
            patch("config.save_config"),
        ):
            historical_config = load_config()
        self.assertFalse(historical_config["GOOGLE_SEARCH_GROUNDING"])
        self.assertFalse(WWII_STICKMAN_SETTINGS["GOOGLE_SEARCH_GROUNDING"])

        client = self._client("Documentary")
        news_client = Mock()
        news_client.get_news.return_value = "Recent headlines"
        with (
            patch("api_clients.requests.post", return_value=self._research_response()) as rest_post,
            patch.object(client, "_generate_text", return_value="Summary"),
        ):
            client.deep_research("A science topic", "English", news_client)

        request_payload = rest_post.call_args.kwargs["json"]
        self.assertEqual(request_payload["tools"], [{"google_search": {}}])
        self.assertIn("Using Google Search", request_payload["contents"][0]["parts"][0]["text"])
        news_client.get_news.assert_called_once_with("A science topic")

        historical_client = self._client()
        historical_news_client = Mock()
        with (
            patch("api_clients.requests.post", return_value=self._research_response()) as rest_post,
            patch.object(historical_client, "_generate_text", return_value="Preliminary dossier"),
        ):
            historical_client.deep_research("Ghost Army", "English", historical_news_client)
        self.assertNotIn("tools", rest_post.call_args.kwargs["json"])
        historical_news_client.get_news.assert_not_called()

    def test_search_free_can_be_selected_for_any_style_and_labels_research_preliminary(self):
        client = self._client("Documentary", GOOGLE_SEARCH_GROUNDING=False)
        news_client = Mock()
        with (
            patch("api_clients.requests.post", return_value=self._research_response()) as rest_post,
            patch.object(client, "_generate_text", return_value="Preliminary dossier") as synthesis,
        ):
            client.deep_research("A science topic", "English", news_client)

        request_payload = rest_post.call_args.kwargs["json"]
        self.assertNotIn("tools", request_payload)
        facet_prompt = request_payload["contents"][0]["parts"][0]["text"]
        self.assertIn("Live Google Search is disabled", facet_prompt)
        self.assertIn("do not invent or name specific sources, institutions, citations, URLs", facet_prompt)
        news_client.get_news.assert_not_called()

        synthesis_prompt = synthesis.call_args.args[0]
        self.assertIn("PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES", synthesis_prompt)
        self.assertIn("no live Search or NewsAPI; not source-verified", synthesis_prompt)
        self.assertIn("Never invent source or organization names, source titles, citations", synthesis_prompt)

    def test_search_free_stickman_research_omits_tool_and_historical_news(self):
        client = self._client()
        news_client = Mock()
        with (
            patch("api_clients.requests.post", return_value=self._research_response()) as rest_post,
            patch.object(client, "_generate_text", return_value="Preliminary dossier") as synthesis,
        ):
            result = client.deep_research("Ghost Army", "English", news_client)

        request_payload = rest_post.call_args.kwargs["json"]
        self.assertNotIn("tools", request_payload)
        facet_prompt = request_payload["contents"][0]["parts"][0]["text"]
        self.assertIn("Do not claim to have searched or verified sources", facet_prompt)
        self.assertIn("Identify evidence gaps", facet_prompt)
        news_client.get_news.assert_not_called()

        synthesis_prompt = synthesis.call_args.args[0]
        self.assertIn("PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES", synthesis_prompt)
        self.assertIn("Never invent source or organization names, source titles, citations", synthesis_prompt)
        self.assertEqual(result, "Preliminary dossier")

    def test_fact_check_revision_and_script_prompts_disclose_search_free_status(self):
        client = self._client("Documentary", GOOGLE_SEARCH_GROUNDING=False)
        with patch.object(client, "_generate_text", return_value="Review notes") as generate:
            client.fact_check_script("Draft narration", "English", "Unverified dossier")
            fact_check_prompt = generate.call_args.args[0]
            self.assertIn("NOT external fact-checking", fact_check_prompt)
            self.assertIn("human must verify", fact_check_prompt)
            self.assertIn("Never invent source/organization names, citations, titles", fact_check_prompt)

            client.revise_script("Draft narration", "Review notes", "English")
            revision_prompt = generate.call_args.args[0]
            self.assertIn("No live Search or NewsAPI sources were consulted", revision_prompt)
            self.assertIn("Do not upgrade claims to externally verified", revision_prompt)
            self.assertIn("Keep human source verification necessary", revision_prompt)
            self.assertIn("retain its exact 'PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES' status label", revision_prompt)

            client.generate_podcast_script(
                "Why did the Aral Sea shrink?",
                "PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES",
                {
                    "CONTENT_STYLE": "Documentary",
                    "LANGUAGE_ENABLED": True,
                    "PODCAST_LANGUAGE": "English",
                    "SINGLE_SPEAKER_CTA": False,
                    "GOOGLE_SEARCH_GROUNDING": False,
                },
            )
            script_prompt = generate.call_args.args[0]
            self.assertIn("no live Google Search or NewsAPI sources were used", script_prompt)
            self.assertIn("Do not present claims as externally confirmed", script_prompt)
            self.assertIn("verify important claims against real sources", script_prompt)

    def test_settings_include_search_grounding_toggle(self):
        source = " ".join((ROOT / "main.py").read_text(encoding="utf-8").split())
        self.assertIn("Use live Google Search grounding", source)
        self.assertIn('self.config["GOOGLE_SEARCH_GROUNDING"] = self.google_search_grounding_var.get()', source)
        self.assertIn("self.google_search_grounding_var.set(", source)
        self.assertIn('cfg.get("GOOGLE_SEARCH_GROUNDING", cfg.get("CONTENT_STYLE", "Podcast") != "Stickman History")', source)
        self.assertIn('self.google_search_grounding_var.set(settings.get("GOOGLE_SEARCH_GROUNDING", False))', source)


if __name__ == "__main__":
    unittest.main()
