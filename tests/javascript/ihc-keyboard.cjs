const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
function open(path){
 const calls=[],errors=[];
 const dom=new JSDOM(fs.readFileSync(path,'utf8'),{runScripts:'dangerously',beforeParse(w){
  w.addEventListener('error',e=>errors.push(e.message));w.setOption=(...args)=>calls.push(args);
  w.fetch=()=>{throw Error('Cell navigation must stay local');};
 }});
 const d=dom.window.document,w=dom.window,cells=Array.from(d.querySelectorAll('.grid button'));
 const stop=()=>{const stops=cells.filter(c=>c.tabIndex===0);assert.equal(stops.length,1);return cells.indexOf(stops[0]);};
 function key(name,options={}){const e=new w.KeyboardEvent('keydown',{key:name,bubbles:true,cancelable:true,...options});d.activeElement.dispatchEvent(e);return e.defaultPrevented;}
 function at(index){assert.equal(d.activeElement,cells[index]);assert.equal(stop(),index);}
 return {dom,d,cells,calls,errors,key,at,stop};
}
// Existing three-row fixture includes missing values and original source IDs 7,9,20.
const a=open(process.argv[2]);assert.equal(a.stop(),0);assert(a.cells.slice(1).every(c=>c.tabIndex===-1));
const description=a.d.querySelector('.grid').getAttribute('aria-describedby');assert.match(a.d.getElementById(description).textContent,/Arrow keys/);
a.cells[0].focus();a.at(0);
assert(a.key('ArrowLeft'));a.at(0);a.key('ArrowUp');a.at(0);
a.key('ArrowRight');a.at(1);a.key('ArrowDown');a.at(4);
assert.match(a.d.querySelector('.detail').textContent,/Source row: 9/);assert.match(a.d.querySelector('.detail').textContent,/Raw value: \[missing\]/);
a.key('Home');a.at(3);a.key('End');a.at(5);a.key('ArrowRight');a.at(5);
a.key('End',{ctrlKey:true});a.at(8);a.key('ArrowDown');a.at(8);
a.key('Home',{metaKey:true});a.at(0);a.key('End',{metaKey:true});a.at(8);
a.key('Home',{ctrlKey:true});a.at(0);a.key('ArrowDown');a.key('ArrowRight');a.at(4);a.key('ArrowUp');a.at(1);
a.key('ArrowLeft');a.at(0);
for(const key of ['Tab','Enter',' ','PageDown']){assert.equal(a.key(key),false);a.at(0);}
a.cells[7].click();assert.equal(a.stop(),7);a.cells[7].focus();a.at(7);
a.d.querySelector('.clear').click();assert.equal(a.stop(),7);
assert.equal(a.calls.length,0);assert.deepEqual(a.errors,[]);a.dom.window.close();
// In toggle mode, keyboard inspection preserves the applied preview until activation.
const b=open(process.argv[3]);b.d.querySelector('.extend-rows').checked=true;
const selected=()=>b.d.querySelectorAll('.grid button[aria-pressed="true"]').length;
assert.equal(selected(),3);b.cells[0].focus();b.key('End',{ctrlKey:true});b.key('Home');assert.equal(selected(),3);
b.key('Home',{ctrlKey:true});b.at(0);b.cells[0].click();assert.equal(selected(),6);assert.equal(b.calls.length,0);
b.d.querySelector('.apply-selection').click();assert.equal(b.calls.length,1);assert.deepEqual(new Set(JSON.parse(b.calls[0][1]).rows),new Set(['2','4']));
assert.deepEqual(b.errors,[]);b.dom.window.close();
const c=open(process.argv[4]);assert.equal(c.cells.length,4000);assert.equal(c.stop(),0);c.cells[0].focus();
c.key('End',{ctrlKey:true});c.at(3999);c.key('Home');c.at(3980);c.key('ArrowUp');c.at(3960);c.key('Home',{ctrlKey:true});c.at(0);
assert.equal(c.calls.length,0);assert.deepEqual(c.errors,[]);c.dom.window.close();
const one=open(process.argv[5]);assert.equal(one.cells.length,3);one.cells[1].focus();one.key('ArrowUp');one.at(1);one.key('ArrowDown');one.at(1);one.key('End',{ctrlKey:true});one.at(2);one.key('Home',{ctrlKey:true});one.at(0);
assert.equal(one.calls.length,0);assert.deepEqual(one.errors,[]);one.dom.window.close();
console.log('IHC roving keyboard focus: arrows, row/matrix boundaries, singleton/4000 cells, missing values, toggle preview and explicit Apply PASSED');
