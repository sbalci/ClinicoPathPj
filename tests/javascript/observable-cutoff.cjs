// Run with NODE_PATH pointing to a temporary jsdom@26.1.0 installation.
// Real pinned Plot/Inputs/htl/D3 bundles execute in the DOM; no network resources are enabled.
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM,VirtualConsole}=require('jsdom');
const errors=[];
const virtualConsole=new VirtualConsole();virtualConsole.on('jsdomError',e=>errors.push(e));
const html=fs.readFileSync(process.argv[2],'utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,virtualConsole,beforeParse(w){
// jsdom 26's HTMLFormElement proxy rejects own accessor setters (unlike Chromium).
// Put those same per-form accessors on a private prototype for this DOM harness.
const define=w.Object.defineProperty;
w.Object.defineProperty=function(target,key,descriptor){
 if(target instanceof w.HTMLFormElement&&descriptor.get){
  const proto=w.Object.create(w.Object.getPrototypeOf(target));
  define(proto,key,descriptor);w.Object.setPrototypeOf(target,proto);return target;
 }
 return define(target,key,descriptor);
};
}});
const {window:w}=dom,root=w.document.querySelector('.cpj-observable');
const input=(node,type='input')=>node.dispatchEvent(new w.Event(type,{bubbles:true}));
const button=name=>[...root.querySelectorAll('button')].find(b=>b.textContent===name);
assert.equal(errors.length,0,errors.map(e=>e.stack).join('\n'));
assert.match(root.querySelector('.status').textContent,/TP 3 · FP 2 · FN 0 · TN 1/);
assert.equal(root.querySelectorAll('.plots svg').length,2);
// Fixed-size snapshots must not clip rows under jamovi's table padding.
assert.equal(root.querySelector('.snapshot-counts form').style.maxHeight,'');
assert.equal(root.querySelector('.snapshot-metrics form').style.maxHeight,'');
assert.equal(root.querySelectorAll('.snapshot-metrics tbody tr').length,5);
assert.ok(root.querySelector('.dots [role="slider"]'));
const number=root.querySelector('.cutoff input[type="number"]');
number.value='4';input(number);
assert.match(root.querySelector('.status').textContent,/Preview only/);
assert.match(root.querySelector('.status').textContent,/TP 2 · FP 1 · FN 1 · TN 2/);
assert.match(root.querySelector('.applied-label').textContent,/≥ 2/);
button('Apply to HTML tables').click();
assert.match(root.querySelector('.applied-label').textContent,/≥ 4/);
assert.match(root.querySelector('.status').textContent,/Applied HTML snapshot/);
const search=root.querySelector('.search input');search.value='3';input(search);
assert.match(root.querySelector('.row-count').textContent,/1 of 6/);
const check=root.querySelector('.row-table tbody input[type="checkbox"]');
assert.ok(check);check.click();
assert.ok(root.querySelector('.dots circle[stroke="currentColor"]'));
assert.match(root.querySelector('.status').textContent,/TP 2 · FP 1 · FN 1 · TN 2/);
const direction=root.querySelector('.direction select');direction.value='1';input(direction);
assert.match(root.querySelector('.status').textContent,/TP 1 · FP 3 · FN 2 · TN 0/);
button('Reset explorer').click();
assert.match(root.querySelector('.row-count').textContent,/6 of 6/);
assert.match(root.querySelector('.status').textContent,/TP 3 · FP 2 · FN 0 · TN 1/);
const handle=root.querySelector('.dots [role="slider"]');
handle.dispatchEvent(new w.KeyboardEvent('keydown',{key:'End',bubbles:true}));
assert.match(root.querySelector('.status').textContent,/TP 0 · FP 0 · FN 3 · TN 3/);
assert.equal(errors.length,0,errors.map(e=>e.stack).join('\n'));
w.close();console.log('Observable DOM checks passed: inputs, linked rendering, snapshot, row search/selection, direction, reset, keyboard.');
