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
  year: document.querySelector('#yearFilter'),
  pageMin: document.querySelector('#pageMin'),
  pageMax: document.querySelector('#pageMax'),
  wordMin: document.querySelector('#wordMin'),
  wordMax: document.querySelector('#wordMax'),
};

const palette = ['#7d25ff', '#ee45aa', '#2972ff', '#ff794c', '#11a88a', '#a89b13', '#7256cb'];
const state = {
  theses: [],
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

function number(value) {
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

function displayNumber(value) {
  const parsed = number(value);
  return parsed === null ? '—' : new Intl.NumberFormat().format(parsed);
}

function categoryColor(category) {
  const categories = [...new Set(state.theses.map((thesis) => thesis.category))].sort();
  return palette[Math.max(0, categories.indexOf(category)) % palette.length];
}

function cleanKeywords(value = '') {
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

function similarity(first, second) {
  if (first.category === second.category) return 1;
  const firstWords = new Set(cleanKeywords(first.keywords).map((item) => item.toLowerCase()));
  const overlap = cleanKeywords(second.keywords).some((item) => firstWords.has(item.toLowerCase()));
  return overlap ? 0.52 : 0;
}

function hash(value) {
  let result = 0;
  for (let index = 0; index < value.length; index += 1) result = (result * 31 + value.charCodeAt(index)) | 0;
  return Math.abs(result);
}

function metricRange(field) {
  const values = state.theses.map((thesis) => number(thesis[field])).filter((value) => value !== null && value > 0);
  return { min: Math.min(...values, 0), max: Math.max(...values, 1) };
}

function normalizedMetric(thesis, field) {
  const value = number(thesis[field]);
  if (value === null || value <= 0) return 0.4;
  const { min, max } = metricRange(field);
  return max === min ? 0.65 : (value - min) / (max - min);
}

function nodeRadius(thesis) {
  if (controls.size.value === 'equal') return 5.5;
  const field = controls.size.value === 'pages' ? 'page_count' : 'word_count';
  return 4.2 + normalizedMetric(thesis, field) * 8;
}

function targetPosition(thesis, index, count) {
  const layout = controls.layout.value;
  const seed = hash(`${thesis.id}-${thesis.title}`);
  const wobble = ((seed % 100) / 100 - 0.5);

  if (layout === 'category') {
    const categories = [...new Set(state.theses.map((item) => item.category))].sort();
    const categoryIndex = categories.indexOf(thesis.category);
    const members = state.theses.filter((item) => item.category === thesis.category);
    const memberIndex = members.findIndex((item) => item.id === thesis.id);
    const mainAngle = (categoryIndex / categories.length) * Math.PI * 2 - Math.PI / 2;
    const clusterDistance = 190;
    const innerAngle = (memberIndex / Math.max(members.length, 1)) * Math.PI * 2 + wobble;
    const localRadius = 38 + (memberIndex % 3) * 21;
    return {
      x: Math.cos(mainAngle) * clusterDistance + Math.cos(innerAngle) * localRadius,
      y: Math.sin(mainAngle) * clusterDistance * 0.55 + Math.sin(innerAngle) * localRadius,
      z: ((memberIndex % 4) - 1.5) * 35 + wobble * 22,
    };
  }

  const field = layout === 'year' ? 'year' : layout === 'pages' ? 'page_count' : 'word_count';
  const value = normalizedMetric(thesis, field);
  const angle = (index / Math.max(count, 1)) * Math.PI * 6 + wobble;
  return {
    x: (value - 0.5) * 550,
    y: Math.sin(angle) * (74 + (seed % 65)),
    z: Math.cos(angle) * 125 + wobble * 55,
  };
}

function rotate(point) {
  const cosineY = Math.cos(state.yaw);
  const sineY = Math.sin(state.yaw);
  const cosineX = Math.cos(state.pitch);
  const sineX = Math.sin(state.pitch);
  const x = point.x * cosineY - point.z * sineY;
  const z = point.x * sineY + point.z * cosineY;
  return { x, y: point.y * cosineX - z * sineX, z: point.y * sineX + z * cosineX };
}

function project(point) {
  const rotated = rotate(point);
  const depth = 780 / (780 + rotated.z);
  return {
    x: canvas.width / (window.devicePixelRatio * 2) + rotated.x * depth * state.zoom,
    y: canvas.height / (window.devicePixelRatio * 2) + rotated.y * depth * state.zoom,
    depth,
    z: rotated.z,
  };
}

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(canvas.clientWidth * dpr);
  canvas.height = Math.floor(canvas.clientHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function drawOrbitGuides(width, height) {
  const centerX = width / 2;
  const centerY = height / 2;
  ctx.save();
  ctx.strokeStyle = 'rgba(125, 37, 255, 0.15)';
  ctx.lineWidth = 0.65;
  ctx.setLineDash([3, 9]);
  [120, 230, 340].forEach((radius) => {
    ctx.beginPath();
    ctx.ellipse(centerX, centerY, radius * state.zoom, radius * 0.42 * state.zoom, -state.yaw * 0.22, 0, Math.PI * 2);
    ctx.stroke();
  });
  ctx.setLineDash([]);
  ctx.fillStyle = 'rgba(125, 37, 255, .9)';
  ctx.shadowBlur = 20;
  ctx.shadowColor = '#7d25ff';
  ctx.beginPath();
  ctx.arc(centerX, centerY, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function lineBetween(first, second, active) {
  ctx.save();
  ctx.strokeStyle = active ? 'rgba(125, 37, 255, .98)' : 'rgba(129, 101, 194, .38)';
  ctx.lineWidth = active ? 2.2 : 0.55;
  ctx.setLineDash(active ? [] : [1.5, 5]);
  if (active) {
    ctx.shadowColor = '#a600ff';
    ctx.shadowBlur = 8;
  }
  ctx.beginPath();
  ctx.moveTo(first.x, first.y);
  ctx.lineTo(second.x, second.y);
  ctx.stroke();
  ctx.restore();
}

function drawThumbnail(image, x, y, size) {
  const thumbnailSize = Math.max(13, Math.min(26, size * 1.32));
  ctx.save();
  ctx.beginPath();
  ctx.rect(x - thumbnailSize / 2, y - thumbnailSize / 2, thumbnailSize, thumbnailSize);
  ctx.clip();
  ctx.drawImage(image, x - thumbnailSize / 2, y - thumbnailSize / 2, thumbnailSize, thumbnailSize);
  ctx.restore();
  ctx.save();
  ctx.strokeStyle = 'rgba(255,255,255,.96)';
  ctx.lineWidth = 1;
  ctx.strokeRect(x - thumbnailSize / 2, y - thumbnailSize / 2, thumbnailSize, thumbnailSize);
  ctx.restore();
}

function drawNode(projected) {
  const { thesis, x, y, depth } = projected;
  const size = nodeRadius(thesis) * (0.8 + depth * 0.35);
  const color = categoryColor(thesis.category);
  const active = thesis.id === state.selected?.id;
  const hovered = thesis.id === state.hovered?.id;
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
  if (image?.complete && image.naturalWidth) drawThumbnail(image, x + size + 6, y - size - 6, size);
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

function draw() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);
  drawOrbitGuides(width, height);
  state.projection = state.theses.map((thesis, index) => ({
    thesis,
    ...project(targetPosition(thesis, index, state.theses.length)),
  }));

  for (let first = 0; first < state.projection.length; first += 1) {
    for (let second = first + 1; second < state.projection.length; second += 1) {
      const one = state.projection[first];
      const two = state.projection[second];
      if (!similarity(one.thesis, two.thesis)) continue;
      const active = Boolean(state.selected && (one.thesis.id === state.selected.id || two.thesis.id === state.selected.id));
      lineBetween(one, two, active);
    }
  }
  [...state.projection].sort((a, b) => a.z - b.z).forEach(drawNode);
}

function loadImages() {
  state.theses.forEach((thesis) => {
    if (!thesis.image_url || state.images.has(thesis.id)) return;
    const image = new Image();
    image.onload = draw;
    image.onerror = () => state.images.delete(thesis.id);
    image.src = thesis.image_url;
    state.images.set(thesis.id, image);
  });
}

function updateCategoryOptions() {
  const current = controls.category.value;
  const categories = [...new Set(state.theses.map((thesis) => thesis.category))].sort();
  controls.category.innerHTML = '<option value="">All categories</option>' + categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`).join('');
  controls.category.value = categories.includes(current) ? current : '';
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}

function queryParams() {
  const params = new URLSearchParams();
  const fields = [
    ['q', controls.search.value], ['category', controls.category.value], ['year', controls.year.value],
    ['page_min', controls.pageMin.value], ['page_max', controls.pageMax.value],
    ['word_min', controls.wordMin.value], ['word_max', controls.wordMax.value],
  ];
  fields.forEach(([key, value]) => { if (value.trim()) params.set(key, value.trim()); });
  return params;
}

async function fetchTheses() {
  const response = await fetch(`/api/theses?${queryParams()}`);
  if (!response.ok) throw new Error('Could not load the thesis database.');
  const data = await response.json();
  state.theses = data.theses;
  if (state.selected && !state.theses.some((thesis) => thesis.id === state.selected.id)) closeDetail();
  updateCategoryOptions();
  loadImages();
  document.querySelector('#recordCount').textContent = `${state.theses.length} thesis nodes currently visible.`;
  draw();
}

function displayDetail(thesis) {
  state.selected = thesis;
  document.querySelector('#detailCategory').textContent = thesis.category || 'UNCATEGORIZED';
  document.querySelector('#detailTitle').textContent = thesis.title;
  document.querySelector('#detailByline').textContent = [thesis.author, thesis.year].filter(Boolean).join(' · ') || 'Author and year unavailable';
  document.querySelector('#detailPages').textContent = displayNumber(thesis.page_count);
  document.querySelector('#detailWords').textContent = displayNumber(thesis.word_count);
  document.querySelector('#detailYear').textContent = thesis.year || '—';
  document.querySelector('#detailSummary').textContent = thesis.ai_summary || thesis.source_abstract || 'No summary has been added yet.';
  document.querySelector('#detailKeywords').textContent = thesis.keywords || 'No keywords available.';
  const image = document.querySelector('#detailImage');
  image.src = thesis.image_url || '';
  image.alt = thesis.image_url ? `Representative image for ${thesis.title}` : '';
  const source = document.querySelector('#sourceLink');
  source.href = thesis.source_url || '#';
  source.hidden = !thesis.source_url;
  detailPanel.classList.add('open');
  draw();
}

function closeDetail() {
  state.selected = null;
  detailPanel.classList.remove('open');
  draw();
}

function showTooltip(thesis, event) {
  tooltip.textContent = `${thesis.title} · ${thesis.category}`;
  tooltip.style.left = `${event.clientX}px`;
  tooltip.style.top = `${event.clientY}px`;
  tooltip.classList.add('visible');
}

function hideTooltip() {
  tooltip.classList.remove('visible');
}

function hitTest(clientX, clientY) {
  const bounds = canvas.getBoundingClientRect();
  const x = clientX - bounds.left;
  const y = clientY - bounds.top;
  return [...state.projection].sort((a, b) => b.z - a.z).find((item) => {
    const radius = Math.max(12, nodeRadius(item.thesis) + 11);
    return Math.hypot(item.x - x, item.y - y) <= radius;
  })?.thesis || null;
}

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
  await fetchTheses();
  displayDetail(state.theses.find((thesis) => thesis.id === result.id));
}

async function deleteSelected() {
  if (!state.selected || !confirm(`Delete “${state.selected.title}”?`)) return;
  const response = await fetch(`/api/theses/${state.selected.id}`, { method: 'DELETE' });
  if (!response.ok) return alert('The thesis could not be deleted.');
  closeDetail();
  await fetchTheses();
}

let filterTimer;
function scheduleLoad() {
  clearTimeout(filterTimer);
  filterTimer = setTimeout(() => fetchTheses().catch((error) => console.error(error)), 220);
}

controls.search.addEventListener('input', scheduleLoad);
[controls.category, controls.year, controls.pageMin, controls.pageMax, controls.wordMin, controls.wordMax].forEach((input) => input.addEventListener('input', scheduleLoad));
controls.layout.addEventListener('change', draw);
controls.size.addEventListener('change', draw);
document.querySelector('#resetFilters').addEventListener('click', () => {
  Object.values(controls).forEach((control) => { if (control !== controls.layout && control !== controls.size) control.value = ''; });
  fetchTheses().catch(console.error);
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
  const thesis = hitTest(event.clientX, event.clientY);
  if (state.dragging) {
    const changeX = event.clientX - state.pointer.lastX;
    const changeY = event.clientY - state.pointer.lastY;
    state.dragDistance += Math.abs(changeX) + Math.abs(changeY);
    state.yaw += changeX * 0.008;
    state.pitch = Math.max(-1.15, Math.min(1.15, state.pitch + changeY * 0.006));
    state.pointer.lastX = event.clientX;
    state.pointer.lastY = event.clientY;
    hideTooltip();
    draw();
    return;
  }
  state.hovered = thesis;
  canvas.style.cursor = thesis ? 'pointer' : 'grab';
  if (thesis) showTooltip(thesis, event); else hideTooltip();
  draw();
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
canvas.addEventListener('pointerleave', () => { state.hovered = null; hideTooltip(); draw(); });
canvas.addEventListener('wheel', (event) => {
  event.preventDefault();
  state.zoom = Math.max(0.48, Math.min(2.2, state.zoom - event.deltaY * 0.0008));
  draw();
}, { passive: false });
window.addEventListener('resize', resizeCanvas);

resizeCanvas();
fetchTheses().catch((error) => {
  document.querySelector('#recordCount').textContent = error.message;
  console.error(error);
});
