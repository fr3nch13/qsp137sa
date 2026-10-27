// Render the backend coordinates and findings over an optional online basemap.
import { useEffect, useRef, useState } from "react";
import type { Network, NodeKind } from "./api";

export const nodeSymbols: Record<NodeKind, string> = {
  backbone: "●",
  "operations-site": "■",
  "data-center": "◆",
  "aggregation-hub": "▲",
};

export function NetworkMap({ network }: { network: Network }) {
  const container = useRef<HTMLElement>(null);
  const [tileError, setTileError] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    let map: import("leaflet").Map | undefined;
    let resize: ResizeObserver | undefined;
    setTileError(false);
    setMapError(null);
    // Leaflet requires a browser; load inside the effect, not during SSR/tests.
    import("leaflet")
      .then((L) => {
        if (!active || !container.current) return;
        map = L.map(container.current, {
          scrollWheelZoom: false,
          zoomSnap: 0.25,
          zoomDelta: 0.25,
        });
        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          referrerPolicy: "strict-origin-when-cross-origin",
        })
          .on("tileerror", () => {
            if (active) setTileError(true);
          })
          .addTo(map);
        const positions = new Map(
          network.nodes.map((node) => [
            node.id,
            L.latLng(node.latitude, node.longitude),
          ]),
        );
        const ranks = new Map(
          network.baseline.top_five.map((item, index) => [item.id, index + 1]),
        );
        const criticalLinks = new Set(
          network.criticality
            .filter((item) => item.kind === "link" && item.critical)
            .map((item) => item.id),
        );
        const criticalNodes = new Set(
          network.criticality
            .filter((item) => item.kind === "node" && item.critical)
            .map((item) => item.id),
        );
        for (const link of network.links) {
          const source = positions.get(link.source);
          const target = positions.get(link.target);
          if (!source || !target)
            throw new Error(`Missing coordinates for link ${link.id}.`);
          const rank = ranks.get(link.id);
          const critical = criticalLinks.has(link.id);
          const line = L.polyline([source, target], {
            color: rank ? "#075985" : "#17212b",
            weight: rank ? 5 : 2,
            dashArray: critical ? "8 5" : undefined,
            opacity: 0.85,
          }).addTo(map);
          const label = document.createElement("span");
          label.textContent = `${link.id}: ${link.source} – ${link.target}${critical ? " · Critical" : ""}${rank ? ` · Top ${rank}` : ""}`;
          if (rank) {
            const badge = document.createElement("span");
            badge.textContent = `#${rank}`;
            line.bindTooltip(badge, {
              permanent: true,
              direction: "center",
              className: "rank-label",
            });
          } else {
            line.bindTooltip(label);
          }
        }
        for (const node of network.nodes) {
          const content = document.createElement("span");
          content.className = "node-label";
          const symbol = document.createElement("span");
          symbol.className = `node-symbol ${node.kind}`;
          symbol.textContent = nodeSymbols[node.kind];
          content.append(
            symbol,
            document.createTextNode(
              ` ${node.id}${criticalNodes.has(node.id) ? " *" : ""}`,
            ),
          );
          L.marker([node.latitude, node.longitude], {
            icon: L.divIcon({
              html: content,
              className: "network-node",
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            }),
            title: `${node.id} (${node.kind})${criticalNodes.has(node.id) ? " · Critical" : ""}`,
            keyboard: false,
          }).addTo(map);
        }
        const bounds = L.latLngBounds([...positions.values()]);
        const fit = () => {
          map?.invalidateSize({ pan: false });
          map?.fitBounds(bounds, {
            padding: [24, 24],
            maxZoom: 6,
            animate: false,
          });
        };
        fit();
        resize = new ResizeObserver(fit);
        resize.observe(container.current);
      })
      .catch((error: unknown) => {
        map?.remove();
        map = undefined;
        resize?.disconnect();
        if (active)
          setMapError(
            error instanceof Error
              ? error.message
              : "Map failed to initialize.",
          );
      });
    return () => {
      active = false;
      resize?.disconnect();
      map?.remove();
    };
  }, [network]);
  return (
    <>
      {mapError && (
        <p role="alert">
          Could not display the map: {mapError} Findings remain available below.
        </p>
      )}
      {tileError && (
        <p role="alert">
          Some map background tiles could not load. Network overlays and
          findings are still available; internet access is required for
          OpenStreetMap tiles.
        </p>
      )}
      <section
        ref={container}
        className="network-map"
        aria-label="European network map"
      />
    </>
  );
}
