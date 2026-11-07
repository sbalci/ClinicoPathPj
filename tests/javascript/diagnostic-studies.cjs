const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{JSDOM}=require('jsdom');
const directory=process.argv[2];
function open(html){const calls=[],errors=[];const dom=new JSDOM(html,{runScripts:'dangerously',beforeParse(w){w.setOption=(...args)=>calls.push(args);w.postMessage=(...args)=>calls.push(args);w.fetch=()=>{throw Error('Network forbidden');};w.addEventListener('error',e=>errors.push(e.message));}});return {dom,d:dom.window.document,w:dom.window,calls,errors};}
function fixture(name){return fs.readFileSync(path.join(directory,name+'.html'),'utf8');}
function key(a,name,modifiers={}){const e=new a.w.KeyboardEvent('keydown',{key:name,bubbles:true,cancelable:true,...modifiers});a.d.activeElement.dispatchEvent(e);return e;}
const a=open(fixture('main')),buttons=[...a.d.querySelectorAll('.study-list button')],charts=[...a.d.querySelectorAll('svg')];
assert.equal(buttons.length,8);assert.equal(charts.length,2);
const current=()=>buttons.findIndex(b=>b.getAttribute('aria-pressed')==='true');
const active=()=>{assert.equal(buttons.filter(b=>b.tabIndex===0).length,1);return buttons.findIndex(b=>b.tabIndex===0);};
function selected(index){assert.equal(current(),index);assert.equal(active(),index);for(const svg of charts){const rows=[...svg.querySelectorAll('g.active')];assert.equal(rows.length,1);assert.equal(rows[0].dataset.index,String(index));}}
selected(0);assert.match(a.d.querySelector('.detail').textContent,/source row 3: Study 01/);
assert.equal(Number(charts[0].querySelectorAll('.point')[0].getAttribute('cx')),350);
assert.equal(Number(charts[1].querySelectorAll('.point')[0].getAttribute('cx')),386);
assert.equal(Number(charts[0].querySelectorAll('.point')[2].getAttribute('cx')),62);
assert.equal(Number(charts[0].querySelectorAll('.point')[4].getAttribute('cx')),422);
const hovered=charts[0].querySelectorAll('.point')[2];hovered.dispatchEvent(new a.w.Event('pointerenter'));
assert.match(a.d.querySelector('.detail').textContent,/Hover preview.*source row 7/);
assert.match(a.d.querySelector('.detail').textContent,/TP = 0; FP = 5; FN = 10; TN = 15/);
assert.equal(current(),0);assert(charts.every(svg=>svg.querySelector('g.active').dataset.index==='2'));
hovered.dispatchEvent(new a.w.Event('pointerleave'));selected(0);
charts[1].querySelectorAll('.point')[4].dispatchEvent(new a.w.MouseEvent('click',{bubbles:true}));selected(4);assert.equal(a.d.activeElement,buttons[4]);
assert.match(a.d.querySelector('.detail').textContent,/Specificity = 0.0%/);
buttons[0].focus();key(a,'ArrowUp');selected(0);
for(let i=1;i<8;i++){key(a,'ArrowDown');selected(i);}key(a,'ArrowDown');selected(7);
key(a,'Home');selected(0);key(a,'End',{metaKey:true});selected(7);key(a,'Home',{ctrlKey:true});selected(0);
for(const k of ['Tab','Enter',' ','Escape','ArrowLeft'])assert.equal(key(a,k).defaultPrevented,false);
assert.equal(key(a,'Tab',{shiftKey:true}).defaultPrevented,false);
assert.equal(key(a,'ArrowDown',{shiftKey:true}).defaultPrevented,false);
buttons[5].click();selected(5);a.d.querySelector('.reset').click();selected(0);
assert.deepEqual(a.errors,[]);assert.deepEqual(a.calls,[]);a.dom.window.close();
for(const [name,count] of [['single',1],['maximum',200],['hostile',1]]){
 const b=open(fixture(name)),items=[...b.d.querySelectorAll('.study-list button')];assert.equal(items.length,count);assert.equal(b.d.querySelectorAll('.point').length,2*count);
 items[0].focus();
 if(name==='maximum'){
  b.d.querySelector('.study-list').getBoundingClientRect=()=>({top:0,bottom:180});
  items[count-1].getBoundingClientRect=()=>({top:200,bottom:230});
  b.d.querySelector('.forest-scroll').getBoundingClientRect=()=>({top:0,bottom:480});
  b.d.querySelectorAll('svg')[0].querySelectorAll('g')[count-1].getBoundingClientRect=()=>({top:600,bottom:624});
 }
 key(b,'End');assert.equal(b.d.activeElement,items[count-1]);
 if(name==='maximum'){assert(b.d.querySelector('.study-list').scrollTop>0);assert(b.d.querySelector('.forest-scroll').scrollTop>0);}
 key(b,'ArrowDown');assert.equal(b.d.activeElement,items[count-1]);key(b,'Home');assert.equal(b.d.activeElement,items[0]);key(b,'ArrowUp');assert.equal(b.d.activeElement,items[0]);
 assert.equal(b.d.querySelectorAll('img,iframe,script[src]').length,0);assert.equal(b.w.pwned,undefined);assert.deepEqual(b.errors,[]);assert.deepEqual(b.calls,[]);b.dom.window.close();
}
const combined=open(fixture('main')+fixture('single')),roots=[...combined.d.querySelectorAll('.cpj-study-inspector')];assert.equal(roots.length,2);assert.notEqual(roots[0].id,roots[1].id);
roots[0].querySelectorAll('.study-list button')[6].click();assert.match(roots[0].querySelector('.detail').textContent,/source row 15/);assert.match(roots[1].querySelector('.detail').textContent,/source row 3/);assert.deepEqual(combined.errors,[]);assert.deepEqual(combined.calls,[]);combined.dom.window.close();
console.log('Linked study inspector: geometry, paired hover/selection, keyboard boundaries, native activation, 1/200-row limits, hostile labels, instance isolation and no host/network writes PASS');
for(const name of ['included','empty','stale']){
 const b=open(fixture(name)),inputs=[...b.d.querySelectorAll('.inclusion-rows input')];
 assert.equal(inputs.length,8);assert.equal(b.d.querySelector('.inclusion-panel').hidden,false);
 const count=()=>inputs.filter(v=>v.checked).length;
 assert.equal(count(),name==='included'?2:0);
 b.d.querySelectorAll('.study-list button')[5].click();assert.deepEqual(b.calls,[]);
 b.d.querySelector('.include-all').click();assert.equal(count(),8);assert.deepEqual(b.calls,[]);
 b.d.querySelector('.include-restore').click();assert.equal(count(),name==='included'?2:0);
 b.d.querySelector('.include-none').click();assert.equal(count(),0);assert.deepEqual(b.calls,[]);
 b.d.querySelector('.include-apply').click();
 if(name==='empty'){assert.deepEqual(b.calls,[]);assert.match(b.d.querySelector('.inclusion-status').textContent,/already applied/);}
 else{assert.equal(b.calls.length,1);assert.equal(b.calls[0][0],'inclusionDefinition');assert.deepEqual(JSON.parse(b.calls[0][1]),{version:1,rows:[],snapshot:'a'.repeat(64)});}
 b.calls.length=0;b.w.setOption=undefined;b.d.querySelector('.include-all').click();b.d.querySelector('.include-apply').click();assert.match(b.d.querySelector('.inclusion-status').textContent,/requires/);assert.deepEqual(b.errors,[]);b.dom.window.close();
}
console.log('Study inclusion preview, restore, explicit Apply, empty/stale states and missing bridge PASS');
