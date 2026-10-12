import type { FarmResponse } from '../types';

/**
 * Generate a friendly farm label "Farm #N — [name]" for display.
 * The number is based on the farm's position in the sorted array (by creation date).
 *
 * @param farm - The farm object
 * @param allFarms - Array of all farms for the current user (sorted by created_at)
 * @param farm - The farm object to generate a label for
 * @returns A friendly label like "Farm #1 — Green Valley Farm"
 */
export function getFarmLabel(farm: FarmResponse, allFarms: FarmResponse[]): string {
  // Sort farms by created_at to determine the ordering
  const sortedFarms = [...allFarms].sort((a, b) => {
    const dateA = new Date(a.created_at || 0).getTime();
    const dateB = new Date(b.created_at || 0).getTime();
    return dateA - dateB;
  });

  // Find the index of this farm in the sorted array
  const farmIndex = sortedFarms.findIndex(f => f.id === farm.id);
  const farmNumber = farmIndex >= 0 ? farmIndex + 1 : '?';

  return `Farm #${farmNumber} — ${farm.name}`;
}
