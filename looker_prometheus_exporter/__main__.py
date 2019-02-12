import os
import logging

from prometheus_client import start_http_server

from .looker_metric_fetcher import LookerMetricFetcher

if __name__ == '__main__':
    client_id = os.getenv("LOOKER_CLIENT_ID")
    client_secret = os.getenv("LOOKER_CLIENT_SECRET")
    fetch_interval = int(os.getenv("LOOKER_FETCH_INTERVAL"))
    dashboard_id = os.getenv("LOOKER_DASHBOARD_ID")
    looker_base_url = os.getenv("LOOKER_BASE_URL")

    lmf = LookerMetricFetcher(
        client_id=client_id,
        client_secret=client_secret,
        fetch_interval=fetch_interval,
        looker_base_url=looker_base_url,
        dashboard_id=dashboard_id
    )

    logging.info("Starting Prometheus server on port 8000")
    start_http_server(8000)

    logging.info("Starting to fetch Looker performance data")
    lmf.observe()
