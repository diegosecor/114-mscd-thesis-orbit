// Presentation-only multipliers never alter relationship types or similarity scores.
export function defaultLineScales() {
  return { semantic: 1, advisor: 1, category: 1, year: 1, keywords: 1 };
}

// Dash–dot years remain distinguishable from category/advisor dots without color.
export function connectionPattern(lane, active) {
  if (lane.solid) return [];
  return lane.type === 'year' ? [8, 3, 2, 3] : [2, active ? 3 : 4.5];
}

export function connectionWidth(lane, active, semanticEnabled, scale = 1) {
  let width = active ? (lane.solid ? 4.2 : 1.9) : lane.solid ? 2.35 : 1.4;
  if (lane.type === 'semantic') {
    const strength = Math.max(0, Math.min(1, (lane.similarity - 0.2) / 0.65));
    width = 1.4 + strength * 4.65;
  } else if (active && semanticEnabled) width = lane.solid ? 1.8 : 1.3;
  // Keep the user's previous 20% dotted-line reduction as the default baseline.
  if (!lane.solid) width *= 0.8;
  return width * scale;
}
