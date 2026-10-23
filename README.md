# checkout-service

A small Flask checkout service instrumented with the New Relic Python agent.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/checkout` | Place an order: checks stock, applies a coupon, validates the card. |
| `GET` | `/products` | List product IDs. |
| `GET` | `/health` | Liveness check. |

## Running

The agent reads its license key from the environment, so none is committed.

```bash
NEW_RELIC_LICENSE_KEY=<ingest-license-key> ./start.sh
```

The service listens on port 5001.
`newrelic.ini` points the agent at the EU collector.

To send continuous traffic, run in a second shell:

```bash
./run_traffic.sh
```
