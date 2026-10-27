// Render the backend coordinates and findings over an optional online basemap.
import { useEffect, useRef, useState } from "react";
import type { Analysis, Network, NodeKind } from "./api";

export const nodeSymbols: Record<NodeKind, string> = {
  backbone: "●",
  "operations-site": "■",
  "data-center": "◆",
  "aggregation-hub": "▲",
};

export function NetworkMap({
  network,
  analysis,
}: {
  network: Network;
  analysis: Analysis;
}) {
  const container = useRef<HTMLElement>(null);
  const [instance, setInstance] = useState<import("leaflet").Map | null>(null);
  const [tileError, setTileError] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [overlayError, setOverlayError] = useState<string | null>(null);
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
        const bounds = L.latLngBounds(
          network.nodes.map(
            (node) => [node.latitude, node.longitude] as [number, number],
          ),
        );
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
        setInstance(map);
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
  useEffect(() => {
    if (!instance) return;
    setOverlayError(null);
    let active = true;
    let overlays: import("leaflet").LayerGroup | undefined;
    import("leaflet")
      .then((L) => {
        if (!active) return;
        overlays = L.layerGroup().addTo(instance);
        const layer = overlays;
        const failed = analysis.failure;
        const overloaded = new Set(analysis.overloaded.map((item) => item.id));
        const positions = new Map(
          network.nodes.map((node) => [
            node.id,
            L.latLng(node.latitude, node.longitude),
          ]),
        );
        const ranks = new Map(
          analysis.top_five.map((item, index) => [item.id, index + 1]),
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
          const removed = failed?.kind === "link" && failed.id === link.id;
          const incident =
            failed?.kind === "node" &&
            (failed.id === link.source || failed.id === link.target);
          const overload = overloaded.has(link.id);
          const line = L.polyline([source, target], {
            color:
              removed || overload ? "#b91c1c" : rank ? "#075985" : "#17212b",
            weight: rank || overload ? 5 : 2,
            dashArray: removed ? "2 6" : critical ? "8 5" : undefined,
            opacity: incident ? 0.2 : 0.85,
            className: removed
              ? "failed-link"
              : overload
                ? "overloaded-link"
                : undefined,
          }).addTo(layer);
          const label = document.createElement("span");
          label.textContent = `${link.id}: ${link.source} – ${link.target}${critical ? " · Critical" : ""}${rank ? ` · Top ${rank}` : ""}`;
          if (rank || removed || overload) {
            const badge = document.createElement("span");
            badge.textContent = [
              rank ? `#${rank}` : "",
              removed ? "× FAILED" : overload ? "! OVERLOAD" : "",
            ]
              .filter(Boolean)
              .join(" ");
            line.bindTooltip(badge, {
              permanent: true,
              direction: "center",
              className: removed || overload ? "failure-label" : "rank-label",
            });
          } else {
            line.bindTooltip(label);
          }
        }
        for (const node of network.nodes) {
          const content = document.createElement("span");
          content.className = "node-label";
          const removed = failed?.kind === "node" && failed.id === node.id;
          const symbol = document.createElement("span");
          symbol.className = `node-symbol ${node.kind}`;
          symbol.textContent = nodeSymbols[node.kind];
          content.append(
            symbol,
            document.createTextNode(
              ` ${node.id}${removed ? " × FAILED" : criticalNodes.has(node.id) ? " *" : ""}`,
            ),
          );
          L.marker([node.latitude, node.longitude], {
            icon: L.divIcon({
              html: content,
              className: removed ? "network-node failed-node" : "network-node",
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            }),
            title: `${node.id} (${node.kind})${removed ? " · FAILED" : criticalNodes.has(node.id) ? " · Critical" : ""}`,
            keyboard: false,
          }).addTo(layer);
        }
      })
      .catch((error: unknown) => {
        overlays?.remove();
        if (active)
          setOverlayError(
            error instanceof Error ? error.message : "Map overlays failed.",
          );
      });
    return () => {
      active = false;
      overlays?.remove();
    };
  }, [network, analysis, instance]);
  return (
    <>
      {(mapError || overlayError) && (
        <p role="alert">
          Could not display the map: {mapError || overlayError} Findings remain
          available below.
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
