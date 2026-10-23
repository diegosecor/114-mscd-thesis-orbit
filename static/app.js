import { buildRelations, categoryColor, hash } from './relations.mjs?v=20261021-semantic-1';
import { visibleConstellations, medianMetric, constellationCenter } from './constellations.mjs?v=20261022-1';
import { defaultLineScales, connectionWidth, connectionPattern } from './line-widths.mjs?v=20261022-2';
import { wheelZoom } from './zoom.mjs?v=20261022-1';
import { defaultLineColors, connectionColor } from './line-colors.mjs?v=20261022-1';

const canvas = document.querySelector('#orbitCanvas');
const ctx = canvas.getContext('2d');
const tooltip = document.querySelector('#tooltip');
const detailPanel = document.querySelector('#detailPanel');
const dialog = document.querySelector('#thesisDialog');
const form = document.querySelector('#thesisForm');

const controls = {
  search: document.querySelector('#searchInput'),
  layout: document.querySelector('#layoutSelect'),
  size: document.querySelector('#sizeSelect'),
  category: document.querySelector('#categoryFilter'),
  advisor: document.querySelector('#advisorFilter'),
  searchMode: document.querySelector('#searchMode'),
  neighborCount: document.querySelector('#neighborCount'),
  similarityMin: document.querySelector('#similarityMin'),
  yearMin: document.querySelector('#yearMin'),
  yearMax: document.querySelector('#yearMax'),
  pageMin: document.querySelector('#pageMin'),
  pageMax: document.querySelector('#pageMax'),
  wordMin: document.querySelector('#wordMin'),
  wordMax: document.querySelector('#wordMax'),
};

const connectionControls = {
  semantic: document.querySelector('#showSemantic'),
  advisor: document.querySelector('#showAdvisor'),
  category: document.querySelector('#showCategory'),
  year: document.querySelector('#showYear'),
  keywords: document.querySelector('#showKeywords'),
};
const state = {
  lineScales: defaultLineScales(),
  lineColors: defaultLineColors(),
  editedLineType: null,
  theses: [],
  categories: [],
  advisors: [],
  semanticMap: null,
  semanticNeighbors: [],
  total: 0,
  minYear: null,
  maxYear: null,
  ranges: {
    pages: { min: null, max: null },
    words: { min: null, max: null },
  },
  relations: [],
  positions: new Map(),
  selected: null,
  hovered: null,
  images: new Map(),
  projection: [],
  yaw: -0.46,
  pitch: 0.22,
  zoom: 1,
  dragging: false,
  dragDistance: 0,
  pointer: { x: 0, y: 0, lastX: 0, lastY: 0 },
  editId: null,
};

const rangeSliders = {
  year: {
    min: controls.yearMin, max: controls.yearMax,
    minLabel: document.querySelector('#yearMinLabel'),
    maxLabel: document.querySelector('#yearMaxLabel'),
    fill: document.querySelector('#yearRangeFill'),
  },
  pages: {
    min: controls.pageMin, max: controls.pageMax,
    minLabel: document.querySelector('#pageMinLabel'),
    maxLabel: document.querySelector('#pageMaxLabel'),
    fill: document.querySelector('#pageRangeFill'),
  },
  words: {
    min: controls.wordMin, max: controls.wordMax,
    minLabel: document.querySelector('#wordMinLabel'),
    maxLabel: document.querySelector('#wordMaxLabel'),
    fill: document.querySelector('#wordRangeFill'),
  },
};

/** Parse optional numeric metadata without converting missing values into zero. */
function number(value) {
  if (value === null || value === undefined || value === '') return null;
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

/** Format counts for display and use a dash when a source value is missing. */
const countFormatter = new Intl.NumberFormat();
function displayNumber(value) {
  const parsed = number(value);
  return parsed === null ? '—' : countFormatter.format(parsed);
}

/** Find the positive metric bounds of the currently visible theses. */
let metricSource;
let metricBounds = {};
function metricRange(field) {
  // A filtered result is immutable until the next fetch: scan it only once per metric.
  if (metricSource !== state.theses) { metricSource = state.theses; metricBounds = {}; }
  if (metricBounds[field]) return metricBounds[field];
  const values = state.theses.map((thesis) => number(thesis[field])).filter((value) => value !== null && value > 0);
  return (metricBounds[field] = { min: values.length ? Math.min(...values) : 0, max: values.length ? Math.max(...values) : 1 });
}

/** Map document length to a comparable 0–1 range within the current view. */
function normalizedMetric(thesis, field) {
  const value = number(thesis[field]);
  if (value === null || value <= 0) return 0.4;
  const { min, max } = metricRange(field);
  return max === min ? 0.65 : (value - min) / (max - min);
}

/** Encode the selected document metric in the point radius, not thumbnail size. */
function nodeRadius(thesis) {
  if (controls.size.value === 'equal') return 5.5;
  const field = controls.size.value === 'pages' ? 'page_count' : 'word_count';
  return 4.2 + normalizedMetric(thesis, field) * 8;
}

/** Distribute points evenly over a sphere using the golden angle. */
function sphericalPoint(index, count, radius) {
  const safeCount = Math.max(1, count);
  const vertical = 1 - (2 * (index + 0.5)) / safeCount;
  const radial = Math.sqrt(Math.max(0, 1 - vertical * vertical));
  const angle = index * Math.PI * (3 - Math.sqrt(5));
  return {
    x: Math.cos(angle) * radial * radius,
    y: vertical * radius,
    z: Math.sin(angle) * radial * radius,
  };
}

/** Choose a world-space layout; semantic groups and metadata groups remain distinct. */
function targetPosition(thesis, index, count) {
  const layout = controls.layout.value;
  const seed = hash(`${thesis.id}-${thesis.title}`);
  const wobble = ((seed % 100) / 100 - 0.5);

  if (layout === 'constellations' || layout === 'topicLength') {
    const data = state.semanticMap?.constellations;
    const group = visibleConstellations(data, state.theses)
      .find((item) => item.id === data.membership[thesis.id]);
    if (!group) return state.semanticMap?.points[thesis.id] || sphericalPoint(index, count, 300);
    const localIndex = group.members.findIndex((item) => item.id === thesis.id);
    const local = sphericalPoint(localIndex, group.members.length, 65 + 7 * Math.sqrt(group.members.length));
    const center = constellationCenter(group.index, data.groups.length);
    // In length mode, height and point size encode length; topic groups stay fixed.
    if (layout === 'topicLength') {
      const field = controls.size.value === 'words' ? 'word_count' : 'page_count';
      const value = number(thesis[field]);
      local.y = value !== null && value > 0 ? (0.5 - normalizedMetric(thesis, field)) * 170 : 110;
    }
    return { x: center.x + local.x, y: center.y + local.y, z: center.z + local.z };
  }

  if (layout === 'semantic') {
    return state.semanticMap?.points[thesis.id] || sphericalPoint(index, count, 300);
  }
  if (layout === 'neighborhood') {
    if (!state.selected) return state.semanticMap?.points[thesis.id] || sphericalPoint(index, count, 300);
    if (thesis.id === state.selected.id) return { x: 0, y: 0, z: 0 };
    const matchIndex = state.semanticNeighbors.findIndex((item) => item.id === thesis.id);
    if (matchIndex >= 0) {
      const score = state.semanticNeighbors[matchIndex].similarity;
      return sphericalPoint(matchIndex, state.semanticNeighbors.length, 80 + (1 - score) * 270);
    }
    return sphericalPoint(index, count, 410 + (seed % 30));
  }
  if (layout === 'advisor') {
    const keys = [...new Set(state.theses.map(advisorGroup))].sort();
    const group = advisorGroup(thesis);
    const members = state.theses.filter((item) => advisorGroup(item) === group);
    const center = advisorCenter(keys.indexOf(group), keys.length);
    const local = sphericalPoint(members.findIndex((item) => item.id === thesis.id), members.length, 48 + 15 * Math.sqrt(members.length));
    return { x: center.x + local.x, y: center.y + local.y, z: center.z + local.z };
  }

  if (layout === 'cloud') {
    const radius = 335 * Math.cbrt(((seed % 1000) + 1) / 1000);
    const point = sphericalPoint(index, count, radius);
    return point;
  }

  if (layout === 'category') {
    const categories = [...new Set(state.theses.map((item) => item.category))].sort();
    const categoryIndex = categories.indexOf(thesis.category);
    const members = state.theses.filter((item) => item.category === thesis.category);
    const memberIndex = members.findIndex((item) => item.id === thesis.id);
    const center = sphericalPoint(categoryIndex, categories.length, categories.length === 1 ? 0 : 235);
    const local = sphericalPoint(memberIndex, members.length, 42 + 100 * Math.sqrt((memberIndex + 0.5) / members.length));
    return {
      x: center.x + local.x,
      y: center.y + local.y,
      z: center.z + local.z,
    };
  }

  if (layout === 'year') {
    const years = [...new Set(state.theses.map((item) => Number(item.year)).filter(Number.isFinite))].sort((a, b) => a - b);
    const recordYear = number(thesis.year);
    const yearIndex = recordYear === null ? -1 : years.indexOf(recordYear);
    const value = years.length > 1 && yearIndex >= 0 ? yearIndex / (years.length - 1) : 0.5;
    const peers = state.theses.filter((item) => recordYear === null
      ? number(item.year) === null : Number(item.year) === recordYear);
    const peerIndex = peers.findIndex((item) => item.id === thesis.id);
    const ring = sphericalPoint(peerIndex, peers.length, 115 + wobble * 32);
    return {
      x: (value - 0.5) * 485 + ring.x * 0.22,
      y: ring.y,
      z: ring.z,
    };
  }

  const field = layout === 'pages' ? 'page_count' : 'word_count';
  const value = normalizedMetric(thesis, field);
  const bandCount = 5;
  const band = Math.min(bandCount - 1, Math.floor(value * bandCount));
  const peers = state.theses.filter((item) => Math.min(bandCount - 1,
    Math.floor(normalizedMetric(item, field) * bandCount)) === band);
  const memberIndex = peers.findIndex((item) => item.id === thesis.id);
  const orbit = sphericalPoint(memberIndex, peers.length, 54 + 9 * Math.sqrt((memberIndex + 0.5) / peers.length));
  return { x: (band - (bandCount - 1) / 2) * 145 + orbit.x * 0.28, y: orbit.y, z: orbit.z };
}

/** Choose the displayed advisor group without duplicating co-advised thesis nodes. */
function advisorGroup(thesis) {
  return controls.advisor.value || thesis.advisor_names?.[0] || 'Advisor not published';
}

/** Arrange advisor groups on a centered three-column spatial grid. */
function advisorCenter(index, count) {
  const columns = Math.min(3, count);
  const rows = Math.ceil(count / columns);
  return { x: (index % columns - (columns - 1) / 2) * 325,
    y: (Math.floor(index / columns) - (rows - 1) / 2) * 260,
    z: count === 1 ? 0 : (index % 2 ? 55 : -55) };
}

/** Project advisor names above their groups after connections and nodes are drawn. */
function drawAdvisorLabels() {
  if (controls.layout.value !== 'advisor') return;
  const keys = [...new Set(state.theses.map(advisorGroup))].sort();
  ctx.save();
  ctx.font = '9px "Courier New", monospace';
  ctx.textAlign = 'center';
  keys.forEach((key, index) => {
    const center = project(advisorCenter(index, keys.length));
    const count = state.theses.filter((item) => advisorGroup(item) === key).length;
    const label = `${key} · ${count}`;
    const labelY = center.y - (48 + 15 * Math.sqrt(count)) * viewport().fit * center.depth * state.zoom - 18;
    const width = Math.min(200, ctx.measureText(label).width + 14);
    ctx.fillStyle = 'rgba(255,255,255,.94)';
    ctx.fillRect(center.x - width / 2, labelY - 14, width, 21);
    ctx.strokeStyle = '#d5cce0';
    ctx.lineWidth = 0.6;
    ctx.strokeRect(center.x - width / 2, labelY - 14, width, 21);
    ctx.fillStyle = '#685479';
    ctx.fillText(label, center.x, labelY, width - 10);
  });
  ctx.restore();
}

// Topic labels are extracted vocabulary, not manually assigned research categories.
/** Label exploratory embedding groups without changing catalogue category colors. */
function drawConstellationLabels() {
  if (!['constellations', 'topicLength'].includes(controls.layout.value)) return;
  const data = state.semanticMap?.constellations;
  ctx.save();
  ctx.font = '10px "Courier New", monospace';
  ctx.textAlign = 'center';
  for (const group of visibleConstellations(data, state.theses)) {
    const center = project(constellationCenter(group.index, data.groups.length));
    const label = `C${Number(group.id) + 1} · ${group.keywords.slice(0, 2).join(' / ') || group.label}`;
    const y = center.y - 115 * viewport().fit * center.depth * state.zoom - 20;
    const width = Math.min(165, ctx.measureText(label).width + 12);
    ctx.fillStyle = 'rgba(255,255,255,.94)';
    ctx.fillRect(center.x - width / 2, y - 12, width, 30);
    ctx.fillStyle = '#685479';
    ctx.fillText(label, center.x, y, width - 10);
    ctx.fillText(`${group.members.length} theses in view`, center.x, y + 12, width - 10);
  }
  ctx.restore();
}

/** Describe visible group sizes and median lengths, excluding missing metrics. */
function updateConstellationSummary() {
  const panel = document.querySelector('#constellationSummary');
  panel.hidden = !['constellations', 'topicLength'].includes(controls.layout.value);
  const data = state.semanticMap?.constellations;
  const groups = visibleConstellations(data, state.theses);
  document.querySelector('#constellationList').innerHTML = !data ? '<p>Waiting for semantic groups…</p>'
    : !groups.length ? '<p>No theses in the current view.</p>' : groups.map((group) => {
      const pages = medianMetric(group.members, 'page_count');
      const words = medianMetric(group.members, 'word_count');
      return `<p><strong>C${Number(group.id) + 1} · ${escapeHtml(group.label)}</strong><br />`
        + `${group.members.length} in view / ${group.count} total<br />Median: ${displayNumber(pages)} P · ${displayNumber(words)} W</p>`;
    }).join('');
}

/** Rebuild world positions only when layout/data changes and freeze framing for orbiting. */
function refreshGeometry() {
  updateConstellationSummary();
  state.positions = new Map(state.theses.map((thesis, index) => [
    thesis.id, targetPosition(thesis, index, state.theses.length),
  ]));
  // Frame a new arrangement once, never continuously during orbiting.
  let extentX = 250;
  let extentY = 200;
  for (const position of state.positions.values()) {
    const rotated = rotate(position);
    const depth = 780 / (780 + rotated.z);
    extentX = Math.max(extentX, Math.abs(rotated.x * depth));
    extentY = Math.max(extentY, Math.abs(rotated.y * depth));
  }
  state.fitExtents = { x: extentX, y: extentY };
  draw();
}

/** Reserve stable panel space so selecting a thesis never recenters or rescales the cloud. */
function viewport() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const left = width > 750 ? 317.4 : 227.6;
  // Reserve the detail area before selection so opening it never moves the cloud.
  const right = width > 1050 ? 395 : 28;
  const { x: extentX, y: extentY } = state.fitExtents || { x: 250, y: 200 };
  return {
    x: left + (width - left - right) / 2 - 25,
    y: 90 + (height - 190) / 2,
    fit: Math.max(0.15, Math.min((width - left - right - 130) / (2 * extentX), (height - 220) / (2 * extentY + 100), 1.5)),
  };
}

/** Apply horizontal and vertical camera rotation without changing stored thesis positions. */
function rotate(point) {
  const cosineY = Math.cos(state.yaw);
  const sineY = Math.sin(state.yaw);
  const cosineX = Math.cos(state.pitch);
  const sineX = Math.sin(state.pitch);
  const x = point.x * cosineY - point.z * sineY;
  const z = point.x * sineY + point.z * cosineY;
  return { x, y: point.y * cosineX - z * sineX, z: point.y * sineX + z * cosineX };
}

/** Convert rotated 3D positions to canvas pixels with perspective and manual zoom. */
function project(point, view = viewport()) {
  const rotated = rotate(point);
  const depth = 780 / (780 + rotated.z);
  return {
    x: view.x + rotated.x * depth * state.zoom * view.fit,
    y: view.y + rotated.y * depth * state.zoom * view.fit,
    depth,
    z: rotated.z,
  };
}

/** Match canvas resolution to device pixels while keeping CSS-space coordinates. */
function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(canvas.clientWidth * dpr);
  canvas.height = Math.floor(canvas.clientHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

/** Draw subtle CAD orbit guides, independent of semantic connection evidence. */
function drawOrbitGuides(width, height, context = ctx) {
  const view = viewport();
  const centerX = view.x;
  const centerY = view.y;
  context.save();
  context.strokeStyle = 'rgba(125, 37, 255, 0.09)';
  context.lineWidth = 0.45;
  context.setLineDash([3, 9]);
  [120, 230, 340].forEach((radius) => {
    context.beginPath();
    context.ellipse(centerX, centerY, radius * state.zoom * view.fit, radius * 0.42 * state.zoom * view.fit, -state.yaw * 0.22, 0, Math.PI * 2);
    context.stroke();
  });
  context.setLineDash([]);
  context.fillStyle = 'rgba(125, 37, 255, .9)';
  context.shadowBlur = 20;
  context.shadowColor = '#7d25ff';
  context.beginPath();
  context.arc(centerX, centerY, 4, 0, Math.PI * 2);
  context.fill();
  context.restore();
}

/** Draw one curved relation lane; semantic thickness reflects original-vector similarity. */
function lineBetween(first, second, lane, laneIndex, laneCount, active, context = ctx) {
  if (!first || !second) return;
  const distance = Math.hypot(second.x - first.x, second.y - first.y);
  if (distance < 1) return;
  // Parallel curved lanes make category + year + keywords individually legible.
  const separation = (laneIndex - (laneCount - 1) / 2) * 22;
  const bend = Math.min(distance * 0.12, 35) + separation + (lane.type === 'semantic' ? 20 : 0);
  const controlX = (first.x + second.x) / 2 - (second.y - first.y) / distance * bend;
  const controlY = (first.y + second.y) / 2 + (second.x - first.x) / distance * bend;
  context.save();
  context.strokeStyle = connectionColor(lane, state.lineColors);
  context.globalAlpha = active ? 0.98 : state.selected ? 0.035 : lane.solid ? 0.24 : 0.22;
  context.lineWidth = connectionWidth(lane, active, connectionControls.semantic.checked, state.lineScales[lane.type]);
  if (lane.type === 'semantic') {
    const strength = Math.max(0, Math.min(1, (lane.similarity - 0.2) / 0.65));
    context.globalAlpha = 0.3 + strength * 0.7;
  } else if (active && connectionControls.semantic.checked) {
    context.globalAlpha = 0.24;
  }
  context.setLineDash(connectionPattern(lane, active));
  context.lineCap = 'round';
  context.beginPath();
  context.moveTo(first.x, first.y);
  context.quadraticCurveTo(controlX, controlY, second.x, second.y);
  context.stroke();
  context.restore();
}

/** Render a representative figure and W/P captions with selection-aware fading. */
function paintThumbnail(context, image, x, y, thesis, thumbnailSize, dimmed) {
  context.save();
  context.globalAlpha = dimmed ? 0.22 : 1;
  context.fillStyle = image?.complete && image.naturalWidth ? '#fff' : 'rgba(255,255,255,.92)';
  context.fillRect(x - thumbnailSize / 2, y - thumbnailSize / 2, thumbnailSize, thumbnailSize);
  if (image?.complete && image.naturalWidth) {
    const scale = Math.min(thumbnailSize / image.naturalWidth, thumbnailSize / image.naturalHeight);
    const width = image.naturalWidth * scale;
    const height = image.naturalHeight * scale;
    context.drawImage(image, x - width / 2, y - height / 2, width, height);
  } else {
    context.fillStyle = '#8c829a';
    context.font = '7px "Courier New", monospace';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText('NO FIGURE', x, y);
  }
  context.restore();
  context.save();
  context.globalAlpha = dimmed ? 0.45 : 1;
  context.strokeStyle = 'rgba(150,146,160,.58)';
  context.lineWidth = 0.7;
  context.strokeRect(x - thumbnailSize / 2, y - thumbnailSize / 2, thumbnailSize, thumbnailSize);
  const caption = `${displayNumber(thesis.word_count)} W · ${displayNumber(thesis.page_count)} P`;
  context.font = `${thumbnailSize > 54 ? 8 : 7}px "Courier New", monospace`;
  const captionWidth = Math.max(thumbnailSize, context.measureText(caption).width + 8);
  const captionY = y + thumbnailSize / 2 + 9;
  context.fillStyle = 'rgba(255,255,255,.96)';
  context.fillRect(x - captionWidth / 2, captionY - 6, captionWidth, 12);
  context.fillStyle = '#4c3868';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(caption, x, captionY, captionWidth - 6);
  context.restore();
}

// Cache exact thumbnail artwork at device resolution, including captions and fading.
// This avoids resizing full PDF figures and measuring text on every pointer event.
const thumbnailSprites = new Map();
function drawThumbnail(image, x, y, thesis, thumbnailSize, dimmed) {
  const dpr = window.devicePixelRatio || 1;
  const ready = Boolean(image?.complete && image.naturalWidth);
  const key = JSON.stringify([thesis.id, thesis.image_url, thesis.word_count, thesis.page_count, thumbnailSize, dimmed, ready, dpr]);
  let sprite = thumbnailSprites.get(key);
  if (!sprite) {
    ctx.save();
    ctx.font = `${thumbnailSize > 54 ? 8 : 7}px "Courier New", monospace`;
    const caption = `${displayNumber(thesis.word_count)} W · ${displayNumber(thesis.page_count)} P`;
    const width = Math.ceil(Math.max(thumbnailSize, ctx.measureText(caption).width + 8) + 4);
    ctx.restore();
    const height = thumbnailSize + 20;
    const surface = document.createElement('canvas');
    surface.width = Math.ceil(width * dpr);
    surface.height = Math.ceil(height * dpr);
    const context = surface.getContext('2d');
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    paintThumbnail(context, image, width / 2, thumbnailSize / 2 + 2, thesis, thumbnailSize, dimmed);
    sprite = { surface, width, height };
    if (thumbnailSprites.size >= 256) thumbnailSprites.delete(thumbnailSprites.keys().next().value);
    thumbnailSprites.set(key, sprite);
  }
  ctx.drawImage(sprite.surface, 0, 0, sprite.width * dpr, sprite.height * dpr,
    x - sprite.width / 2, y - thumbnailSize / 2 - 2, sprite.width, sprite.height);
}

/** Draw the category-colored point and its thumbnail, emphasizing visible relationships. */
function drawNode(projected, relatedIds = new Set()) {
  const { thesis, x, y, depth } = projected;
  const size = nodeRadius(thesis) * (0.8 + depth * 0.35);
  const color = categoryColor(thesis.category);
  const active = thesis.id === state.selected?.id;
  const hovered = thesis.id === state.hovered?.id;
  const dimmed = Boolean(state.selected && !relatedIds.has(thesis.id) && !active);
  ctx.save();
  if (active || hovered) {
    ctx.shadowColor = color;
    ctx.shadowBlur = active ? 20 : 11;
  }
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, size, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.arc(x, y, Math.max(1.3, size * 0.27), 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  const image = state.images.get(thesis.id);
  const thumbnailSize = active ? 66 : dimmed ? 36 : hovered ? 56 : 48;
  const thumbnailX = x + size + 8 + thumbnailSize / 2;
  const thumbnailY = y - size - 10;
  drawThumbnail(image, thumbnailX, thumbnailY, thesis, thumbnailSize, dimmed);
  if (active) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.1;
    ctx.setLineDash([2, 3]);
    ctx.beginPath();
    ctx.arc(x, y, size + 9, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }
}

/** Render connections first, depth-sorted nodes next, and readable group labels last. */
// Cache background connections/projections across hover changes. Any camera, data,
// selection, filter, or width change invalidates the layer; no edges are omitted.
let sceneSignature = [];
let connectionLayer;
let projectedById = new Map();
let sceneRelatedIds = new Set();
function draw() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);
  const signature = [width, height, canvas.width, canvas.height, state.positions, state.theses,
    state.relations, state.semanticNeighbors, state.selected?.id, state.yaw, state.pitch, state.zoom,
    ...Object.values(connectionControls).map((input) => input.checked), ...Object.values(state.lineScales),
    ...Object.values(state.lineColors || {})];
  const rebuild = signature.length !== sceneSignature.length || signature.some((value, index) => value !== sceneSignature[index]);
  if (rebuild) {
    if (!connectionLayer) connectionLayer = document.createElement('canvas');
    if (connectionLayer.width !== canvas.width) connectionLayer.width = canvas.width;
    if (connectionLayer.height !== canvas.height) connectionLayer.height = canvas.height;
    const layerContext = connectionLayer.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    layerContext.setTransform(dpr, 0, 0, dpr, 0, 0);
    layerContext.clearRect(0, 0, width, height);
    drawOrbitGuides(width, height, layerContext);
    const view = viewport();
    state.projection = state.theses.map((thesis, index) => ({
      thesis,
      ...project(state.positions.get(thesis.id) || targetPosition(thesis, index, state.theses.length), view),
    }));

    projectedById = new Map(state.projection.map((item) => [item.thesis.id, item]));
    sceneRelatedIds = relatedThesisIds();
    const semanticEdges = state.selected && connectionControls.semantic.checked ? state.semanticNeighbors.map((match) => ({
      a: state.selected.id, b: match.id,
      lanes: [{ type: 'semantic', color: '#7d25ff', solid: true, similarity: match.similarity }],
    })) : [];
    const edges = [...state.relations, ...semanticEdges].map((relation) => ({
      ...relation, active: Boolean(state.selected && (relation.a === state.selected.id || relation.b === state.selected.id)),
    })).sort((a, b) => Number(a.active) - Number(b.active));
    for (const edge of edges) {
      const lanes = edge.lanes.filter((lane) => connectionControls[lane.type].checked);
      lanes.forEach((lane, index) => lineBetween(
        projectedById.get(edge.a), projectedById.get(edge.b), lane, index, lanes.length, edge.active, layerContext,
      ));
    }
    state.hitProjection = [...state.projection].sort((a, b) => a.z - b.z);
    sceneSignature = signature;
  }
  ctx.drawImage(connectionLayer, 0, 0, width, height);
  [...state.projection].sort((a, b) => b.z - a.z).forEach((item) => drawNode(item, sceneRelatedIds));
  if (state.selected) {
    const selected = projectedById.get(state.selected.id);
    if (selected) drawNode(selected, sceneRelatedIds);
  }
  drawAdvisorLabels();
  drawConstellationLabels();
}

/** Combine enabled semantic and metadata neighbors for selection highlighting. */
function relatedThesisIds() {
  const related = new Set();
  if (!state.selected) return related;
  related.add(state.selected.id);
  if (connectionControls.semantic.checked) state.semanticNeighbors.forEach((item) => related.add(item.id));
  for (const relation of state.relations) {
    const otherId = relation.a === state.selected.id ? relation.b
      : relation.b === state.selected.id ? relation.a : null;
    if (otherId !== null && relation.lanes.some((lane) => connectionControls[lane.type].checked)) {
      related.add(otherId);
    }
  }
  return related;
}

let drawFrame;
/** Coalesce image loads, dragging, and zoom events into one screen refresh. */
function requestDraw() {
  if (drawFrame) return;
  drawFrame = requestAnimationFrame(() => { drawFrame = null; draw(); });
}

/** Cache source figures and discard failed images instead of inventing replacements. */
function loadImages() {
  state.theses.forEach((thesis) => {
    const previous = state.images.get(thesis.id);
    if (previous?.dataset.url === thesis.image_url) return;
    state.images.delete(thesis.id);
    if (!thesis.image_url) return;
    const image = new Image();
    image.dataset.url = thesis.image_url;
    image.onload = requestDraw;
    image.onerror = () => state.images.delete(thesis.id);
    image.src = thesis.image_url;
    state.images.set(thesis.id, image);
  });
}

/** Refresh category filters and legend while retaining a still-valid selection. */
function updateCategoryOptions() {
  const current = controls.category.value;
  const categories = state.categories.map((item) => item.category).sort();
  controls.category.innerHTML = '<option value="">All categories</option>' + categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`).join('');
  controls.category.value = categories.includes(current) ? current : '';
  document.querySelector('#categoryKey').innerHTML = categories.map((category) => `
    <button type="button" data-category="${escapeHtml(category)}" class="${current === category ? 'active' : ''}">
      <i style="background:${categoryColor(category)}"></i>${escapeHtml(category)}
    </button>`).join('');
}

/** Escape source text before inserting it into dynamic HTML. */
function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}

/** Serialize current filters, omitting range endpoints that impose no restriction. */
function queryParams() {
  const params = new URLSearchParams();
  const fields = [
    ['q', controls.search.value], ['category', controls.category.value],
    ['advisor', controls.advisor.value], ['mode', controls.searchMode.value],
  ];
  fields.forEach(([key, value]) => { if (value.trim()) params.set(key, value.trim()); });
  const filters = [
    { min: state.minYear, max: state.maxYear, controls: rangeSliders.year, params: ['year_min', 'year_max'] },
    { min: state.ranges.pages.min, max: state.ranges.pages.max, controls: rangeSliders.pages, params: ['page_min', 'page_max'] },
    { min: state.ranges.words.min, max: state.ranges.words.max, controls: rangeSliders.words, params: ['word_min', 'word_max'] },
  ];
  for (const filter of filters) {
    if (filter.min !== null && Number(filter.controls.min.value) > filter.min) {
      params.set(filter.params[0], filter.controls.min.value);
    }
    if (filter.max !== null && Number(filter.controls.max.value) < filter.max) {
      params.set(filter.params[1], filter.controls.max.value);
    }
  }
  return params;
}

/** Initialize a paired-handle range from source bounds, retaining missing-data states. */
function setRangeSlider(key, minimum, maximum) {
  const config = rangeSliders[key];
  const min = minimum === null ? null : Number(minimum);
  const max = maximum === null ? null : Number(maximum);
  if (key === 'year') {
    state.minYear = min;
    state.maxYear = max;
  } else {
    state.ranges[key] = { min, max };
  }
  const lower = min ?? 0;
  const upper = max ?? lower;
  for (const slider of [config.min, config.max]) {
    slider.min = lower;
    slider.max = upper;
    slider.step = 1;
  }
  config.min.value = lower;
  config.max.value = upper;
  updateRangeSlider(key);
}

/** Synchronize range labels and the filled track, separating overlapping labels. */
function updateRangeSlider(key) {
  const config = rangeSliders[key];
  const bounds = key === 'year' ? { min: state.minYear, max: state.maxYear } : state.ranges[key];
  const start = Number(config.min.value);
  const end = Number(config.max.value);
  const span = bounds.max - bounds.min;
  const normalizedStart = span > 0 ? ((start - bounds.min) / span) * 100 : 0;
  const endPosition = span > 0 ? ((end - bounds.min) / span) * 100 : 100;
  config.minLabel.textContent = bounds.min === null ? '—' : new Intl.NumberFormat().format(start);
  config.maxLabel.textContent = bounds.max === null ? '—' : new Intl.NumberFormat().format(end);
  config.minLabel.style.left = `${normalizedStart}%`;
  config.maxLabel.style.left = `${endPosition}%`;
  const overlap = endPosition - normalizedStart < 12;
  config.minLabel.classList.toggle('is-overlap-min', overlap);
  config.maxLabel.classList.toggle('is-overlap-max', overlap);
  config.fill.style.left = `${normalizedStart}%`;
  config.fill.style.width = `${Math.max(0, endPosition - normalizedStart)}%`;
}

/** Initialize year, page, and word sliders from collection statistics. */
function setRangeControls(data) {
  setRangeSlider('year', data.year_min, data.year_max);
  setRangeSlider('pages', data.page_min, data.page_max);
  setRangeSlider('words', data.word_min, data.word_max);
}

/** Load catalogue totals, advisor options, and numeric filter bounds. */
async function fetchStats() {
  const response = await fetch('/api/stats');
  if (!response.ok) throw new Error('Could not load the collection.');
  const data = await response.json();
  state.categories = data.categories;
  state.total = data.total;
  state.advisors = data.advisors || [];
  const previous = controls.advisor.value;
  controls.advisor.innerHTML = '<option value="">All advisors</option>' + state.advisors.map((item) =>
    `<option value="${escapeHtml(item.name)}">${escapeHtml(item.name)} (${item.count})</option>`).join('');
  controls.advisor.value = state.advisors.some((item) => item.name === previous) ? previous : '';
  setRangeControls(data);
}

/** Fetch full-dimensional group assignments and approximate 3D projection coordinates. */
async function fetchSemanticMap() {
  const status = document.querySelector('#semanticStatus');
  try {
    const response = await fetch('/api/semantic/map');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Semantic map unavailable.');
    state.semanticMap = data;
    status.textContent = `${data.passages} indexed passages · search ready`;
    refreshGeometry();
  } catch (error) { status.textContent = error.message; }
}

let neighborVersion = 0;
/** Fetch ranked neighbors; ignore responses for a selection that has since changed. */
async function loadSemanticNeighbors() {
  const version = ++neighborVersion;
  const selectedId = state.selected?.id;
  if (!selectedId) return;
  const status = document.querySelector('#neighborStatus');
  status.textContent = 'Finding the closest abstracts…';
  state.semanticNeighbors = [];
  document.querySelector('#semanticNeighbors').replaceChildren();
  updateConnectionDetail();
  draw();
  const params = new URLSearchParams({ id: selectedId, k: controls.neighborCount.value,
    minimum: controls.similarityMin.value, ids: state.theses.map((item) => item.id).join(',') });
  try {
    const response = await fetch(`/api/semantic/neighbors?${params}`);
    const data = await response.json();
    if (version !== neighborVersion || state.selected?.id !== selectedId) return;
    if (!response.ok) throw new Error(data.error || 'Could not find semantic neighbors.');
    state.semanticNeighbors = data.neighbors;
    status.textContent = data.neighbors.length ? `${data.neighbors.length} closest in the current view · cosine similarity`
      : 'No thesis meets this similarity threshold. Try a lower value.';
    document.querySelector('#semanticNeighbors').innerHTML = data.neighbors.map((match) =>
      `<button type="button" data-thesis="${match.id}"><span>${escapeHtml(match.title)}</span><strong>${match.similarity.toFixed(2)}</strong></button>`).join('');
    updateConnectionDetail();
    if (controls.layout.value === 'neighborhood') refreshGeometry(); else draw();
  } catch (error) {
    if (version === neighborVersion && state.selected?.id === selectedId) status.textContent = error.message;
  }
}

let loadVersion = 0;
/** Load filtered/ranked records and reject stale responses from earlier searches. */
async function fetchTheses() {
  const version = ++loadVersion;
  const response = await fetch(`/api/theses?${queryParams()}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Could not load the thesis database.');
  if (version !== loadVersion) return;
  state.theses = data.theses;
  const semanticSearch = Boolean(controls.search.value && controls.searchMode.value === 'semantic');
  document.querySelector('#searchResults').hidden = !semanticSearch;
  document.querySelector('#searchResultsList').innerHTML = semanticSearch ? data.theses.map((item) =>
    `<button type="button" data-thesis="${item.id}"><span>${escapeHtml(item.title)}</span><strong>${item.semantic_similarity.toFixed(2)}</strong></button>`).join('') : '';
  state.relations = buildRelations(state.theses);
  if (state.selected && !state.theses.some((thesis) => thesis.id === state.selected.id)) closeDetail();
  else if (state.selected) displayDetail(state.theses.find((thesis) => thesis.id === state.selected.id));
  updateCategoryOptions();
  updateLayoutGuide();
  loadImages();
  document.querySelector('#recordCount').textContent = controls.search.value && controls.searchMode.value === 'semantic'
    ? `${state.theses.length} closest thesis results, ranked by meaning.`
    : `${state.theses.length} / ${state.total} thesis records in view.`;
  refreshGeometry();
}

/** Populate source evidence and metadata without moving the ordinary overview. */
function displayDetail(thesis) {
  if (state.selected?.id !== thesis.id) state.semanticNeighbors = [];
  state.selected = thesis;
  document.querySelector('#detailCategory').textContent = thesis.category || 'UNCATEGORIZED';
  document.querySelector('#detailTitle').textContent = thesis.title;
  document.querySelector('#detailByline').textContent = [thesis.author, thesis.year].filter(Boolean).join(' · ') || 'Author and year unavailable';
  document.querySelector('#detailPages').textContent = displayNumber(thesis.page_count);
  document.querySelector('#detailWords').textContent = displayNumber(thesis.word_count);
  document.querySelector('#detailYear').textContent = thesis.year || '—';
  document.querySelector('#detailSummary').textContent = thesis.ai_summary || thesis.source_abstract || 'No summary has been added yet.';
  document.querySelector('#summaryHeading').textContent = thesis.ai_summary ? 'AI SUMMARY' : 'SOURCE ABSTRACT';
  document.querySelector('#detailKeywords').textContent = thesis.keywords || 'No keywords available.';
  document.querySelector('#detailAdvisors').textContent = thesis.advisor_names?.join(' · ') || 'Not published in KiltHub metadata';
  document.querySelector('#detailAdvisors').title = thesis.advisors ? `As published by KiltHub: ${thesis.advisors}` : '';
  const advisorSource = document.querySelector('#advisorSource');
  advisorSource.hidden = !thesis.advisor_source;
  if (thesis.advisor_source) advisorSource.href = thesis.advisor_source.split('#')[0];
  document.querySelector('#searchEvidence').hidden = !thesis.semantic_excerpt;
  document.querySelector('#searchExcerpt').textContent = thesis.semantic_excerpt
    ? `Similarity ${thesis.semantic_similarity.toFixed(2)} · ${thesis.semantic_source}, passage ${thesis.semantic_passage}: “${thesis.semantic_excerpt}”` : '';
  const image = document.querySelector('#detailImage');
  const fallback = document.querySelector('#imageFallback');
  image.hidden = !thesis.image_url;
  fallback.hidden = Boolean(thesis.image_url);
  image.onerror = () => { image.hidden = true; fallback.hidden = false; };
  if (thesis.image_url) image.src = thesis.image_url; else image.removeAttribute('src');
  image.alt = thesis.image_url ? `Representative image for ${thesis.title}` : '';
  document.querySelector('#imageSource').textContent = thesis.image_source || '';
  const source = document.querySelector('#sourceLink');
  source.href = thesis.source_url || '#';
  source.hidden = !thesis.source_url;
  detailPanel.classList.add('open');
  updateConnectionDetail();
  if (controls.layout.value === 'neighborhood') refreshGeometry(); else draw();
  loadSemanticNeighbors();
}

/** Explain which enabled connections come from meaning versus exact metadata. */
function updateConnectionDetail() {
  if (!state.selected) return;
  const counts = { category: 0, year: 0, keywords: 0, advisor: 0 };
  for (const relation of state.relations) {
    if (relation.a !== state.selected.id && relation.b !== state.selected.id) continue;
    for (const lane of relation.lanes) {
      if (connectionControls[lane.type].checked) counts[lane.type] += 1;
    }
  }
  document.querySelector('#detailConnections').textContent =
    `${state.semanticNeighbors.length} semantic neighbors · ${counts.advisor} share an advisor · ${counts.category} share a category · ${counts.year} share a year · ${counts.keywords} share keywords. Metadata connections are exact matches.`;
}

/** Dismiss details and semantic emphasis; only explicit neighborhood mode rearranges. */
function closeDetail() {
  state.selected = null;
  neighborVersion += 1;
  state.semanticNeighbors = [];
  detailPanel.classList.remove('open');
  if (controls.layout.value === 'neighborhood') refreshGeometry(); else draw();
}

/** Position a plain-text thesis tooltip next to the cursor. */
function showTooltip(thesis, event) {
  tooltip.textContent = `${thesis.title} · ${thesis.category}`;
  tooltip.style.left = `${event.clientX}px`;
  tooltip.style.top = `${event.clientY}px`;
  tooltip.classList.add('visible');
}

/** Hide hover text when dragging or leaving a point. */
function hideTooltip() {
  tooltip.classList.remove('visible');
}

/** Resolve pointer hits against the same projected point/thumbnail sizes used for drawing. */
function hitTest(clientX, clientY) {
  const bounds = canvas.getBoundingClientRect();
  const x = clientX - bounds.left;
  const y = clientY - bounds.top;
  const relatedIds = sceneRelatedIds;
  return (state.hitProjection || []).find((item) => {
    const nodeSize = nodeRadius(item.thesis) * (0.8 + item.depth * 0.35);
    if (Math.hypot(item.x - x, item.y - y) <= Math.max(12, nodeSize + 11)) return true;
    const active = item.thesis.id === state.selected?.id;
    const hovered = item.thesis.id === state.hovered?.id;
    const dimmed = Boolean(state.selected && !relatedIds.has(item.thesis.id) && !active);
    const thumbSize = active ? 66 : dimmed ? 36 : hovered ? 56 : 48;
    const thumbX = item.x + nodeSize + 8 + thumbSize / 2;
    const thumbY = item.y - nodeSize - 10;
    return Math.abs(x - thumbX) <= Math.max(50, thumbSize / 2)
      && y >= thumbY - thumbSize / 2 && y <= thumbY + thumbSize / 2 + 18;
  })?.thesis || null;
}

/** Open a blank or prefilled metadata form without saving anything yet. */
function openForm(thesis = null) {
  state.editId = thesis?.id ?? null;
  form.reset();
  document.querySelector('#dialogMode').textContent = thesis ? 'EDIT RECORD' : 'NEW RECORD';
  document.querySelector('#dialogTitle').textContent = thesis ? 'Edit thesis' : 'Add a thesis';
  document.querySelector('#formError').textContent = '';
  if (thesis) {
    Object.entries(thesis).forEach(([key, value]) => {
      const field = form.elements.namedItem(key);
      if (field && value !== null) field.value = value;
    });
  }
  dialog.showModal();
}

/** Persist an addition/edit, then refresh records, statistics, and vector-derived layouts. */
async function saveForm(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  const method = state.editId ? 'PUT' : 'POST';
  const url = state.editId ? `/api/theses/${state.editId}` : '/api/theses';
  const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  const result = await response.json();
  if (!response.ok) {
    document.querySelector('#formError').textContent = result.error || 'Could not save this record.';
    return;
  }
  dialog.close();
  await fetchStats();
  await fetchTheses();
  displayDetail(result);
  await fetchSemanticMap();
}

/** Delete only the explicitly confirmed thesis and refresh both catalogue and map. */
async function deleteSelected() {
  if (!state.selected || !confirm(`Delete “${state.selected.title}”?`)) return;
  const response = await fetch(`/api/theses/${state.selected.id}`, { method: 'DELETE' });
  if (!response.ok) return alert('The thesis could not be deleted.');
  closeDetail();
  await fetchStats();
  await fetchTheses();
  await fetchSemanticMap();
}

let filterTimer;
/** Debounce typing and sliders to avoid sending a request for every input event. */
function scheduleLoad() {
  clearTimeout(filterTimer);
  filterTimer = setTimeout(() => fetchTheses().catch((error) => {
    document.querySelector('#recordCount').textContent = error.message;
  }), 220);
}

controls.search.addEventListener('input', scheduleLoad);
controls.searchMode.addEventListener('change', scheduleLoad);
controls.advisor.addEventListener('change', scheduleLoad);
let neighborTimer;
for (const input of [controls.neighborCount, controls.similarityMin]) {
  input.addEventListener('input', () => {
    document.querySelector('#neighborCountLabel').textContent = controls.neighborCount.value;
    document.querySelector('#similarityLabel').textContent = Number(controls.similarityMin.value).toFixed(2);
    clearTimeout(neighborTimer);
    neighborTimer = setTimeout(loadSemanticNeighbors, 200);
  });
}
/** Navigate from ranked search or recommendation lists to the corresponding node. */
function selectThesisFromList(event) {
  const button = event.target.closest('[data-thesis]');
  const thesis = button && state.theses.find((item) => item.id === Number(button.dataset.thesis));
  if (thesis) displayDetail(thesis);
}
document.querySelector('#semanticNeighbors').addEventListener('click', selectThesisFromList);
document.querySelector('#searchResultsList').addEventListener('click', selectThesisFromList);
for (const [key, config] of Object.entries(rangeSliders)) {
  [config.min, config.max].forEach((slider) => slider.addEventListener('input', () => {
    if (Number(config.min.value) > Number(config.max.value)) {
      if (slider === config.min) config.max.value = slider.value;
      else config.min.value = slider.value;
    }
    updateRangeSlider(key);
    scheduleLoad();
  }));
}
controls.category.addEventListener('input', scheduleLoad);
const layoutDescriptions = {
  constellations: 'Exploratory abstract-based groups, not official topics. Labels use title terms; filters keep groups fixed.',
  topicLength: 'Topic groups with longer documents higher and larger. Choose pages or words below; missing lengths sit lowest.',
  semantic: 'Nearby points suggest similar abstracts. The 3D projection is approximate.',
  neighborhood: 'Select a thesis: it moves to the center, with semantic neighbors around it. Higher similarity brings a neighbor closer.',
  advisor: 'Groups use the first advisor listed by KiltHub. The advisor filter includes all co-advised theses.',
  category: 'Theses form category clusters; each point keeps its category colour.',
  cloud: 'All theses share one rotatable 3D cloud, without metric grouping.',
  year: 'Theses line up in bands from the oldest posting year to the newest.',
  pages: 'Five page-count galaxies run from fewer pages on the left to more on the right.',
  words: 'Five word-count galaxies run from fewer words on the left to more on the right.',
};
/** Explain each layout and show numeric axes only where their direction is meaningful. */
function updateLayoutGuide() {
  const layout = controls.layout.value;
  document.querySelector('#layoutHelp').textContent = layoutDescriptions[layout];
  const axis = document.querySelector('#metricAxis');
  const field = layout === 'pages' ? 'page_count' : layout === 'words' ? 'word_count' : null;
  axis.hidden = !field;
  if (!field) return;
  const range = metricRange(field);
  const unit = field === 'page_count' ? 'PAGES' : 'WORDS';
  document.querySelector('#metricAxisLow').textContent = `${displayNumber(range.min)} ${unit} · FEWER`;
  document.querySelector('#metricAxisHigh').textContent = `${displayNumber(range.max)} ${unit} · MORE`;
}
controls.layout.addEventListener('change', () => {
  if (controls.layout.value === 'topicLength' && controls.size.value === 'equal') controls.size.value = 'pages';
  updateLayoutGuide(); refreshGeometry();
});
controls.size.addEventListener('change', () => {
  if (controls.layout.value === 'topicLength') {
    if (controls.size.value === 'equal') controls.size.value = 'pages';
    refreshGeometry();
  } else draw();
});
Object.values(connectionControls).forEach((input) => input.addEventListener('change', () => {
  updateConnectionDetail();
  draw();
}));

/** Open a per-type width editor without toggling visibility or changing camera state. */
function updateLineWidthEditor() {
  const type = state.editedLineType;
  const editor = document.querySelector('#lineWidthEditor');
  editor.hidden = !type;
  document.querySelectorAll('[data-line-type]').forEach((button) => {
    const selected = button.dataset.lineType === type;
    button.setAttribute('aria-expanded', String(selected));
    if (selected) {
      // Move the existing editor (and its listeners) directly below this row.
      button.closest('.connection-row').insertAdjacentElement('afterend', editor);
      document.querySelector('#lineWidthTitle').textContent = button.textContent;
    }
  });
  if (!type) return;
  const percent = Math.round(state.lineScales[type] * 100);
  document.querySelector('#lineWidthSlider').value = percent;
  document.querySelector('#lineWidthValue').textContent = `${percent}%`;
  const palette = { semantic: '#7d25ff', advisor: '#5b7892', year: '#219fb3', keywords: '#d84b9b',
    category: categoryColor(state.selected?.category || state.theses[0]?.category || 'Uncategorized') };
  document.querySelector('#lineColorPicker').value = state.lineColors[type] || palette[type];
}
document.querySelectorAll('[data-line-type]').forEach((button) => button.addEventListener('click', () => {
  state.editedLineType = state.editedLineType === button.dataset.lineType ? null : button.dataset.lineType;
  updateLineWidthEditor();
}));
document.querySelector('#lineWidthSlider').addEventListener('input', (event) => {
  if (!state.editedLineType) return;
  state.lineScales[state.editedLineType] = Number(event.target.value) / 100;
  document.querySelector('#lineWidthValue').textContent = `${event.target.value}%`;
  requestDraw();
});
// Native color input opens the browser's compact RGB picker; only lines are recolored.
document.querySelector('#lineColorPicker').addEventListener('input', (event) => {
  const type = state.editedLineType;
  if (!type) return;
  state.lineColors[type] = event.target.value;
  document.documentElement.style.setProperty(`--${type}-line-color`, event.target.value);
  document.querySelector(`[data-legend-color="${type}"]`).textContent = 'Custom color';
  requestDraw();
});
document.querySelector('#resetLineWidths').addEventListener('click', () => {
  state.lineScales = defaultLineScales();
  updateLineWidthEditor();
  draw();
});
document.querySelector('#categoryKey').addEventListener('click', (event) => {
  const button = event.target.closest('[data-category]');
  if (!button) return;
  controls.category.value = controls.category.value === button.dataset.category ? '' : button.dataset.category;
  fetchTheses().catch(console.error);
});
/** Remove color overrides, restoring the source palette and matching legend labels. */
function resetLineColors() {
  state.lineColors = defaultLineColors();
  const labels = { semantic: 'Semantic link', advisor: 'Advisor link', category: 'Category link', year: 'Year link', keywords: 'Keyword link' };
  for (const [type, label] of Object.entries(labels)) {
    document.documentElement.style.removeProperty(`--${type}-line-color`);
    document.querySelector(`[data-legend-color="${type}"]`).textContent = label;
  }
  updateLineWidthEditor();
  requestDraw();
}

document.querySelector('#resetFilters').addEventListener('click', () => {
  [controls.search, controls.category, controls.advisor].forEach((control) => { control.value = ''; });
  for (const [key, config] of Object.entries(rangeSliders)) {
    const bounds = key === 'year' ? { min: state.minYear, max: state.maxYear } : state.ranges[key];
    config.min.value = bounds.min ?? 0;
    config.max.value = bounds.max ?? 0;
    updateRangeSlider(key);
  }
  resetLineColors();
  fetchTheses().then(updateLineWidthEditor).catch(console.error);
});
document.querySelector('#openAddButton').addEventListener('click', () => openForm());
document.querySelector('#closeDetailButton').addEventListener('click', closeDetail);
document.querySelector('#editButton').addEventListener('click', () => openForm(state.selected));
document.querySelector('#deleteButton').addEventListener('click', deleteSelected);
document.querySelector('#closeDialogButton').addEventListener('click', () => dialog.close());
document.querySelector('#cancelButton').addEventListener('click', () => dialog.close());
form.addEventListener('submit', saveForm);

canvas.addEventListener('pointerdown', (event) => {
  state.dragging = true;
  state.dragDistance = 0;
  state.pointer.lastX = event.clientX;
  state.pointer.lastY = event.clientY;
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener('pointermove', (event) => {
  if (state.dragging) {
    const changeX = event.clientX - state.pointer.lastX;
    const changeY = event.clientY - state.pointer.lastY;
    state.dragDistance += Math.abs(changeX) + Math.abs(changeY);
    state.yaw += changeX * 0.008;
    state.pitch = Math.max(-Math.PI, Math.min(Math.PI, state.pitch + changeY * 0.006));
    state.pointer.lastX = event.clientX;
    state.pointer.lastY = event.clientY;
    hideTooltip();
    requestDraw();
    return;
  }
  const thesis = hitTest(event.clientX, event.clientY);
  const changed = state.hovered?.id !== thesis?.id;
  state.hovered = thesis;
  canvas.style.cursor = thesis ? 'pointer' : 'grab';
  if (thesis) showTooltip(thesis, event); else hideTooltip();
  if (changed) requestDraw();
});
canvas.addEventListener('pointerup', (event) => {
  const wasDragging = state.dragDistance > 5;
  state.dragging = false;
  canvas.releasePointerCapture(event.pointerId);
  if (!wasDragging) {
    const thesis = hitTest(event.clientX, event.clientY);
    if (thesis) displayDetail(thesis);
  }
});
canvas.addEventListener('pointerleave', () => { state.hovered = null; hideTooltip(); requestDraw(); });
canvas.addEventListener('wheel', (event) => {
  event.preventDefault();
  state.zoom = wheelZoom(state.zoom, event.deltaY, event.deltaMode, canvas.clientHeight);
  requestDraw();
}, { passive: false });
window.addEventListener('resize', resizeCanvas);

resizeCanvas();
fetchStats().then(fetchTheses).catch((error) => {
  document.querySelector('#recordCount').textContent = error.message;
  console.error(error);
});
fetchSemanticMap();
