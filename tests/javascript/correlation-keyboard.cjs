const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const errors=[],calls=[];
const dom=new JSDOM(fs.readFileSync(process.argv[2],'utf8'),{runScripts:'dangerously',beforeParse(w){w.setOption=(...a)=>calls.push(a);w.fetch=()=>{throw Error('No network');};w.addEventListener('error',e=>errors.push(e.message));}});
const d=dom.window.document,b=[...d.querySelectorAll('button')],n=Number(process.argv[3]);
assert.equal(b.length,n*n);assert.equal(b.filter(x=>x.tabIndex===0).length,1);
function key(k,mods={}){const e=new dom.window.KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true,...mods});d.activeElement.dispatchEvent(e);return e;}
b[0].focus();key('ArrowUp');key('ArrowLeft');assert.equal(d.activeElement,b[0]);
for(let i=1;i<n;i++){key('ArrowRight');assert.equal(d.activeElement,b[i]);}
key('ArrowRight');assert.equal(d.activeElement,b[n-1]);
for(let i=1;i<n;i++){key('ArrowDown');assert.equal(d.activeElement,b[i*n+n-1]);}
key('ArrowDown');assert.equal(d.activeElement,b[n*n-1]);
key('Home');assert.equal(d.activeElement,b[(n-1)*n]);key('Home',{ctrlKey:true});assert.equal(d.activeElement,b[0]);
key('End',{metaKey:true});assert.equal(d.activeElement,b[n*n-1]);
key('ArrowUp');key('ArrowLeft');assert.equal(d.activeElement,b[(n-2)*n+n-2]);
assert.equal(key('Tab').defaultPrevented,false);assert.equal(key('Tab',{shiftKey:true}).defaultPrevented,false);
assert.equal(key('Escape').defaultPrevented,false);assert.equal(key('Enter').defaultPrevented,false);assert.equal(key(' ').defaultPrevented,false);
assert.equal(b.filter(x=>x.tabIndex===0).length,1);assert.equal(calls.length,0);assert.deepEqual(errors,[]);
dom.window.close();console.log(`Correlation ${n} x ${n} keyboard boundaries/endpoints and local-only inspection PASSED`);
