const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
function open(file){const calls=[],errors=[];const dom=new JSDOM(fs.readFileSync(file,'utf8'),{runScripts:'dangerously',beforeParse(w){w.setOption=(...a)=>calls.push(a);w.fetch=()=>{throw Error('Keyboard inspection must stay local');};w.addEventListener('error',e=>errors.push(e.message));}});const d=dom.window.document,w=dom.window;const points=()=>[...d.querySelectorAll('.scatter-view circle')];const stops=()=>points().filter(e=>e.tabIndex===0);function key(k){const e=new w.KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true});d.activeElement.dispatchEvent(e);return e.defaultPrevented;}return{dom,d,w,points,stops,key,calls,errors};}
const a=open(process.argv[2]);assert.equal(a.stops().length,1);assert.equal(a.points().length,3);
assert.match(a.d.getElementById(a.d.querySelector('.scatter-view').getAttribute('aria-describedby')).textContent,/row-order navigation/);
a.stops()[0].focus();assert.equal(a.d.activeElement.dataset.row,'2');
a.key('ArrowLeft');assert.equal(a.d.activeElement.dataset.row,'2');
a.key('ArrowRight');assert.equal(a.d.activeElement.dataset.row,'4'); // tied point is separately reachable
assert.match(a.d.querySelector('.detail').textContent,/Source row: 4/);
a.key('ArrowDown');assert.equal(a.d.activeElement.dataset.row,'9'); // row 7 missing this pair
assert.equal(a.stops().length,1);a.key('End');a.key('ArrowRight');assert.equal(a.d.activeElement.dataset.row,'9');
a.key('Home');a.key('ArrowRight');assert.equal(a.d.activeElement.dataset.row,'4');
assert.equal(a.key('Tab'),false);assert.equal(a.key('PageDown'),false);assert.equal(a.calls.length,0);
const ys=a.d.querySelector('.y-marker');ys.focus();ys.value='2';ys.dispatchEvent(new a.w.Event('change'));
assert.equal(a.d.activeElement,ys);assert.equal(a.stops()[0].dataset.row,'4');assert.equal(a.points().length,4);
ys.value='0';ys.dispatchEvent(new a.w.Event('change'));assert.equal(a.points().length,0);assert.equal(a.stops().length,0);
ys.value='1';ys.dispatchEvent(new a.w.Event('change'));assert.equal(a.stops().length,1);assert.equal(a.stops()[0].dataset.row,'4');
const extend=a.d.querySelector('.extend-rows');extend.checked=true;
a.d.querySelector('.clear').click();a.stops()[0].focus();a.key('End');assert.equal(a.d.querySelectorAll('.scatter-view circle[aria-pressed="true"]').length,0);
a.key('Enter');assert.equal(a.d.querySelectorAll('.scatter-view circle[aria-pressed="true"]').length,1);
a.key(' ');assert.equal(a.d.querySelectorAll('.scatter-view circle[aria-pressed="true"]').length,0);
assert.equal(a.calls.length,0);a.key('Enter');a.d.querySelector('.apply-selection').click();assert.equal(a.calls.length,1);assert.deepEqual(JSON.parse(a.calls[0][1]).rows,['9']);
assert.deepEqual(a.errors,[]);a.dom.window.close();
const b=open(process.argv[3]);assert.equal(b.points().length,0);assert.equal(b.stops().length,0);assert.equal(b.calls.length,0);assert.deepEqual(b.errors,[]);b.dom.window.close();
const max=open(process.argv[4]);assert.equal(max.points().length,200);assert.equal(max.stops().length,1);max.stops()[0].focus();max.key('End');assert.equal(max.d.activeElement.dataset.row,'399');max.key('Home');assert.equal(max.d.activeElement.dataset.row,'1');assert.equal(max.calls.length,0);assert.deepEqual(max.errors,[]);max.dom.window.close();
const one=open(process.argv[5]);assert.equal(one.points().length,1);one.stops()[0].focus();for(const k of ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'])one.key(k);assert.equal(one.stops().length,1);assert.equal(one.d.activeElement,one.points()[0]);assert.equal(one.calls.length,0);assert.deepEqual(one.errors,[]);one.dom.window.close();
console.log('Scatter row-order keyboard navigation, ties/missing pairs, redraw focus, toggle activation and explicit Apply PASSED');
