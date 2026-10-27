const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
function open(file){
 const calls=[],errors=[];
 const dom=new JSDOM(fs.readFileSync(file,'utf8'),{runScripts:'dangerously',beforeParse(w){
  w.addEventListener('error',e=>errors.push(e.message));w.setOption=(...args)=>calls.push(args);
  w.fetch=()=>{throw Error('Selection must stay local');};
 }});
 return {dom,d:dom.window.document,calls,errors};
}
const {dom,d,calls,errors}=open(process.argv[2]);
assert.deepEqual(errors,[]);assert.equal(calls.length,0);
const click=el=>el.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}));
const selected=()=>d.querySelectorAll('.grid button[aria-pressed="true"]');
d.querySelector('.tree-branch[data-axis="rows"]').focus();assert.equal(selected().length,6);
assert.equal(calls.length,0);d.querySelector('.apply-selection').click();assert.equal(calls.length,1);
assert.equal(calls[0][0],'selectionDefinition');const payload=JSON.parse(calls[0][1]);
assert.equal(payload.version,1);assert.deepEqual(payload.rows,['2','7']);assert.match(payload.snapshot,/^[0-9a-f]{64}$/);
d.querySelector('.restore-selection').click();assert.equal(selected().length,0);assert.equal(calls.length,1);
d.querySelector('.extend-rows').checked=true;
const p2=d.querySelector('.scatter-view circle[data-row="2"]'),p4=d.querySelector('.scatter-view circle[data-row="4"]');
p2.focus();assert.equal(selected().length,0);click(p2);click(p4);assert.equal(selected().length,6);
click(p2);assert.equal(selected().length,3);assert.match(d.querySelector('.selection-preview').textContent,/\(1\): 4/);
d.querySelector('.tree-branch[data-axis="markers"]').focus();assert.equal(d.querySelector('.apply-selection').disabled,true);
assert.equal(calls.length,1);assert.deepEqual(errors,[]);
d.querySelector('.clear').click();d.querySelector('.grid button').click();delete dom.window.setOption;
d.querySelector('.apply-selection').click();assert.match(d.querySelector('.selection-status').textContent,/requires the native jamovi/);
assert.equal(calls.length,1);dom.window.close();
const restored=open(process.argv[3]);
assert.equal(restored.calls.length,0);assert.equal(restored.d.querySelectorAll('.grid button[aria-pressed="true"]').length,3);
assert.match(restored.d.querySelector('.selection-preview').textContent,/\(1\): 4/);
restored.d.querySelector('.apply-selection').click();assert.equal(restored.calls.length,0);
restored.d.querySelector('.clear').click();restored.d.querySelector('.apply-selection').click();
assert.deepEqual(JSON.parse(restored.calls[0][1]).rows,[]);assert.deepEqual(restored.errors,[]);
restored.dom.window.close();
if(process.argv[4]){
 const invalid=open(process.argv[4]);assert.match(invalid.d.querySelector('.selection-preview').textContent,/needs review/);
 invalid.d.querySelector('.grid button[aria-label^="Row 4,"]').click();invalid.d.querySelector('.apply-selection').click();
 const current=JSON.parse(invalid.calls[0][1]);assert.deepEqual(current.rows,['4']);assert.notEqual(current.snapshot,'0'.repeat(64));
 assert.deepEqual(invalid.errors,[]);invalid.dom.window.close();
}
console.log('IHC explicit Apply, no automatic dispatch, toggled source IDs, restoration, review and clearing PASSED');
