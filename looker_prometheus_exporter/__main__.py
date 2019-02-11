from prometheus_client import start_http_server, Summary
import json
import requests
import time


class LookerMetricFetcher(object):
    def __init__(self):
        self.summary = Summary('looker_dashboard_performance', 'Performance of Looker dashboard')

    def observe(self):
        while True:
            time.sleep(5)
            self._fetch_metrics()

    def _fetch_metrics(self):
        # Actually get the shizz from Looker

        # Add the shizz to the summary
        self.summary.observe(3)


if __name__ == '__main__':
    lmf = LookerMetricFetcher()
    start_http_server(8000)

    lmf.observe()
