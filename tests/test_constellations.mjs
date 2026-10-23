// Test layout summaries independently of canvas rendering and network requests.
import test from 'node:test';
import assert from 'node:assert/strict';
import { visibleConstellations, medianMetric, constellationCenter } from '../static/constellations.mjs';

test('filters retain full-corpus group identity and totals', () => {
  const data = { groups: [{ id: '0', ids: ['1', '2'], count: 2 }, { id: '1', ids: ['3'], count: 1 }] };
  const groups = visibleConstellations(data, [{ id: 2 }, { id: 3 }]);
  assert.equal(groups[0].count, 2);
  assert.equal(groups[0].members.length, 1);
  assert.equal(groups[1].index, 1);
  assert.deepEqual(visibleConstellations(null, []), []);
});

test('median excludes missing counts, supports odd/even counts', () => {
  const rows = [null, 0, '', undefined, 10, 30].map((page_count) => ({ page_count }));
  assert.equal(medianMetric(rows, 'page_count'), 20);
  assert.equal(medianMetric([...rows, { page_count: 60 }], 'page_count'), 30);
  assert.equal(medianMetric([{ page_count: null }], 'page_count'), null);
});

test('group centers remain finite for small collections', () => {
  for (const count of [1, 2, 7]) {
    for (let index = 0; index < count; index++) assert.ok(Object.values(constellationCenter(index, count)).every(Number.isFinite));
  }
});
