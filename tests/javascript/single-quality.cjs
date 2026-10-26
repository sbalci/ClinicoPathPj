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
const {window:w}=dom,root=w.document.querySelector('[id^=cpjqc]');
const input=(node,type='input')=>node.dispatchEvent(new w.Event(type,{bubbles:true}));
const button=name=>[...root.querySelectorAll('button')].find(b=>b.textContent===name);
assert.equal(errors.length,0,errors.map(e=>e.detail?.stack||e.stack).join('\n'));
assert.match(root.querySelector('.count').textContent,/12 matching/);
const filter=root.querySelector('.filter select');filter.value='2';input(filter);
assert.match(root.querySelector('.count').textContent,/1 matching/);
assert.match(root.querySelector('.rows').textContent,/37/);
assert.match(root.querySelector('.rows').textContent,/Flagged/);
filter.value='1';input(filter);
assert.match(root.querySelector('.rows').textContent,/40/);
filter.value='0';input(filter);
const search=root.querySelector('.search input');search.value='37';input(search);
assert.match(root.querySelector('.count').textContent,/1 matching/);
assert.match(root.querySelector('.scope').textContent,/12 input rows/);
assert.equal(errors.length,0,errors.map(e=>e.detail?.stack||e.stack).join('\n'));
w.close();console.log('Single-quality DOM checks passed: status filter, original-row search, missing rows and unchanged scope.');
