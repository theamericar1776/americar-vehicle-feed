# Americar LLC vehicle ads feed

Public Google Merchant Center vehicle-ads feed for [Americar LLC](https://www.americar-llc.com) (7216 Main St, Ralston, NE).

This repo hosts the feed that replaces Dealer Merchant Center (DMC). Customers do not use these links; only Google fetches them.

## Public feed URLs

- XML: https://theamericar1776.github.io/americar-vehicle-feed/vehicle_feed.xml
- TSV: https://theamericar1776.github.io/americar-vehicle-feed/vehicle_feed.tsv

The builder scrapes live inventory from americar-llc.com and writes Google RSS 2.0 (`g:` namespace) XML plus a matching TSV.

## Refresh schedule

A GitHub Actions workflow rebuilds the feed every day at 11:00 UTC (5:00 AM CST / 6:00 AM CDT) and on manual `workflow_dispatch`. The updated files are committed to `docs/` only if the build succeeds and the feed contains at least 5 vehicles, so a website outage cannot publish an empty feed.

To run it by hand from this repo:

```bash
gh workflow run refresh-feed.yml
```

To rebuild on the box and push as a fallback:

```bash
/workspace/americar/merchant-feed/publish.sh
```

(or `./publish.sh` in this repo, with `REPO_DIR` pointing at a local clone if needed)

## Source

Python 3.10+ standard library only — no pip packages. Entry point is `./run.sh`.
