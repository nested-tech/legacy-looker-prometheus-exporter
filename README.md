# Looker Prometheus Exporter 👀🏥✊🔥🚢

The _Looker Prometheus Exporter_ fetches metrics on dashboard performance from Looker and exports them to Prometheus.

It's highly WIP!

## Usage

Currently, everything is set in env vars (an example .env is provided). The following (hopefully self-explanatory) variables are what you need:

```bash
LOOKER_CLIENT_ID
LOOKER_CLIENT_SECRET
LOOKER_DASHBOARD_ID
LOOKER_BASE_URL
```

_N.B._ The Looker API runs by default on port 1999 (as mentioned [here](https://docs.looker.com/reference/api-and-integration/api-reference/v3.0)). If you're getting 403s all over, maybe you need to try this port.

With those variables set, the exporter is simply run with:

```python
python -m looker_prometheus_exporter
```

## TODO

- [ ] Switch to more common container registry (e.g. Docker Hub)
- [ ] Add more accessible deploy script (pushes to above container registry, builds from standard Python image and start versioning)
- [ ] Monitor multiple dashboards
- [ ] Add comprehensive unit tests (for a start...)
- [ ] Bagsy a [default port](https://github.com/prometheus/prometheus/wiki/Default-port-allocations)
