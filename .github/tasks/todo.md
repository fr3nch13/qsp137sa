# Project Tasks

## Open

### Gather and validate the Nobel-EU dataset source

- **Status:** Pending
- **Goal:** Select a reliable source for the required `nobel-eu` backbone data and make its use reproducible.
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
