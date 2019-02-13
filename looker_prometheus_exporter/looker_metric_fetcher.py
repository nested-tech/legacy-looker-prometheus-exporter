import json
import requests
import logging
import time

from prometheus_client import Summary, Counter
from datetime import datetime, timedelta

from looker_prometheus_exporter.looker_auth import LookerAuth, LookerAuthenticationError


class LookerQueryError(Exception):
    # Represents a 500 from Looker
    pass


class LookerMetricFetcher(object):
    def __init__(self, *, client_id, client_secret, fetch_interval, looker_base_url, dashboard_id):
        self._interval = fetch_interval
        self._query_url = "{}/api/3.0/queries/run/json".format(looker_base_url)
        self._dashboard_id = dashboard_id

        self._dashboard_render_time_summary = Summary(
            "looker_dashboard_{}_render_time_seconds".format(dashboard_id),
            "Time in seconds until last tile of dashboard {} finished rendering".format(dashboard_id)
        )
        self._successful_queries_counter = Counter(
            "looker_number_of_successful_queries_counter", "Number of successful queries to Looker's API"
        )
        self._query_response_time_summary = Summary(
            "looker_query_response_time_seconds", "Length of time Looker took to respond to the performance query"
        )

        self._auth = LookerAuth(client_id=client_id, client_secret=client_secret, looker_base_url=looker_base_url)
        self._max_event_id = None

    def observe(self):
        while True:
            self._fetch_metrics()
            time.sleep(60)

    def _fetch_metrics(self):
        data = json.dumps(
            {
                "model": "i__looker",
                "view": "dashboard_performance",
                "fields": ["dashboard_performance.seconds_until_last_tile_finished_rendering", "event.id"],
                "filters": self._filters(),
            }
        )

        headers = {"Authorization": "Bearer {}".format(self._auth.get_token())}
        response = requests.post(self._query_url, headers=headers, data=data)

        if response.status_code >= 500:
            raise LookerQueryError
        if response.status_code >= 400:
            if "authentication" in response.json()["message"]:
                raise LookerAuthenticationError
            else:
                # TODO: Add actual useful exception
                raise Exception

        response_time = response.elapsed.seconds + response.elapsed.microseconds / 1000000
        self._query_response_time_summary.observe(response_time)
        self._successful_queries_counter.inc()

        for result in response.json():
            event_id = int(result["event.id"])
            if self._max_event_id is None or event_id > self._max_event_id:
                self._max_event_id = event_id

            self._dashboard_render_time_summary.observe(
                result["dashboard_performance.seconds_until_last_tile_finished_rendering"]
            )

    def _filters(self):
        if self._max_event_id is None:
            return {
                "history.real_dash_id": self._dashboard_id,
                "dashboard_performance.seconds_until_last_tile_finished_rendering": "NOT NULL",
                "dashboard_performance.last_event_at_date": "10 minutes".format(self._interval),
            }

        return {
            "history.real_dash_id": self._dashboard_id,
            "dashboard_performance.seconds_until_last_tile_finished_rendering": "NOT NULL",
            "event.id": ">{}".format(self._max_event_id)
        }
