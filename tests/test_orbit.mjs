// Exercise the real viewport functions in isolation: no DOM, server, or rendering required.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

test('orbiting keeps framing and user zoom fixed', () => {
  const source = readFileSync(new URL('../static/app.js', import.meta.url), 'utf8');
  const functions = source.slice(source.indexOf('function refreshGeometry()'), source.indexOf('function project('));
  const state = { theses: [{ id: 1 }, { id: 2 }], yaw: 0, pitch: 0, zoom: 1.2 };
  const context = vm.createContext({ state, canvas: { clientWidth: 1440, clientHeight: 900 },
    targetPosition: (_, index) => ({ x: index ? 330 : -300, y: 90, z: 120 }), draw() {}, updateConstellationSummary() {} });
  vm.runInContext(functions, context);
  context.refreshGeometry();
  const initialFit = context.viewport().fit;
  const initialView = JSON.stringify(context.viewport());
  state.selected = state.theses[0];
  assert.equal(JSON.stringify(context.viewport()), initialView);
  state.selected = state.theses[1];
  assert.equal(JSON.stringify(context.viewport()), initialView);
  state.selected = null;
  assert.equal(JSON.stringify(context.viewport()), initialView);
  for (let step = 0; step < 24; step++) {
    state.yaw = step * Math.PI / 12;
    state.pitch = step * Math.PI / 24;
    assert.equal(context.viewport().fit, initialFit);
    assert.equal(state.zoom, 1.2);
  }
});
