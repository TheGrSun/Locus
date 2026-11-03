// In-memory DOM and SDK double: no browser, network, or real key.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function page({failLoad = false, dimension = '2d'} = {}) {
  const elements = new Map(), downloads = [], blobs = [], scripts = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      textContent: '', value: '', disabled: false, hidden: id === 'workspace', handlers: {},
      classList: {toggle() {}}, addEventListener(name, handler) {this.handlers[name] = handler;},
      click() {if (this.onclick) this.onclick();},
    });
    return elements.get(id);
  };
  let state = {expressions: {list: []}};
  const calculator = () => ({
    setExpressions(list) {state.expressions.list = list;}, setMathBounds(bounds) {state.bounds = bounds;},
    getState() {return JSON.parse(JSON.stringify(state));},
    setState(value) {state = JSON.parse(JSON.stringify(value));},
    screenshot() {return 'data:image/png;base64,test';}, destroy() {},
  });
  const sdk = {
    GraphingCalculator() {state.kind = '2d'; return calculator();},
    Calculator3D() {state.kind = '3d'; return calculator();},
  };
  const context = {
    window: {}, Blob, console, encodeURIComponent,
    setTimeout: () => 1, clearTimeout() {},
    URL: {createObjectURL(blob) {blobs.push(blob); return 'blob:test';}, revokeObjectURL() {}},
    document: {
      documentElement: {}, title: '', getElementById: element,
      createElement() {return {remove() {}, click() {downloads.push({url: this.href, name: this.download});}};},
      head: {append(script) {
        scripts.push(script.src);
        if (failLoad) script.onerror();
        else {context.Desmos = sdk; context.window.Desmos = sdk; script.onload();}
      }},
    },
  };
  const template = fs.readFileSync(path.join(__dirname, '../src/locus/graph.html'), 'utf8');
  const code = template.match(/<script>([\s\S]*?)<\/script>/)[1].replace('__GRAPH_DATA__', JSON.stringify({
    expressions: ['a=1', 'y=ax^2'], title: 'Test', xRange: [-6, 6], yRange: [-4, 8], language: 'zh-CN', dimension,
    officialDemos: { '2d': 'https://example.com/2d', '3d': 'https://example.com/3d' },
  }));
  vm.runInNewContext(code, context);
  const connect = async () => {
    element('api-key').value = 'test-key';
    await element('connect').handlers.submit({preventDefault() {}});
  };
  return {element, downloads, blobs, scripts, connect, state: () => state};
}

test('connect, export, import, and reset with a simulated Desmos SDK', async () => {
  const p = page();
  assert.equal(p.element('workspace').hidden, true);
  await p.connect();
  assert.equal(p.element('workspace').hidden, false);
  assert.equal(p.element('setup').hidden, true);
  assert.equal(p.element('api-key').value, '');
  assert.match(p.scripts[0], /apiKey=test-key$/);
  assert.equal(p.state().expressions.list.length, 2);
  p.element('save').onclick();
  assert.equal(p.downloads[0].name, 'desmos-state.json');
  assert.doesNotMatch(await p.blobs[0].text(), /test-key/);
  p.element('png').onclick();
  assert.equal(p.downloads[1].name, 'desmos-graph.png');
  const fileInput = {value: 'file', files: [{size: 50, text: async () => '{"expressions":{"list":[{"id":"new","latex":"y=x"}]}}'}]};
  await p.element('state-file').onchange({target: fileInput});
  assert.equal(p.state().expressions.list[0].latex, 'y=x');
  assert.equal(fileInput.value, '');
  p.element('reset').onclick();
  assert.equal(p.state().expressions.list[0].latex, 'a=1');
});

test('3d page uses Calculator3D and does not apply 2d bounds', async () => {
  const p = page({dimension: '3d'});
  assert.match(p.element('mode').textContent, /3D · Calculator3D/);
  await p.connect();
  assert.equal(p.state().kind, '3d');
  assert.equal(p.state().bounds, undefined);
  assert.equal(p.element('open-demo').textContent, '打开官方 3D 示例（不需要 key）');
  assert.equal(p.element('open-demo').href, 'https://example.com/3d');
  assert.equal(p.element('workspace').hidden, false);
});

test('template names both constructors and does not point at the missing v1.11 demo', () => {
  const template = fs.readFileSync(path.join(__dirname, '../src/locus/graph.html'), 'utf8');
  assert.match(template, /__DEMO_2D__/);
  assert.match(template, /__DEMO_3D__/);
  assert.match(template, /Calculator3D/);
  assert.doesNotMatch(template, /api\/v1\.11/);
});

test('load errors return an actionable message and allow retry', async () => {
  const p = page({failLoad: true});
  await p.connect();
  assert.equal(p.element('load').disabled, false);
  assert.equal(p.element('workspace').hidden, true);
  assert.match(p.element('status').textContent, /无法加载/);
});

test('invalid state input leaves the current graph unchanged', async () => {
  const p = page();
  await p.connect();
  for (const file of [{size: 10, text: async () => '{bad'}, {size: 3 * 1024 * 1024}]) {
    await p.element('state-file').onchange({target: {files: [file], value: 'file'}});
    assert.match(p.element('status').textContent, /导入失败/);
    assert.equal(p.state().expressions.list[0].latex, 'a=1');
  }
});
