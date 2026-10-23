// Pure layout helpers: filtering changes summaries, never the full-corpus grouping.
export function visibleConstellations(data, theses) {
  return (data?.groups || []).map((group, index) => {
    const ids = new Set(group.ids.map(Number));
    return { ...group, index, members: theses.filter((thesis) => ids.has(thesis.id)) };
  }).filter((group) => group.members.length);
}

export function medianMetric(theses, field) {
  // Missing/zero counts are excluded, not reported as zero-length documents.
  const values = theses.map((thesis) => thesis[field])
    .filter((value) => value !== null && value !== '' && Number.isFinite(Number(value)) && Number(value) > 0)
    .map(Number).sort((a, b) => a - b);
  if (!values.length) return null;
  const middle = Math.floor(values.length / 2);
  return values.length % 2 ? values[middle] : (values[middle - 1] + values[middle]) / 2;
}

export function constellationCenter(index, count) {
  const columns = Math.min(3, Math.max(1, count));
  const rows = Math.ceil(count / columns);
  return { x: (index % columns - (columns - 1) / 2) * 340,
    y: (Math.floor(index / columns) - (rows - 1) / 2) * 300, z: index % 2 ? 35 : -35 };
}
