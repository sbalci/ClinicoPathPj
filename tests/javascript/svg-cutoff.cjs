// Uses only local files in jsdom; native coordinate conversion is separately GUI-tested.
const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const markup=fs.readFileSync(process.argv[2],'utf8');
const dom=new JSDOM('',{runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;
(async()=>{
w.eval(fs.readFileSync('inst/js/pysvgcutoff.js','utf8'));
// Match native jamovi: asset first, then result insertion into an already loaded document.
w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
w.document.body.innerHTML=markup;
await new Promise(resolve=>setTimeout(resolve,0));
const root=w.document.querySelector('.cpj-svg-cutoff'),svg=root;
assert.equal(root.dataset.ready,'true');
const input=root.querySelector('.cutoff-input'),preview=svg.querySelector('.preview'),snapshot=svg.querySelector('.snapshot');
assert.match(preview.textContent,/TP 3 · FP 2 · FN 0 · TN 1/);
input.textContent='3';input.dispatchEvent(new w.Event('input'));
assert.match(preview.textContent,/TP 2 · FP 1 · FN 1 · TN 2/);
assert.match(snapshot.textContent,/cutoff 2/);
assert.match(svg.querySelector('.native-rule').textContent,/≥ 2/);
root.querySelector('.apply').dispatchEvent(new w.MouseEvent('click',{bubbles:true}));assert.match(snapshot.textContent,/cutoff 3/);
assert.ok(Math.abs(Number(svg.querySelector('.operating').getAttribute('cx'))-(535+400/3))<1e-10);
const handle=svg.querySelector('.handle');
svg.createSVGPoint=()=>({x:0,y:0,matrixTransform(){return {x:this.x,y:this.y};}});
svg.getScreenCTM=()=>({inverse:()=>({})});
handle.dispatchEvent(new w.MouseEvent('pointerdown',{clientX:200,clientY:300,bubbles:true}));
w.dispatchEvent(new w.MouseEvent('pointermove',{clientX:200,clientY:545,bubbles:true}));
assert.match(preview.textContent,/TP 3 · FP 3 · FN 0 · TN 0/);
w.dispatchEvent(new w.MouseEvent('pointerup',{bubbles:true}));
const stopped=preview.textContent;
w.dispatchEvent(new w.MouseEvent('pointermove',{clientX:200,clientY:205,bubbles:true}));
assert.equal(preview.textContent,stopped);

handle.dispatchEvent(new w.KeyboardEvent('keydown',{key:'End'}));
assert.match(preview.textContent,/TP 0 · FP 0 · FN 3 · TN 3/);
handle.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Home'}));
assert.match(preview.textContent,/TP 3 · FP 3 · FN 0 · TN 0/);
const dot=[...svg.querySelectorAll('.roc-point')].find(x=>x.getAttribute('aria-label')==='Preview cutoff 2.0');
assert.ok(dot);dot.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Enter'}));
assert.match(preview.textContent,/TP 3 · FP 2 · FN 0 · TN 1/);
root.querySelector('.reset').dispatchEvent(new w.MouseEvent('click',{bubbles:true}));assert.match(snapshot.textContent,/cutoff 2/);
input.textContent='';input.dispatchEvent(new w.Event('input'));
assert.match(root.querySelector('.feedback').textContent,/finite numeric/);
assert.match(preview.textContent,/TP 3 · FP 2 · FN 0 · TN 1/);
// Serialized visible SVG includes the changed drawing and preview label, with no script.
input.textContent='3';input.dispatchEvent(new w.Event('input'));const exported=svg.outerHTML;
assert.match(exported,/Preview cutoff 3: TP 2/);assert.doesNotMatch(exported,/data-payload=/);assert.doesNotMatch(exported,/<script/);
assert.equal(svg.querySelectorAll('.observation').length,6);
w.dispatchEvent(new w.Event('pagehide'));w.close();console.log('SVG DOM passed: input, tied cutoff, lookup, snapshot, native-rule separation, ROC keyboard, reset, endpoints, invalid input, export content.');

})().catch(e=>{console.error(e);process.exitCode=1});
