// Pure metadata tests protect connection reasons without network/model dependencies.
import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRelations, categoryColor, keywordSet } from '../static/relations.mjs';

test('a pair can show category, year and keyword lanes independently', () => {
  const edges = buildRelations([
    { id: 1, category: 'XR + Immersion', year: 2025, keywords: 'VR, haptics' },
    { id: 2, category: 'XR + Immersion', year: 2025, keywords: 'Virtual Reality, tools' },
  ]);
  assert.equal(edges.length, 1);
  assert.deepEqual(edges[0].lanes.map((lane) => lane.type), ['category', 'year', 'keywords']);
  assert.deepEqual(edges[0].lanes.map((lane) => lane.solid), [true, false, true]);
  assert.equal(edges[0].lanes[2].label, 'virtual reality');
  assert.equal(new Set(edges[0].lanes.map((lane) => lane.color)).size, 3);
});

test('generic tags and missing years do not invent relationships', () => {
  assert.deepEqual(buildRelations([
    { id: 1, category: 'XR + Immersion', year: null, keywords: 'Computational Design, Architecture' },
    { id: 2, category: 'Creative Media', year: null, keywords: 'computational design, architecture' },
  ]), []);
});

test('a category-only relationship is dotted; year-only also works', () => {
  const [categoryEdge] = buildRelations([
    { id: 1, category: 'Creative Media', year: 2020, keywords: 'dance' },
    { id: 2, category: 'Creative Media', year: 2021, keywords: 'sound' },
  ]);
  assert.equal(categoryEdge.lanes.length, 1);
  assert.equal(categoryEdge.lanes[0].solid, false);
  const [yearEdge] = buildRelations([
    { id: 1, category: 'Creative Media', year: 2020 },
    { id: 2, category: 'Robotics + Fabrication', year: '2020' },
  ]);
  assert.equal(yearEdge.lanes[0].type, 'year');
  assert.equal(yearEdge.lanes[0].label, 'Posted in 2020');
});

test('category colors do not depend on filtered membership', () => {
  const category = 'Robotics + Fabrication';
  const full = buildRelations([
    { id: 1, category, keywords: '' },
    { id: 2, category, keywords: '' },
    { id: 3, category: 'Creative Media', keywords: '' },
  ]);
  const filtered = buildRelations([
    { id: 1, category, keywords: '' },
    { id: 2, category, keywords: '' },
  ]);
  assert.equal(full[0].lanes[0].color, filtered[0].lanes[0].color);
  assert.equal(full[0].lanes[0].color, categoryColor(category));
});

test('commas inside repository subjects cannot create spurious keyword matches', () => {
  assert.deepEqual([...keywordSet('BIM, Architectural Science and Technology (incl. Acoustics, Lighting, Structure and Ecologically Sustainable Design)')], ['bim']);
});

test('co-advisor relationships use complete names and preserve their reason', () => {
  const edges = buildRelations([
    { id: 1, advisor_names: ['Ada Example', 'Alan Example'] },
    { id: 2, advisor_names: ['Alan Example'] },
    { id: 3, advisor_names: ['Alan'] },
  ]);
  assert.equal(edges.length, 1);
  assert.equal(edges[0].lanes[0].type, 'advisor');
  assert.equal(edges[0].lanes[0].label, 'Alan Example');
});
