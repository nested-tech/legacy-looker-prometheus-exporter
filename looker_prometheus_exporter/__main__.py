import json
import os
import requests
import time
import logging

from prometheus_client import start_http_server, Summary
from datetime import datetime, timedelta


class LookerAuth(object):
    def __init__(self, *, client_id, client_secret, looker_base_url):
        self._client_id = client_id
        self._client_secret = client_secret
        self._login_url = "{}/api/3.0/login".format(looker_base_url)

        self._auth_token = None
        self._expiry_time = datetime.now()

        self._authenticate()

    def _authenticate(self):
        logging.debug("No up-to-date token. Authenticating now.")
        params = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        response = requests.post(self._login_url, params=params)
        credentials = response.json()

        try:
            self._auth_token = credentials["access_token"]
            self._expiry_time = datetime.now() + timedelta(seconds=credentials["expires_in"] - 60)
            logging.debug("New credentials succesfully fetched.")
        except:
            logging.error("""
Couldn't find credentials in Looker response:
    {}
If you're seeing 'Not found' this could be because of an incorrect client_id/client_secret.
            """.format(credentials))
            raise

    def get_token(self):
        if datetime.now() >= self._expiry_time:
            self._authenticate()

        return self._auth_token


class LookerMetricFetcher(object):
    def __init__(self, *, client_id, client_secret, fetch_interval, looker_base_url, dashboard_id):
        self._interval = fetch_interval * 60
        self._query_url = "{}/api/3.0/queries/run/json".format(looker_base_url)
        self._summary = Summary(
            "looker_dashboard_{}_render_time".format(dashboard_id),
            "Time until last tile of dashboard {} finished rendering".format(dashboard_id)
        )

        self._auth = LookerAuth(client_id=client_id, client_secret=client_secret, looker_base_url=looker_base_url)
        self._max_event_id = 0

    def observe(self):
        while True:
            time.sleep(self._interval)
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
            },
            "sorts": ["event.id asc 0"],
        })

        headers = {'Authorization': 'Bearer {}'.format(self._auth.get_token())}
        response = requests.post(self._query_url, headers=headers, data=data)

        for result in response.json():
            if int(result["event.id"]) > self._max_event_id:
                self._max_event_id = int(result["event.id"])
                self._summary.observe(result["dashboard_performance.seconds_until_last_tile_finished_rendering"])


if __name__ == '__main__':
    client_id = os.getenv("LOOKER_CLIENT_ID")
    client_secret = os.getenv("LOOKER_CLIENT_SECRET")
    fetch_interval = int(os.getenv("LOOKER_FETCH_INTERVAL"))
    dashboard_id = os.getenv("LOOKER_DASHBOARD_ID")
    looker_base_url = os.getenv("LOOKER_BASE_URL")

    lmf = LookerMetricFetcher(client_id=client_id, client_secret=client_secret,
                              fetch_interval=fetch_interval, looker_base_url=looker_base_url, dashboard_id=dashboard_id)

    logging.info("Starting Prometheus server on port 8000")
    start_http_server(8000)

    logging.info("Starting to fetch Looker performance data")
    lmf.observe()
