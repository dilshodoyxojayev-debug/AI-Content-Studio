from pathlib import Path
import unittest

from security_utils import redact_sensitive_text


ROOT = Path(__file__).resolve().parents[1]


class ApiKeySafetyTests(unittest.TestCase):
    def test_redacts_key_query_parameters(self):
        message = "429 for https://example.test/generate?key=AIzaSy-test-secret&alt=json"

        redacted = redact_sensitive_text(message)

        self.assertNotIn("AIzaSy-test-secret", redacted)
        self.assertIn("?key=[REDACTED]&alt=json", redacted)

    def test_redacts_known_secret_values_in_arbitrary_text(self):
        message = "Request failed with secret-value-123 in the details"

        redacted = redact_sensitive_text(message, "secret-value-123")

        self.assertEqual(redacted, "Request failed with [REDACTED] in the details")

    def test_gemini_rest_calls_send_key_in_header_not_url(self):
        source = (ROOT / "api_clients.py").read_text(encoding="utf-8")

        self.assertNotIn("?key={self.api_key}", source)
        self.assertEqual(source.count('"x-goog-api-key": self.api_key'), 2)


if __name__ == "__main__":
    unittest.main()
