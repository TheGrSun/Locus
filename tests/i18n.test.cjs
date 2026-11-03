const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../demo/i18n.js'), 'utf8').replace(/^export /gm, '');
const context = {module: {exports: {}}};
vm.runInNewContext(`${source}\nmodule.exports = { LANGS, SYMBOL_ROWS, translate, translateError };`, context);
const {LANGS, SYMBOL_ROWS, translate, translateError} = context.module.exports;

test('the demo defaults to English and offers the requested languages', () => {
  assert.equal(LANGS[0][0], 'en');
  assert.equal(LANGS.map(([id]) => id).join(','), 'en,zh-CN,zh-TW,ja,ko,de,fr,es,ru');
  assert.equal(translate('en', 'surface'), '3D surface');
  assert.equal(translate('zh-TW', 'surface'), '三維曲面');
  assert.equal(translate('ru', 'hint').includes('Тяните'), true);
});

test('symbol buttons insert calculator text and server errors follow the language', () => {
  assert.equal(SYMBOL_ROWS.flat().find(([label]) => label === 'π')[1], 'π');
  assert.equal(translateError('fr', '请输入至少一条公式。'), 'Saisissez au moins une formule.');
  assert.equal(translateError('de', 'speed 必须是有限数字。'), 'speed muss eine endliche Zahl sein.');
});
