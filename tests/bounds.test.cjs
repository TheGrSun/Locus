const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../demo/bounds.js'), 'utf8').replace(/^export /gm, '');
const context = {module: {exports: {}}};
vm.runInNewContext(`${source}\nmodule.exports = { finiteBounds, viewSpan };`, context);
const {finiteBounds, viewSpan} = context.module.exports;

function pair(values) {
  return [values[0], values[1]];
}

test('an empty axis falls back instead of producing Infinity', () => {
  assert.deepEqual(pair(finiteBounds([null, undefined])), [-6, 6]);
  assert.deepEqual(pair(finiteBounds([1, null, 3])), [1, 3]);
  assert.deepEqual(pair(finiteBounds([2, 2])), [1, 3]);
});

test('a singular surface is kept inside the x y window', () => {
  const samples = [];
  for (let index = 0; index < 80; index += 1) samples.push(Math.sin(index / 8));
  samples.push(-500, 800, 1200);
  const [low, high] = pair(viewSpan(samples, 10));
  assert.ok(high - low < 24, `${low} ${high}`);
  assert.ok(low > -12 && high < 12);
});
