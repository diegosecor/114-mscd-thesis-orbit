// Expanded zoom must pass the old limit without affecting orbit framing.
import test from 'node:test';
import assert from 'node:assert/strict';
import { wheelZoom } from '../static/zoom.mjs';

test('zoom continues beyond the previous 2.2x limit', () => {
  assert.ok(wheelZoom(2.2, -100) > 2.2);
  assert.ok(wheelZoom(6, -100) > 6);
});

test('zoom is bounded and remains reversible away from its limits', () => {
  let zoom = 1;
  for (let i = 0; i < 100; i++) zoom = wheelZoom(zoom, -200);
  assert.equal(zoom, 8);
  for (let i = 0; i < 100; i++) zoom = wheelZoom(zoom, 200);
  assert.equal(zoom, .25);
  assert.ok(Math.abs(wheelZoom(wheelZoom(1, -80), 80) - 1) < 1e-10);
});

test('wheel unit modes are normalized and zero movement preserves scale', () => {
  assert.equal(wheelZoom(1, -1, 1), wheelZoom(1, -16));
  assert.equal(wheelZoom(1, -.1, 2, 800), wheelZoom(1, -80));
  assert.equal(wheelZoom(3, 0), 3);
});
