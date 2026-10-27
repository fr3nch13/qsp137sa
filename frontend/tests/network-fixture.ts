// Small typed API fixture shared by frontend contract and presentation tests.
import type { Network } from "../src/api";

export const networkFixture: Network = {
  nodes: [
    { id: "A", kind: "backbone", latitude: 50, longitude: 5, transit: true },
    {
      id: "DC",
      kind: "data-center",
      latitude: 51,
      longitude: 6,
      transit: false,
    },
  ],
  links: [{ id: "L1", source: "A", target: "DC", capacity: 100 }],
  demands: [{ id: "D1", source: "A", target: "DC", units: 25 }],
  baseline: {
    failure: null,
    links: [
      {
        id: "L1",
        source: "A",
        target: "DC",
        capacity: 100,
        load: 25,
        utilization_percent: 25,
      },
    ],
    top_five: [
      {
        id: "L1",
        source: "A",
        target: "DC",
        capacity: 100,
        load: 25,
        utilization_percent: 25,
      },
    ],
    undeliverable: [],
    failed_endpoint_demands: [],
    overloaded: [],
    disconnected: false,
  },
  criticality: [
    { kind: "node", id: "A", critical: true, reasons: ["undeliverable"] },
    { kind: "node", id: "DC", critical: true, reasons: ["undeliverable"] },
    {
      kind: "link",
      id: "L1",
      critical: true,
      reasons: ["disconnected", "undeliverable"],
    },
  ],
};
