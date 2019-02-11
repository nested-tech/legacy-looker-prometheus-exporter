import json
import os
import requests
import time

from prometheus_client import start_http_server, Summary
from datetime import datetime, timedelta


class LookerAuth(object):
    def __init__(self):
        self._client_id = os.getenv("LOOKER_CLIENT_ID")
        self._client_secret = os.getenv("LOOKER_CLIENT_SECRET")

        self._auth_token = None
        self._expiry_time = datetime.now()

        self._authenticate()

    def _authenticate(self):
        params = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        response = requests.post('https://nested.eu.looker.com:19999/api/3.0/login', params=params)
        credentials = response.json()

        self._auth_token = credentials["access_token"]
        self._expiry_time = datetime.now() + timedelta(seconds=credentials["expires_in"] - 60)

    def get_token(self):
        if datetime.now() >= self._expiry_time:
            self._authenticate()

        return self._auth_token


class LookerMetricFetcher(object):
    def __init__(self):
        self._summary = Summary('looker_dashboard_performance', 'Performance of Looker dashboard')
        self._auth = LookerAuth()
        self._max_event_id = 0

    def observe(self):
        while True:
            time.sleep(5)
            self._fetch_metrics()

    def _fetch_metrics(self):
        data = json.dumps({
            "model": "i__looker",
            "view": "dashboard_performance",
            "fields": ["dashboard_performance.seconds_until_last_tile_finished_rendering", "event.id"],
            "filters": {
                "history.real_dash_id": "22",
                "dashboard_performance.seconds_until_last_tile_finished_rendering": "NOT NULL",
                "dashboard_performance.last_event_at_date": "10 minutes"
            }
        })

        headers = {'Authorization': 'Bearer {}'.format(self._auth.get_token())}
        response = requests.post('https://nested.eu.looker.com:19999/api/3.0/queries/run/json', headers=headers,
                                 data=data).content.decode('UTF-8')

        for result in json.loads(response):
            if int(result["event.id"]) > self._max_event_id:
                self._max_event_id = result["event.id"]
                self._summary.observe(result["dashboard_performance.seconds_until_last_tile_finished_rendering"])


if __name__ == '__main__':
    lmf = LookerMetricFetcher()
    start_http_server(8000)

    lmf.observe()
