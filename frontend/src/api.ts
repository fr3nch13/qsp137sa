// Fetch and validate the greeting contract rather than supplying fallback content.
export async function fetchGreeting(signal: AbortSignal): Promise<string> {
  const response = await fetch("/api", { signal });
  if (!response.ok) {
    throw new Error(`API request failed (HTTP ${response.status}).`);
  }
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error("API returned a non-JSON response.");
  }
  const data: unknown = await response.json();
  if (
    typeof data !== "object" ||
    data === null ||
    !("message" in data) ||
    typeof data.message !== "string" ||
    !data.message.trim()
  ) {
    throw new Error("API returned an invalid greeting.");
  }
  return data.message;
}
