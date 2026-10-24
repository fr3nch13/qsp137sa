# LinkScope

LinkScope is a network resilience analysis application for operations teams responsible for a European backbone network and its connected sites and data centers. It is an application within Project 137, a division of Quantum Sky.

The planned application will help teams explore network weak points, understand which links carry the most traffic, and assess the impact of a node or link outage. Its network view is intended to show critical infrastructure, link utilization, and outage impacts.

The project is based on the `nobel-eu` network from the [Survivable Network Design Library (SNDlib)](https://sndlib.put.poznan.pl/), with additional operations sites and data centers.

> **Availability:** The server currently displays a status page only. Network analysis and the interactive Web UI are not implemented yet. The demonstration is local-only and has no authentication.

## Run the current demonstration

Install Docker with the Docker Compose plugin and ensure Docker is running. Download or clone this repository and open a terminal in its root directory.

If the container package is private, sign Docker in to `ghcr.io` first. Your GitHub account must have access to the package. Use one of these options:

- **GitHub CLI:** add the package-read scope to your login, then pass its token to Docker:

  ```sh
  gh auth refresh -h github.com -s read:packages
  gh auth token | docker login ghcr.io -u "$(gh api user --jq .login)" --password-stdin
  ```

- **Personal access token:** create a [classic token](https://github.com/settings/tokens/new?scopes=read:packages) with the `read:packages` scope. Then run the following, replacing `YOUR_GITHUB_USERNAME`. The token is read without being shown on screen or saved in your shell history:

  ```sh
  read -rs GHCR_TOKEN && printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin; unset GHCR_TOKEN
  ```

Docker should print `Login Succeeded`. Run `docker logout ghcr.io` to remove the saved credential later. Never put credentials in this repository.

Start the published stable image in the background:

```sh
docker compose up -d
```

Compose downloads the image; it does not build the application locally. By default, it uses a public development-only secret key, **only for this local demonstration**. A shared deployment must use a private, randomly generated key supplied at runtime.

The image targets Linux AMD64. It runs natively on AMD64 hosts; ARM64 hosts, including Apple Silicon Macs, need AMD64 emulation enabled (provided by Docker Desktop). Emulation can be slower than native execution.

Open **<http://localhost:2158/>**. The page should say:

> LinkScope is running. Network analysis and the Web UI are not implemented yet.

View logs:

```sh
docker compose logs -f
```

Press **Ctrl+C** to stop following logs; the app keeps running. Stop and remove the container with:

```sh
docker compose down
```

No database or dataset setup is needed for this status page. The port is bound to your computer's loopback interface, not exposed to other machines. Do not change this to a public binding for the current unauthenticated scaffold.

### Configuration

Compose reads these optional variables from your shell or a private `.env` file in the repository root:

| Variable | Default | Purpose |
|---|---|---|
| `LINKSCOPE_IMAGE_TAG` | `main` | Select an available image tag. |
| `DJANGO_SECRET_KEY` | Public local-demo key | Override the demonstration key; never commit private keys. |

For example, run the development preview with:

```sh
LINKSCOPE_IMAGE_TAG=dev docker compose up -d
```

Run `docker compose up -d` again to pull the selected image and apply configuration changes.

### Docker run alternative

To run without Compose or a local copy of the repository:

```sh
docker run --rm --pull=always --platform linux/amd64 --name linkscope \
  -p 127.0.0.1:2158:2158 \
  -e DJANGO_SECRET_KEY=django-insecure-linkscope-local-development-only-not-for-production \
  ghcr.io/fr3nch13/qsp137sa:main
```

The same local-only key and port restrictions apply. Logs appear in the terminal. Press **Ctrl+C** to stop the app; Docker removes the container afterward. Do not run this alongside Compose on the same port.

### Available images

Images are available in the [GitHub container package](https://github.com/fr3nch13/qsp137sa/pkgs/container/qsp137sa):

| Tag | Purpose |
|---|---|
| `main` | Stable channel; used above. |
| `dev` | Development preview channel. |
| A release version, such as `2.4.11` | A versioned release, once that Git tag has been published successfully. |

Set `LINKSCOPE_IMAGE_TAG` for Compose, or replace `main` in the Docker run command, with the desired available tag. All channels currently serve the same status-page scaffold; a versioned image does not imply production readiness.

## Data sources and attribution

- **Backbone:** The `nobel-eu` network from [SNDlib, the Survivable Network Design Library](https://sndlib.put.poznan.pl/), using the native-text copy from the [sikorski-as/sndlib mirror](https://github.com/sikorski-as/sndlib/blob/master/native/nobel-eu/nobel-eu.txt) as the provisionally selected source. It describes 28 cities, 41 links, and 378 traffic demands.
- **Sites:** The `sites.csv` table supplied in the [Quantum Sky assignment instructions](docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md), defining nine additional sites, their types, attachment points, and access-link capacities. Additional traffic demands follow the assignment's rules.

These are the selected inputs for the network analysis; the current status-page scaffold does not load them yet.
