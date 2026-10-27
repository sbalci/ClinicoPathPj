const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
function open(path){
 const calls=[],errors=[];
 const dom=new JSDOM(fs.readFileSync(path,'utf8'),{runScripts:'dangerously',beforeParse(w){
  w.addEventListener('error',e=>errors.push(e.message));w.setOption=(...args)=>calls.push(args);
  w.fetch=()=>{throw Error('Rectangle inspection must stay local');};
 }});
 const d=dom.window.document,w=dom.window,svg=d.querySelector('.scatter-view');
 const fields=['xmin','xmax','ymin','ymax'].map(k=>d.querySelector('.brush-'+k));
 const ids=()=>Array.from(d.querySelectorAll('.scatter-view circle[aria-pressed="true"]'),el=>el.dataset.row);
 function bounds(values){values.forEach((v,i)=>{fields[i].value=String(v);});d.querySelector('.brush-preview').click();}
 svg.getBoundingClientRect=()=>({left:100,top:200,width:325,height:200});
 function pointer(type,x,y,id=1,button=0){const e=new w.MouseEvent(type,{clientX:100+x/2,clientY:200+y/2,button,bubbles:true,cancelable:true});Object.defineProperty(e,'pointerId',{value:id});svg.dispatchEvent(e);}
 return {dom,d,w,svg,fields,ids,bounds,pointer,calls,errors};
}
const a=open(process.argv[2]);
assert.deepEqual(a.errors,[]);assert.equal(a.calls.length,0);assert.equal(a.d.querySelector('.brush-mode').checked,false);
a.pointer('pointerdown',70,330);a.pointer('pointerup',620,30);assert.deepEqual(a.ids(),[]);
a.bounds([0,1,0,2]);assert.deepEqual(a.ids(),['2','7']);assert.equal(a.calls.length,0);
a.d.querySelector('.apply-selection').click();assert.equal(a.calls.length,1);assert.deepEqual(JSON.parse(a.calls[0][1]).rows,['2','7']);
assert.match(a.d.querySelector('.brush-status').textContent,/2 source rows/);
for(const invalid of [[2,1,0,2],['',1,0,2],[0,1,3,2],['NaN',1,0,2],['Infinity',1,0,2]]){
 a.bounds(invalid);assert.deepEqual(a.ids(),['2','7']);assert.match(a.d.querySelector('.brush-status').textContent,/finite bounds/);
}
const mode=a.d.querySelector('.brush-mode');mode.checked=true;mode.dispatchEvent(new a.w.Event('change'));
assert.equal(a.svg.style.touchAction,'none');
let captures=0,releases=0;a.svg.setPointerCapture=()=>{captures++;};a.svg.releasePointerCapture=()=>{releases++;};
const p2=a.d.querySelector('circle[data-row="2"]'),p7=a.d.querySelector('circle[data-row="7"]');
const x0=+p2.getAttribute('cx')-1,y0=+p7.getAttribute('cy')-1;
const x1=+p7.getAttribute('cx')+1,y1=+p2.getAttribute('cy')+1;
a.d.querySelector('.clear').click();a.pointer('pointerdown',x1,y1);a.pointer('pointermove',x0,y0);
assert.deepEqual(a.ids(),[]);assert(a.d.querySelector('.brush-box'));
a.pointer('pointerup',x0,y0);assert.deepEqual(a.ids(),['2','7']);assert.equal(captures,1);assert.equal(releases,1);
assert.equal(a.calls.length,1);p2.dispatchEvent(new a.w.MouseEvent('click',{bubbles:true}));assert.deepEqual(a.ids(),['2','7']);
// SVG's screen matrix takes precedence over CSS bounds; preserve exact source identities.
let matrixCalls=0;a.svg.getScreenCTM=()=>({inverse:()=>({})});a.svg.createSVGPoint=()=>({x:0,y:0,matrixTransform(){matrixCalls++;return {x:(this.x-100)*2,y:(this.y-200)*2};}});
a.pointer('pointerdown',x0,y0);a.pointer('pointermove',x1,y1);a.pointer('pointerup',x1,y1);assert.deepEqual(a.ids(),['2','7']);assert(matrixCalls>=3);
// Cancel/escape/foreign pointers never replace the prior preview.
for(const cancel of ['pointercancel','lostpointercapture','escape']){
 a.pointer('pointerdown',70,330);a.pointer('pointermove',620,30);
 if(cancel==='escape')a.svg.dispatchEvent(new a.w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));else a.pointer(cancel,620,30);
 assert.deepEqual(a.ids(),['2','7']);assert.equal(a.d.querySelector('.brush-box'),null);
}
a.pointer('pointerdown',70,330);a.pointer('pointerup',620,30,99);assert.deepEqual(a.ids(),['2','7']);a.pointer('pointercancel',620,30);
a.pointer('pointerdown',70,330);a.pointer('pointerup',71,329);assert.deepEqual(a.ids(),['2','7']);
a.pointer('pointerdown',0,0);a.pointer('pointerup',620,30);assert.deepEqual(a.ids(),['2','7']);
a.pointer('pointerdown',70,330,1,2);a.pointer('pointerup',620,30);assert.deepEqual(a.ids(),['2','7']);
a.pointer('pointerdown',70,330);a.pointer('pointermove',900,-100);a.pointer('pointerup',900,-100);assert.deepEqual(a.ids(),['2','7','4','9']);
delete a.svg.setPointerCapture;delete a.svg.releasePointerCapture;
a.pointer('pointerdown',70,330);a.pointer('pointermove',620,30);a.pointer('pointerleave',620,30);
assert.equal(a.d.querySelector('.brush-box'),null);assert.deepEqual(a.ids(),['2','7','4','9']);
a.bounds([0,1,0,2]);a.d.querySelector('.restore-selection').click();assert.deepEqual(a.ids(),[]);assert.equal(a.d.querySelector('.brush-box'),null);
a.bounds([0,1,0,2]);a.d.querySelector('.tree-branch[data-axis="markers"]').focus();assert.equal(a.d.querySelector('.brush-box'),null);assert(a.d.querySelector('.apply-selection').disabled);
a.bounds([0,1,0,2]);assert.equal(a.d.querySelector('.apply-selection').disabled,false);
a.d.querySelector('.clear').click();assert.equal(a.d.querySelector('.brush-box'),null);assert.deepEqual(a.ids(),[]);
a.bounds([0,1,0,2]);
// Pair changes invalidate rectangle geometry, not selected source identities or native state.
a.d.querySelector('.y-marker').value=a.d.querySelector('.x-marker').value;
a.d.querySelector('.y-marker').dispatchEvent(new a.w.Event('change'));assert(a.d.querySelector('.brush-preview').disabled);
assert.equal(a.d.querySelector('.brush-box'),null);assert.equal(a.calls.length,1);
assert.equal(a.d.querySelectorAll('.grid button[aria-pressed="true"]').length,6);
assert.deepEqual(a.errors,[]);a.dom.window.close();
// Ties are included individually; missing pairs remain outside the rectangle.
const b=open(process.argv[3]);b.bounds([0,0,0,0]);assert.deepEqual(b.ids(),['2','4']);
b.bounds([100,110,100,110]);assert.deepEqual(b.ids(),[]);
b.bounds([0,2,0,2]);assert.deepEqual(b.ids(),['2','4','9']);
b.d.querySelector('.y-marker').value='2';b.d.querySelector('.y-marker').dispatchEvent(new b.w.Event('change'));
b.bounds([0,1,0,2]);assert.deepEqual(b.ids(),['2','4','7']);
b.fields[0].dispatchEvent(new b.w.KeyboardEvent('keydown',{key:'Enter',bubbles:true}));assert.deepEqual(b.ids(),['2','4','7']);
assert.equal(b.calls.length,0);assert.deepEqual(b.errors,[]);b.dom.window.close();
const empty=open(process.argv[4]);assert(empty.d.querySelector('.brush-preview').disabled);assert(empty.fields.every(f=>f.disabled));assert.deepEqual(empty.errors,[]);empty.dom.window.close();
const constant=open(process.argv[5]);constant.bounds([1,1,0,2]);assert.deepEqual(constant.ids(),['2','4','9']);assert.deepEqual(constant.errors,[]);constant.dom.window.close();
const z=open(process.argv[6]);z.d.querySelector('.brush-preview').click();assert.deepEqual(z.ids(),['2','4','9']);assert.equal(z.calls.length,0);assert.deepEqual(z.errors,[]);z.dom.window.close();
console.log('IHC rectangle numeric/drag previews: inclusive bounds, ties/missing, scaling, pointer capture/cancel, source identity and explicit Apply PASSED');
