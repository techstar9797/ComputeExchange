/**
 * Canonical display names for cloud providers.
 * Maps backend provider IDs (including legacy) to user-facing names.
 */
export const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  nebius: "Nebius",
  aws: "AWS",
  "lambda-labs": "Lambda Labs",
  coreweave: "CoreWeave",
  "google-cloud": "Google Cloud",
  azure: "Azure",
  "neocloud-alpha": "Nebius",
  "datacenter-prime": "AWS",
  "hyperscale-cloud": "Google Cloud",
  "edge-neural": "Lambda Labs",
  "green-compute": "CoreWeave",
};

export function getProviderDisplayName(item: {
  provider_id?: string;
  provider_name?: string;
}): string {
  const id = item.provider_id ?? "";
  const parts = id.split("-");
  const lastPart = parts[parts.length - 1] ?? "";
  const hasNumericSuffix = /^\d+$/.test(lastPart);
  const baseId = hasNumericSuffix ? parts.slice(0, -1).join("-") : id;
  if (hasNumericSuffix) {
    return PROVIDER_DISPLAY_NAMES[baseId] ?? item.provider_name ?? id;
  }
  return PROVIDER_DISPLAY_NAMES[id] ?? PROVIDER_DISPLAY_NAMES[baseId] ?? item.provider_name ?? id;
}
