// Normalize mouse/trackpad wheel units and keep proportional zoom at every scale.
export function wheelZoom(current, deltaY, deltaMode = 0, pageHeight = 800) {
  const pixels = deltaY * (deltaMode === 1 ? 16 : deltaMode === 2 ? pageHeight : 1);
  const step = Math.max(-240, Math.min(240, pixels));
  return Math.max(0.25, Math.min(8, current * Math.exp(-step * 0.0015)));
}
