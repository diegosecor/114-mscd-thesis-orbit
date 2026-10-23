// Width preferences must not change semantic ranking or other connection types.
import test from 'node:test';
import assert from 'node:assert/strict';
import { defaultLineScales, connectionWidth, connectionPattern } from '../static/line-widths.mjs';

test('years use dash-dot while category/advisor links retain dots and solid links stay solid', () => {
  assert.deepEqual(connectionPattern({ type: 'year', solid: false }, false), [8, 3, 2, 3]);
  assert.deepEqual(connectionPattern({ type: 'category', solid: false }, false), [2, 4.5]);
  assert.deepEqual(connectionPattern({ type: 'advisor', solid: false }, true), [2, 3]);
  assert.deepEqual(connectionPattern({ type: 'keywords', solid: true }, true), []);
});

test('defaults retain the previous dotted and solid widths', () => {
  assert.ok(Math.abs(connectionWidth({ type: 'year', solid: false }, false, false) - 1.12) < 1e-10);
  assert.equal(connectionWidth({ type: 'keywords', solid: true }, true, false), 4.2);
  assert.ok(Math.abs(connectionWidth({ type: 'category', solid: false }, true, true) - 1.04) < 1e-10);
});

test('scaling one type leaves other types unchanged; reset returns fresh defaults', () => {
  const scales = defaultLineScales();
  scales.year = 1.5;
  const lane = { type: 'year', solid: false };
  assert.equal(connectionWidth(lane, false, false, scales.year), connectionWidth(lane, false, false) * 1.5);
  assert.equal(scales.category, 1);
  assert.deepEqual(defaultLineScales(), { semantic: 1, advisor: 1, category: 1, year: 1, keywords: 1 });
});

test('semantic scaling preserves stronger/weaker differences', () => {
  const weak = { type: 'semantic', solid: true, similarity: .35 };
  const strong = { ...weak, similarity: .8 };
  assert.ok(connectionWidth(strong, true, true, .25) > connectionWidth(weak, true, true, .25));
  assert.equal(connectionWidth(strong, true, true, 2), connectionWidth(strong, true, true) * 2);
});
