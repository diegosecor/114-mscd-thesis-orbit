// Exercise the real renderer's cache boundaries with a deterministic canvas stand-in.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../static/app.js', import.meta.url), 'utf8');

test('hover reuses every connection, while camera/style/selection changes rebuild', () => {
  let lines = 0;
  let projections = 0;
  const context = { clearRect() {}, drawImage() {}, setTransform() {} };
  const state = { theses: [{ id: 1 }, { id: 2 }], positions: new Map([[1, {}], [2, {}]]),
    relations: [{ a: 1, b: 2, lanes: [{ type: 'category', solid: false }] }],
    semanticNeighbors: [], lineScales: { category: 1, semantic: 1 }, yaw: 0, pitch: 0, zoom: 1 };
  const sandbox = vm.createContext({ state, canvas: { clientWidth: 1200, clientHeight: 800, width: 1200, height: 800 },
    ctx: context, window: { devicePixelRatio: 1 }, document: { createElement: () => ({ getContext: () => context }) },
    connectionControls: { category: { checked: true }, semantic: { checked: true } },
    viewport: () => ({}), project: () => { projections++; return { x: 1, y: 1, z: 1 }; },
    relatedThesisIds: () => new Set(), drawOrbitGuides() {}, lineBetween: () => lines++,
    drawNode() {}, drawAdvisorLabels() {}, drawConstellationLabels() {} });
  vm.runInContext(source.slice(source.indexOf('let sceneSignature ='), source.indexOf('/** Combine enabled semantic')), sandbox);
  sandbox.draw();
  assert.equal(lines, 1);
  for (let index = 0; index < 100; index++) { state.hovered = state.theses[index % 2]; sandbox.draw(); }
  assert.equal(lines, 1);
  assert.equal(projections, 2);
  state.yaw = .2; sandbox.draw(); assert.equal(lines, 2);
  state.lineScales.category = .5; sandbox.draw(); assert.equal(lines, 3);
  state.selected = state.theses[0]; sandbox.draw(); assert.equal(lines, 4);
  state.semanticNeighbors = [{ id: 2, similarity: .7 }]; sandbox.draw(); assert.equal(lines, 6);
  sandbox.connectionControls.category.checked = false; sandbox.draw(); assert.equal(lines, 7);
  state.lineColors = { semantic: '#112233' }; sandbox.draw(); assert.equal(lines, 8);
  state.lineColors.semantic = '#445566'; sandbox.draw(); assert.equal(lines, 9);
});

test('thumbnail artwork is prepared once per appearance, not per frame', () => {
  let paints = 0;
  const ctx = { save() {}, restore() {}, measureText: () => ({ width: 70 }), drawImage() {} };
  const sandbox = vm.createContext({ ctx, window: { devicePixelRatio: 1 },
    document: { createElement: () => ({ getContext: () => ({ setTransform() {} }) }) },
    displayNumber: String, paintThumbnail: () => paints++ });
  vm.runInContext(source.slice(source.indexOf('const thumbnailSprites ='), source.indexOf('/** Draw the category-colored')), sandbox);
  const thesis = { id: 1, image_url: '/one.jpg', word_count: 1000, page_count: 40 };
  const image = { complete: true, naturalWidth: 1000 };
  for (let index = 0; index < 100; index++) sandbox.drawThumbnail(image, index, 0, thesis, 48, false);
  assert.equal(paints, 1);
  sandbox.drawThumbnail(image, 0, 0, thesis, 48, true); assert.equal(paints, 2);
  thesis.page_count = 50;
  sandbox.drawThumbnail(image, 0, 0, thesis, 48, true); assert.equal(paints, 3);
  sandbox.window.devicePixelRatio = 2;
  sandbox.drawThumbnail(image, 0, 0, thesis, 48, true); assert.equal(paints, 4);
});

test('a burst of redraw requests schedules only one animation frame', () => {
  const queued = [];
  let draws = 0;
  const sandbox = vm.createContext({ requestAnimationFrame: (callback) => { queued.push(callback); return queued.length; }, draw: () => draws++ });
  vm.runInContext(source.slice(source.indexOf('let drawFrame;'), source.indexOf('/** Cache source figures')), sandbox);
  for (let index = 0; index < 100; index++) sandbox.requestDraw();
  assert.equal(queued.length, 1);
  queued[0]();
  assert.equal(draws, 1);
  sandbox.requestDraw(); assert.equal(queued.length, 2);
});
