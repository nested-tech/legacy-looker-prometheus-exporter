from unittest import TestCase
from unittest.mock import patch, MagicMock
from requests import Response

from looker_prometheus_exporter.looker_metric_fetcher import LookerMetricFetcher
from looker_prometheus_exporter.looker_auth import LookerAuthenticationError


class TestMetricFetcher(TestCase):
    @patch("requests.post")
    @patch("looker_prometheus_exporter.looker_metric_fetcher.LookerAuth.get_token", return_value="i_r_bad_token")
    def test_raises_auth_error_appropriately(self, mocked_token_getter, mocked_post):
        metric_fetcher = LookerMetricFetcher(
            client_id="i_r_id", client_secret="i_r_secret", looker_base_url="https://example.com", dashboard_id=42
        )

        mock_response = MagicMock(Response)
        mocked_post.return_value = mock_response

        mock_response.status_code = 401
        mock_response.json.return_value = {
            "message": "Requires authentication.",
            "documentation_url": "http://docs.looker.com/"
        }

        with self.assertRaises(LookerAuthenticationError):
            metric_fetcher._fetch_metrics()
