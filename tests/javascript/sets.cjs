const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const errors=[],calls=[];const dom=new JSDOM(fs.readFileSync(process.argv[2],'utf8'),{runScripts:'dangerously',beforeParse(w){w.setOption=(...a)=>calls.push(a);w.fetch=()=>{throw Error('No network');};w.addEventListener('error',e=>errors.push(e.message));}});
const d=dom.window.document,b=[...d.querySelectorAll('button')],detail=()=>d.querySelector('.detail').textContent;
assert.equal(b.length,4);assert.equal(d.querySelector('unsafe'),null);assert.match(d.querySelector('.legend').textContent,/1: <unsafe> = Y/);
b[0].focus();assert.match(detail(),/Pattern 00/);assert.match(detail(),/Rows: 1 \/ 4/);assert.match(detail(),/Source rows: 2/);assert.doesNotMatch(detail(),/15/);
b[3].click();assert.match(detail(),/Pattern 11/);assert.match(detail(),/<unsafe> \+ B/);assert.match(detail(),/Source rows: 12/);
assert.equal(calls.length,0);assert.deepEqual(errors,[]);dom.window.close();console.log('Set inspector literal labels, focus/click, none/overlap counts, original rows and no backend dispatch PASSED');
