import json
import requests
import logging
import time

from prometheus_client import Summary
from datetime import datetime, timedelta

from looker_prometheus_exporter.looker_auth import LookerAuth


class LookerMetricFetcher(object):
    def __init__(self, *, client_id, client_secret, fetch_interval, looker_base_url, dashboard_id):
        self._interval = fetch_interval
        self._query_url = "{}/api/3.0/queries/run/json".format(looker_base_url)
        self._dashboard_id = dashboard_id
        self._summary = Summary(
            "looker_dashboard_{}_render_time".format(dashboard_id),
            "Time until last tile of dashboard {} finished rendering".format(dashboard_id)
        )

        self._auth = LookerAuth(client_id=client_id, client_secret=client_secret, looker_base_url=looker_base_url)
        self._max_event_id = 0

    def observe(self):
        while True:
            self._fetch_metrics()
            time.sleep(self._interval * 60)

    def _fetch_metrics(self):
        data = json.dumps(
            {
                "model": "i__looker",
                "view": "dashboard_performance",
                "fields": ["dashboard_performance.seconds_until_last_tile_finished_rendering", "event.id"],
                "filters": {
                    "history.real_dash_id": self._dashboard_id,
                    "dashboard_performance.seconds_until_last_tile_finished_rendering": "NOT NULL",
                    "dashboard_performance.last_event_at_date": "{} minutes".format(self._interval),
                    "event.id": ">{}".format(self._max_event_id)
                },
            }
        )

        headers = {"Authorization": "Bearer {}".format(self._auth.get_token())}
        response = requests.post(self._query_url, headers=headers, data=data)

        for result in response.json():
            event_id = int(result["event.id"])
            if event_id > self._max_event_id:
                self._max_event_id = event_id

            self._summary.observe(result["dashboard_performance.seconds_until_last_tile_finished_rendering"])
