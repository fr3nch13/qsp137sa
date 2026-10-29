<!--
Release notes template for GitHub releases. Replace {{VERSION}} with the SemVer tag
(for example 1.2.3, without a "v" prefix), then create the release, e.g.:
  sed "s/{{VERSION}}/1.2.3/g" RELEASE.md > /tmp/notes.md
  gh release create 1.2.3 --title "LinkScope 1.2.3" --notes-file /tmp/notes.md
-->

## Overview

LinkScope is a network-resilience analysis tool for a European backbone and its connected operations sites and data centres.

This initial release answers three questions:
- Where does the network have single points of failure?
- Which links does the traffic depend on most?
- What happens when a link or site goes down?

## Features

- Interactive geographic map of 37 nodes and 55 links.
- Baseline traffic analysis covering 391 demands totalling 2,068 units, with the five most-utilized links ranked.
- Single-node and single-link failure simulation, with results updated without reloading the page.
- Separate reporting of failed-node endpoint traffic, other undeliverable traffic, network disconnection, and overloaded links.
- Baseline restoration without changing the source data.
- Input validation with detailed server-side diagnostics and user-friendly error messages.

## Run locally

Requires Docker. The container image is published by the release tag's CI workflow; wait for that workflow to complete successfully before starting it.

### Docker Compose

Download `compose.yaml` from this release's source, then run:

```sh
LINKSCOPE_IMAGE_TAG={{VERSION}} docker compose up -d
```

### Docker directly

Alternatively, run without a Compose file:

```sh
docker run -d \
  --name linkscope \
  --platform linux/amd64 \
  --pull always \
  -p 127.0.0.1:2158:2158 \
  -e DJANGO_SECRET_KEY=django-insecure-linkscope-local-development-only-not-for-production \
  ghcr.io/fr3nch13/qsp137sa:{{VERSION}}
```

Use either method, not both at once. Open http://localhost:2158.

The public secret key above is for this local-only demonstration, not production or shared access.

## Limitations

- Intended for local demonstration, not production or shared access. Authentication and authorization are not implemented.
- The supplied default secret key is public and suitable only for the local demonstration.
- The container image targets Linux AMD64. ARM hosts require compatible emulation.
- Analysis models one failure at a time and splits traffic equally across all permitted minimum-hop paths; it is not a full simulation of production routing protocols.
- OpenStreetMap background tiles require internet access; analysis and network overlays remain available without them.

## Data

Uses the SNDlib `nobel-eu` backbone and the assignment's additional site definitions. The backbone comes from an approved mirrored snapshot because the official download was unavailable. Source details, checksum and attribution are documented in the repository.
