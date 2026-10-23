// Exact metadata relationships only. Semantic scores are supplied by the Python API.
export const CATEGORY_COLORS = {
  'AI + Generative Design': '#7d25ff',
  'Creative Media': '#df439d',
  'Data + Built Environment': '#3279d8',
  'Embodied Systems + Wearables': '#db793e',
  'Interaction + Experience': '#11947e',
  'Robotics + Fabrication': '#a18b27',
  'XR + Immersion': '#8b62c8',
  'Computational Design': '#697d9c',
  'Uncategorized': '#92909a',
};

// Stable hashing keeps fallback colors/layout seeds consistent across filters.
export function hash(value) {
  let result = 0;
  for (const character of String(value)) result = (result * 31 + character.charCodeAt(0)) | 0;
  return Math.abs(result);
}

// Curated colors are fixed; unknown categories get a deterministic fallback hue.
export function categoryColor(category) {
  return CATEGORY_COLORS[category] || `hsl(${hash(category) % 360} 58% 48%)`;
}

// The same posting year always has the same color regardless of visible records.
export function yearColor(year) {
  return `hsl(${175 + ((Number(year) * 17) % 65)} 62% 48%)`;
}

const genericKeywords = new Set([
  'design', 'computational design', 'architecture', 'architectural design',
  'mscd', 'thesis', 'master of science', 'master of science in computational design',
  'master of computational design', 'carnegie mellon university', 'cmu',
  'architecture not elsewhere classified', 'digital and interaction design',
  'built environment and design not elsewhere classified', 'design not elsewhere classified',
  'architectural science and technology (incl. acoustics, lighting, structure and ecologically sustainable design)',
]);
const aliases = {
  'ar': 'augmented reality', 'vr': 'virtual reality', 'ai': 'artificial intelligence',
  'ml': 'machine learning', 'hci': 'human computer interaction',
  'llm': 'large language models', 'large language model': 'large language models',
  'robot': 'robotics', 'robots': 'robotics', 'robotic': 'robotics',
  '3 d printing': '3d printing',
};

export function keywordSet(value = '') {
  // Subject names may contain commas inside parentheses. Keep those intact.
  const parts = [];
  let depth = 0;
  let start = 0;
  for (let index = 0; index < value.length; index += 1) {
    if (value[index] === '(') depth += 1;
    if (value[index] === ')') depth = Math.max(0, depth - 1);
    if ((value[index] === ',' || value[index] === ';') && depth === 0) {
      parts.push(value.slice(start, index));
      start = index + 1;
    }
  }
  parts.push(value.slice(start));
  return new Set(parts.map((word) => {
    const normalized = word.toLowerCase().replace(/[-_]/g, ' ').replace(/\s+/g, ' ').trim();
    return aliases[normalized] || normalized;
  }).filter((word) => word && !genericKeywords.has(word)));
}

// Separate lanes retain the reason for every connection. No distance-based or
// invented semantic links: these are editable catalogue categories and keywords.
export function buildRelations(theses) {
  const keywords = new Map(theses.map((thesis) => [thesis.id, keywordSet(thesis.keywords)]));
  const relations = [];
  for (let i = 0; i < theses.length; i += 1) {
    for (let j = i + 1; j < theses.length; j += 1) {
      const a = theses[i];
      const b = theses[j];
      const shared = [...keywords.get(a.id)].filter((word) => keywords.get(b.id).has(word));
      const sameCategory = a.category && a.category === b.category && a.category !== 'Uncategorized';
      const sameYear = a.year != null && a.year !== '' && b.year != null && b.year !== ''
        && Number(a.year) === Number(b.year);
      const lanes = [];
      if (sameCategory) lanes.push({
        type: 'category', color: categoryColor(a.category), solid: shared.length > 0,
        label: a.category,
      });
      if (sameYear) lanes.push({
        type: 'year', color: yearColor(a.year), solid: false, label: `Posted in ${a.year}`,
      });
      if (shared.length) lanes.push({
        type: 'keywords', color: '#d84b9b', solid: true, label: shared.join(', '),
      });
      const sharedAdvisors = (a.advisor_names || []).filter((name) => (b.advisor_names || []).includes(name));
      if (sharedAdvisors.length) lanes.push({
        type: 'advisor', color: '#5b7892', solid: false, label: sharedAdvisors.join(', '),
      });
      if (lanes.length) relations.push({ a: a.id, b: b.id, lanes });
    }
  }
  return relations;
}
