#!/usr/bin/env node
// Exercise generated ROC bindings with the installed jamovi client's actual methods.
// This checks client binding/widget behavior; it does not replace desktop acceptance.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '..');
const assets = process.argv[2] ||
    '/Applications/jamovi.app/Contents/Resources/jamovi/client/dist/assets';
const clients = fs.readdirSync(assets).filter(x => /^analysisui-.*\.js$/.test(x));
assert.equal(clients.length, 1, 'Expected one installed analysis UI bundle');
const client = path.join(assets, clients[0]);
const source = fs.readFileSync(client, 'utf8');

// Fail closed if the installed client's structure changes. Evaluate only class
// definitions in an isolated VM: no bundle startup, browser, network or model fit.
function clientClass(method, ending) {
    const position = source.indexOf(method);
    assert(position >= 0, `Client method not found: ${method}`);
    const start = source.lastIndexOf('=class', position) + 1;
    const end = source.indexOf(ending, position);
    assert(start > 0 && end >= position, 'Unsupported client class structure');
    return source.slice(start, end + ending.length);
}
const binderCode = clientClass('bindActionParams(e,t,n)', 'this._resources={}}}');
// ComboBox's last method precedes the next class declaration in this client.
const comboMethod = source.indexOf('getOptionsProperty(){');
assert(comboMethod >= 0, 'Client ComboBox method not found');
const comboStart = source.lastIndexOf('=class', comboMethod) + 1;
const comboTail = source.indexOf('updateOptionsList(){', comboStart);
const comboEnd = source.indexOf('}},', comboTail);
assert(comboTail >= 0 && comboEnd > comboTail, 'Unsupported ComboBox structure');
const Combo = vm.runInNewContext('(' + source.slice(comboStart, comboEnd + 2) + ')', {
    R: class { onPropertyChanged() {} },
});
const Binder = vm.runInNewContext('(' + binderCode + ')', {
    Mt: x => typeof x === 'object' && !!x && typeof x.bindFunction === 'function',
});
const detectorStart = source.indexOf('isValueDataBound(e){');
const detectorEnd = source.indexOf('getPropertyValue(e){', detectorStart);
assert(detectorStart >= 0 && detectorEnd > detectorStart, 'Client binding detector not found');
const Detector = vm.runInNewContext('(class {' +
    source.slice(detectorStart, detectorEnd) + '})');
const detector = new Detector();
const binder = new Binder({});
const uiPath = process.env.CPJ_ROC_UI || path.join(root, 'jamovi/pyenhancedroc.u.yaml');
const ui = JSON.parse(fs.readFileSync(uiPath, 'utf8').split('\n').slice(1).join('\n'));
const controls = new Map();
function visit(items) {
    for (const item of items || []) {
        if (item.name) controls.set(item.name, item);
        visit(item.children);
    }
}
visit(ui.children);
let stateChecks = 0;
for (let slot = 1; slot <= 3; slot++) {
    const marker = `marker${slot}`;
    const direction = controls.get(`direction${slot}`);
    assert(detector.isValueDataBound(direction.enable), 'Client must recognize a dynamic binding');
    let value = null;
    binder._resources = { [marker]: { value: () => value } };
    const binding = binder._resolveBinding(direction.enable, 0);
    assert.deepEqual(Array.from(binding.sourceNames), [marker]);
    const widget = Object.create(Combo.prototype);
    widget.input = { disabled: false };
    widget.label = null;
    let enabled;
    widget.getPropertyValue = () => enabled;
    widget.setPropertyValue = (name, next) => {
        assert.equal(name, 'enable');
        enabled = next;
        widget.onPropertyChanged(name);
    };
    const action = binder.bindActionParams(widget, 'enable', binding);
    for (const selection of [null, 'Score A', null, 'Score B', null]) {
        value = selection;
        action.execute(binder._resources);
        assert.equal(widget.input.disabled, selection === null, `${marker}: dropdown state`);
        assert.equal(typeof enabled, 'boolean', `${marker}: binding must return boolean`);
        assert.equal(enabled, selection !== null, `${marker}: binding selection state`);
        stateChecks += 3;
    }
}
console.log(JSON.stringify({
    status: 'passed', state_checks: stateChecks, role_bindings: 3, client,
    client_sha256: crypto.createHash('sha256').update(source).digest('hex'),
    scope: 'Actual installed-client binding and ComboBox methods; desktop GUI pending',
}, null, 2));
