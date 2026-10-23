// Null keeps the original per-category/per-year palette until the user picks a color.
export function defaultLineColors() {
  return { semantic: null, advisor: null, category: null, year: null, keywords: null };
}

export function connectionColor(lane, overrides) {
  return overrides[lane.type] || lane.color;
}
