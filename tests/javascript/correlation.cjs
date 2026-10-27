const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const errors=[],calls=[];const dom=new JSDOM(fs.readFileSync(process.argv[2],'utf8'),{runScripts:'dangerously',beforeParse(w){w.setOption=(...a)=>calls.push(a);w.fetch=()=>{throw Error('Inspection must stay local');};w.addEventListener('error',e=>errors.push(e.message));}});
const d=dom.window.document,b=[...d.querySelectorAll('button')];assert.equal(b.length,9);assert.equal(d.querySelector('unsafe'),null);
b[1].focus();assert.match(d.querySelector('.detail').textContent,/n = 4; excluded = 0/);assert.match(d.querySelector('.detail').textContent,/<unsafe>/);
b[2].click();assert.match(d.querySelector('.detail').textContent,/Constant variable/);assert.match(d.querySelector('.detail').textContent,/unavailable/);
b[0].click();assert.match(d.querySelector('.detail').textContent,/not tested/);assert.equal(calls.length,0);assert.deepEqual(errors,[]);dom.window.close();console.log('Correlation literal labels, keyboard inspection, pair n, unavailable cells and no backend dispatch PASSED');
