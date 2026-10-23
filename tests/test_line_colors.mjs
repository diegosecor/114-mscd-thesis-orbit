// Per-type color choices must preserve the untouched source palette.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';
import { defaultLineColors, connectionColor } from '../static/line-colors.mjs';

test('default colors retain dynamic category/year source colors', () => {
  const colors = defaultLineColors();
  assert.equal(connectionColor({ type: 'category', color: '#a18b27' }, colors), '#a18b27');
  assert.equal(connectionColor({ type: 'year', color: 'hsl(210 62% 48%)' }, colors), 'hsl(210 62% 48%)');
});

test('a custom color applies only to the selected relationship type', () => {
  const colors = defaultLineColors();
  colors.year = '#112233';
  assert.equal(connectionColor({ type: 'year', color: '#219fb3' }, colors), '#112233');
  assert.equal(connectionColor({ type: 'semantic', color: '#7d25ff' }, colors), '#7d25ff');
  assert.equal(defaultLineColors().year, null);
});

test('reset restores every source color and legend without changing widths', () => {
  const source = readFileSync(new URL('../static/app.js', import.meta.url), 'utf8');
  const labels = {};
  const removed = [];
  const state = { lineColors: { year: '#112233', category: '#445566' }, lineScales: { year: 1.5 } };
  const context = vm.createContext({ state, defaultLineColors, updateLineWidthEditor() {}, requestDraw() {},
    document: { documentElement: { style: { removeProperty: (name) => removed.push(name) } },
      querySelector: (selector) => labels[selector] ||= {} } });
  const start = source.indexOf('function resetLineColors()');
  vm.runInContext(source.slice(start, source.indexOf("document.querySelector('#resetFilters')", start)), context);
  context.resetLineColors();
  assert.deepEqual(state.lineColors, defaultLineColors());
  assert.equal(removed.length, 5);
  assert.equal(labels['[data-legend-color="year"]'].textContent, 'Blue / teal');
  assert.equal(labels['[data-legend-color="category"]'].textContent, 'Category color');
  assert.equal(state.lineScales.year, 1.5);
});
