# Project Tasks

## Open

### Django scaffold and container startup

- **Status:** Complete; Docker image validation remains environment-blocked
- [x] Scaffold Django without authentication or database setup.
- [x] Add locked Gunicorn dependency and replace the production placeholder with the WSGI server on port 2158.
- [x] Require the secret key at runtime and restrict allowed hosts to local addresses.
- [x] Document local startup and loopback-only container publishing.
- [x] Verify system checks, all three route tests, and an HTTP request through the exact Docker Gunicorn command on port 2158.
- **Review:** Lockfile and whitespace checks passed. Missing runtime secret key produces an explicit configuration error. Gunicorn starts, serves HTTP 200, and shuts down cleanly; its unused control socket is disabled for compatibility with root-owned application files.
- **Limitation:** Docker is unavailable in the current environment; image build and container smoke tests must run where Docker is available.

### Gather and validate the Nobel-EU dataset source

- **Status:** In progress; provisional mirror selected, official-source confirmation pending
- **Goal:** Select a reliable source for the required `nobel-eu` backbone data and make its use reproducible.
- **Decision (2026-10-23):** Use a local `nobel-eu.txt` from the [sikorski-as/sndlib native-text mirror](https://raw.githubusercontent.com/sikorski-as/sndlib/master/native/nobel-eu/nobel-eu.txt) provisionally. The project owner will contact Quantum Sky about the original source failures. This does not resolve provenance or permitted-use checks.
- **Remaining work:**
  - [ ] Obtain clarification from Quantum Sky and locate or confirm the official dataset.
  - [ ] Preserve the provisional native file unchanged, recording its source revision, retrieval date, and checksum.
  - [ ] Confirm provenance, permitted use, and attribution; compare or replace the provisional copy when an official file becomes available.
- **Acceptance criteria:**
  - Confirm the selected source's provenance and permitted use.
  - Validate that the data represents 28 nodes, 41 links, and 378 demands, including node coordinates and demand values.
  - Record the source citation and preserve the dataset in a reproducible, appropriately attributed form.
  - Do not bypass TLS certificate validation to retrieve data.

#### Source findings (checked 2026-10-23)

The assignment's original download endpoints are currently unusable:

- [SNDlib XML download](https://sndlib.put.poznan.pl/download/sndlib-networks-xml/nobel-eu.xml) returned HTTP 404.
- [SNDlib native-text download](https://sndlib.put.poznan.pl/download/sndlib-networks-native/nobel-eu.txt) returned HTTP 404.
- The `sndlib.put.poznan.pl` TLS certificate names `ventus.put.poznan.pl` as its Common Name and only Subject Alternative Name. Normal hostname verification therefore fails. The 404 checks were diagnostic requests with certificate validation disabled; do not use that as a retrieval workaround.
- Requests to the corresponding paths on `ventus.put.poznan.pl` also returned HTTP 404.
- The `sndlib.zib.de` download URLs redirect to `sndlib.put.poznan.pl`, so they do not provide a working independent official source.

Potential alternatives found and checked:

1. **SNDlib native-text and XML mirrors in the same repository:**
   - [Native text](https://github.com/sikorski-as/sndlib/blob/master/native/nobel-eu/nobel-eu.txt) ([raw file](https://raw.githubusercontent.com/sikorski-as/sndlib/master/native/nobel-eu/nobel-eu.txt)) identifies itself as SNDlib native format, network `nobel-eu`, version 1.0.
   - [XML, identified by the project owner](https://github.com/sikorski-as/sndlib/blob/master/xml/nobel-eu/nobel-eu.xml) ([raw file](https://raw.githubusercontent.com/sikorski-as/sndlib/master/xml/nobel-eu/nobel-eu.xml)) is also available with normal TLS validation.
   - Both files were parsed and counted: each contains 28 nodes, 41 links, and 378 demands totaling 1,898 units. All 28 XML nodes have coordinates. Adding the assignment's sites and demands yields the expected 37 nodes, 55 links, and 391 demands totaling 2,068 units.
   - Counts and demand totals match, but a complete record-by-record comparison has not been performed. This is a third-party GitHub repository, not verified as an official SNDlib source; provenance and permitted use remain to be confirmed before adoption.
2. **TopoHub JSON conversion:** [TopoHub — `data/sndlib/nobel-eu.json`](https://github.com/piotrjurkiewicz/topohub/blob/master/data/sndlib/nobel-eu.json) ([raw file](https://raw.githubusercontent.com/piotrjurkiewicz/topohub/master/data/sndlib/nobel-eu.json)). The raw file returned HTTP 200. Inspection found 28 nodes, 41 edges, and 378 demand entries. This is a converted JSON representation, not an original SNDlib file; verify coordinates, link endpoints, demand values, and provenance against the expected network before use.
3. **XML copy in a project repository:** [Ruayakh8/ICA-JH-Simulation — `data/topologies/sndlib/nobel-eu.xml`](https://github.com/Ruayakh8/ICA-JH-Simulation/blob/main/data/topologies/sndlib/nobel-eu.xml) ([raw file](https://raw.githubusercontent.com/Ruayakh8/ICA-JH-Simulation/main/data/topologies/sndlib/nobel-eu.xml)). The raw file returned HTTP 200 and appears to be XML, but its provenance and contents have not been independently validated. Treat as a fallback candidate only.

These candidates are not equivalent in provenance or format. Verify a candidate against known network counts and content before relying on it, and cite both SNDlib and any mirror or conversion used.

### Implement local backbone and site loading with TopoHub

- **Status:** Pending
- **Design:** Follow the [local data loading design](../project-context.md#data-loading-design). Use TopoHub's native parser through `LocalSNDlibGenerator`, with local backbone input and CSV merging rather than bundled JSON or runtime downloads.
- **Implementation checklist:**
  - [ ] Verify the `SNDlibGenerator` subclass extension against the locked TopoHub version.
  - [ ] Add the assignment's site table as `sites.csv`.
  - [ ] Implement local backbone loading with file-and-row validation and preserved link identities.
  - [ ] Validate and merge sites, access links, capacities, coordinates, transit roles, and additional demands into one topology.
  - [ ] Test invalid input, including unknown attachments, duplicate IDs, bad capacities, and site references independent of CSV row order.
  - [ ] Verify the merged totals of 37 nodes, 55 links, and 391 demands totaling 2,068 units.
- **Prerequisite for baseline integration tests:** A recorded local backbone snapshot from the resource-gathering task above. Loader implementation and synthetic-fixture tests need not wait for official-source confirmation.
- **Review:** Dependencies are declared and locked; the loader and local input files have not yet been added.
