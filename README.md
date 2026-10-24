# LinkScope

LinkScope is a network resilience analysis application for operations teams responsible for a European backbone network and its connected sites and data centers. It is an application within Project 137, a division of Quantum Sky.

The planned application will help teams explore network weak points, understand which links carry the most traffic, and assess the impact of a node or link outage. Its network view is intended to show critical infrastructure, link utilization, and outage impacts.

The project is based on the `nobel-eu` network from the [Survivable Network Design Library (SNDlib)](https://sndlib.put.poznan.pl/), with additional operations sites and data centers.

> **Availability:** The server currently displays a status page only. Network analysis and the interactive Web UI are not implemented yet. The demonstration is local-only and has no authentication.

## Run the current demonstration

Install Docker and ensure it is running. If the container package is private, first authenticate Docker to `ghcr.io` using a GitHub account with access to the package and a credential with package-read permission. Never put credentials in this repository.

Start the published stable image with one command:

```sh
docker run --rm --pull=always --name linkscope \
  -p 127.0.0.1:2158:2158 \
  -e DJANGO_SECRET_KEY=django-insecure-linkscope-local-development-only-not-for-production \
  ghcr.io/fr3nch13/qsp137sa:main
```

The key above is public and **only for this local demonstration**. A shared deployment must use a private, randomly generated key supplied at runtime.

Open **<http://localhost:2158/>**. The page should say:

> LinkScope is running. Network analysis and the Web UI are not implemented yet.

Leave the command running while using the app. Press **Ctrl+C** to stop it; Docker removes the container afterward. No database or dataset setup is needed for this status page. Logs appear in the terminal.

The port is bound to your computer's loopback interface, not exposed to other machines. Do not change this to a public binding for the current unauthenticated scaffold.

### Available images

Images are available in the [GitHub container package](https://github.com/fr3nch13/qsp137sa/pkgs/container/qsp137sa):

| Tag | Purpose |
|---|---|
| `main` | Stable channel; used above. |
| `dev` | Development preview channel. |
| A release version, such as `2.4.11` | A versioned release, once that Git tag has been published successfully. |

Replace `main` in the startup command with the desired available tag. All channels currently serve the same status-page scaffold; a versioned image does not imply production readiness.

## Data sources and attribution

- **Backbone:** The `nobel-eu` network from [SNDlib, the Survivable Network Design Library](https://sndlib.put.poznan.pl/), using the native-text copy from the [sikorski-as/sndlib mirror](https://github.com/sikorski-as/sndlib/blob/master/native/nobel-eu/nobel-eu.txt) as the provisionally selected source. It describes 28 cities, 41 links, and 378 traffic demands.
- **Sites:** The `sites.csv` table supplied in the [Quantum Sky assignment instructions](docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md), defining nine additional sites, their types, attachment points, and access-link capacities. Additional traffic demands follow the assignment's rules.

These are the selected inputs for the network analysis; the current status-page scaffold does not load them yet.
