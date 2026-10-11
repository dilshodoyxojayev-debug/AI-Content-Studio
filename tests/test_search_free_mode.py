import unittest
from unittest.mock import Mock, patch

from api_clients import GoogleClient


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

    def test_stickman_research_omits_search_tool_and_labels_dossier_unverified(self):
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
        self.assertIn("Live Google Search is disabled", facet_prompt)
        self.assertIn("Do not claim to have searched or verified sources", facet_prompt)
        self.assertIn("do not invent or name specific sources, institutions, citations, URLs", facet_prompt)
        news_client.get_news.assert_not_called()

        synthesis_prompt = synthesis.call_args.args[0]
        self.assertIn("PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES", synthesis_prompt)
        self.assertIn("no live search; not source-verified", synthesis_prompt)
        self.assertIn("Never invent source titles, organization names, citations, quotations, or URLs", synthesis_prompt)
        self.assertEqual(result, "Preliminary dossier")

    def test_other_styles_keep_existing_google_search_grounding_default(self):
        client = self._client("Documentary")
        news_client = Mock()
        news_client.get_news.return_value = "Recent headlines"
        with (
            patch("api_clients.requests.post", return_value=self._research_response()) as rest_post,
            patch.object(client, "_generate_text", return_value="Summary"),
        ):
            client.deep_research("A current topic", "English", news_client)

        request_payload = rest_post.call_args.kwargs["json"]
        self.assertEqual(request_payload["tools"], [{"google_search": {}}])
        self.assertIn("Using Google Search", request_payload["contents"][0]["parts"][0]["text"])
        news_client.get_news.assert_called_once_with("A current topic")

    def test_fact_check_script_and_revision_disclose_preliminary_review(self):
        client = self._client()
        with patch.object(client, "_generate_text", return_value="Review notes") as generate:
            client.fact_check_script("Draft narration", "English", "Unverified dossier")
            fact_check_prompt = generate.call_args.args[0]
            self.assertIn("NOT external fact-checking", fact_check_prompt)
            self.assertIn("human must verify", fact_check_prompt)
            self.assertIn("Never invent citations, source or organization names, or URLs", fact_check_prompt)

            client.revise_script("Draft narration", "Review notes", "English")
            revision_prompt = generate.call_args.args[0]
            self.assertIn("No live sources were consulted", revision_prompt)
            self.assertIn("Do not upgrade any claim to externally verified", revision_prompt)
            self.assertIn("Keep the need for human source verification clear", revision_prompt)
            self.assertIn("retain its exact 'PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES' status label", revision_prompt)

            client.generate_podcast_script(
                "Ghost Army",
                "PRELIMINARY — NOT VERIFIED AGAINST LIVE SOURCES",
                {
                    "CONTENT_STYLE": "Stickman History",
                    "LANGUAGE_ENABLED": True,
                    "PODCAST_LANGUAGE": "English",
                    "SINGLE_SPEAKER_CTA": False,
                },
            )
            script_prompt = generate.call_args.args[0]
            self.assertIn("generated without live web search", script_prompt)
            self.assertIn("do not present claims as confirmed", script_prompt)
            self.assertIn("check important claims against real historical sources", script_prompt)


if __name__ == "__main__":
    unittest.main()
